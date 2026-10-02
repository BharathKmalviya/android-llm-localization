import os
import re
import time
import socket
import argparse
import urllib.request
import urllib.error
import json
import math
import difflib
import sys

if __package__ in (None, ""):
    # Retain direct script execution as well as installed and -m entry points.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from android_localisation.resources import (
    atomic_write, is_locale_folder, locale_folders, merge_missing,
    missing_resources, parse_resources, validate_resources,
)

from android_localisation.locales import (
    all_android_locales, android_locale, language_items, normalize_play_locale, select_locales,
)

DEFAULT_RES_DIR = "app/src/main/res"
DEFAULT_API_TIMEOUT = 180  # seconds (3 minutes) — large strings.xml files can exceed 60s
MAX_TIMEOUT_RETRIES = 2

# Ordered list of models per provider.
# First entry = default. Rest = automatic fallbacks (used only when user hasn't pinned a model).
# Latest text-model lineup checked against official catalogs on 2026-10-02.
# Do not add older-generation models as automatic fallbacks.
PROVIDER_MODELS = {
    "gemini": [
        "gemini-3.8-flash",
    ],
    "openai": [
        "gpt-6-luna",
        "gpt-6.1-sol",
        "gpt-6-astra",
    ],
    "anthropic": [
        "claude-sonnet-5-5",
        "claude-opus-5-5",
    ],
    "custom": [],  # user must specify --model
}


def get_target_directories(res_dir):
    """Find locale directories, excluding configuration-only folders."""
    return locale_folders(res_dir)


def normalize_android_folder(value):
    value = value.strip()
    if not value:
        raise ValueError("empty Android locale")
    # Preserve existing Android forms; also accept conventional language tags.
    if not value.startswith(("values-", "b+")) and "-" in value:
        try:
            value = android_locale(value)
        except ValueError:
            pass  # May be an Android qualifier such as es-rES or en-night.
    folder = value if value.startswith("values-") else "values-" + value
    if not is_locale_folder(folder):
        raise ValueError("invalid Android locale: {} (use hi, es-rES, es-ES or b+zh+Hans)".format(value))
    return folder


def _android_identity(folder):
    qualifier = folder[len("values-"):]
    if qualifier.startswith("b+"):
        qualifier = qualifier[2:].replace("+", "-")
    return re.sub(r"-r([A-Z]{2}|\d{3})(?=-|$)", r"-\1", qualifier).lower()


def ensure_locale_dirs(res_dir, languages, create=True, excluded=None):
    """
    Creates values-<lang> directories for each language code in the list.
    Returns the list of folder names created or already existing.
    """
    languages = [lang.strip() for lang in languages]
    # Historical manual Android lists ignore empty entries.
    languages = [lang for lang in languages if lang]
    created = select_locales(
        languages, normalize_android_folder,
        ["values-" + locale for locale in all_android_locales()], excluded, _android_identity,
    )
    # Validate the entire list before creating any directories.
    for folder in created:
        folder_path = os.path.join(res_dir, folder)
        if create and not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            print(f"📁 Created {folder}/")
    return created


def read_source_xml(source_path):
    with open(source_path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def build_prompt(source_xml, target_folder_name, app_context, source_language="en-US"):
    context_str = f"an Android app ({app_context})" if app_context else "an Android application"
    return f"""You are a professional Android localization expert.

Translate the `strings.xml` below from {source_language} for {context_str} into the language for Android resource directory: `{target_folder_name}`.
For example, `values-hi` is Hindi, `values-es-rES` is Spanish (Spain), `values-zh-rTW` is Traditional Chinese, `values-ar` is Arabic, etc.

STRICT GUIDELINES:
1. Translate only eligible string and item values — preserve resource names, tags, item order, attributes and namespace declarations exactly as in the source.
   Never change values marked translatable="false", resource references, or non-text resources.
2. Use natural, human-sounding language. Simple everyday mobile UI tone. Not robotic or word-for-word.
3. Preserve ALL placeholders exactly as-is: %s, %d, %1$s, %1$d, %2$s, etc.
4. Preserve ALL escape sequences exactly as-is: \\n, \\', \\", \\\\.
5. Preserve ALL HTML tags exactly as-is: <b>, <i>, <u>, <br/>, etc.
6. Apostrophes in translated text MUST be escaped as \\' — never use a raw ' or a curly apostrophe.
7. The output MUST use standard Android strings.xml format:
   - Start with: <?xml version="1.0" encoding="utf-8"?>
   - Preserve the source <resources> attributes and all xmlns declarations
   - Every string on its own line: <string name="key">translated value</string>
   - Preserve inline markup, CDATA content, string arrays and plural quantities; do not invent or remove resources
8. Return ONLY the raw XML. No markdown, no code fences, no explanation.

SOURCE XML:
{source_xml}
"""


def clean_xml_response(result):
    if not result:
        return ""
    result = result.strip()

    # Strip markdown code fences
    if result.startswith("```xml"):
        result = result[6:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    result = result.strip()

    return result


def _read_error_body(e):
    try:
        return e.read().decode("utf-8", errors="replace")[:500]
    except Exception:
        return "(could not read error body)"


def _is_model_not_found(http_code, body):
    """Returns True if the error clearly means the model doesn't exist."""
    if http_code == 404:
        return True
    body_lower = body.lower()
    return any(phrase in body_lower for phrase in [
        "model not found", "model_not_found", "does not exist",
        "no such model", "unknown model", "invalid model",
    ])


def _is_timeout_error(exc):
    """True for direct timeouts and URLError wrappers (common from urllib.request.urlopen)."""
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    return isinstance(exc, urllib.error.URLError) and isinstance(
        exc.reason, (TimeoutError, socket.timeout)
    )


def _urlopen_with_retries(req, provider_label, timeout):
    """
    Execute an HTTP request with timeout/network error handling and retries on timeout.
    Returns (response_bytes, model_not_found).
    """
    for attempt in range(MAX_TIMEOUT_RETRIES + 1):
        if attempt > 0:
            wait = attempt * 3
            print(f"  🔁 {provider_label} timed out — retrying ({attempt}/{MAX_TIMEOUT_RETRIES}) in {wait}s...")
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read(), False
        except urllib.error.HTTPError as e:
            body = _read_error_body(e)
            model_gone = _is_model_not_found(e.code, body)
            print(f"  ❌ {provider_label} API Error: {e.code} - {body}")
            return None, model_gone
        except (TimeoutError, socket.timeout, urllib.error.URLError) as e:
            if not _is_timeout_error(e):
                print(f"  ❌ {provider_label} network error: {e.reason}")
                return None, False
            if attempt < MAX_TIMEOUT_RETRIES:
                continue
            print(f"  ❌ {provider_label} API timed out after {timeout}s ({MAX_TIMEOUT_RETRIES + 1} attempts)")
            return None, False
    return None, False


def call_gemini(api_key, model, prompt, timeout=DEFAULT_API_TIMEOUT):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    raw, model_gone = _urlopen_with_retries(req, "Gemini", timeout)
    if raw is None:
        return None, model_gone
    result = json.loads(raw.decode("utf-8"))
    candidates = result.get("candidates", [])
    if not candidates:
        print("  ❌ Gemini returned no candidates.")
        return None, False
    candidate = candidates[0]
    if candidate.get("finishReason") not in (None, "STOP"):
        print("  ❌ Gemini response was incomplete or blocked: {}".format(candidate.get("finishReason")))
        return None, False
    return "".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", [])
                   if not part.get("thought")), False


def call_openai_compatible(api_key, base_url, model, prompt, timeout=DEFAULT_API_TIMEOUT):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key or ''}",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(base_url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    raw, model_gone = _urlopen_with_retries(req, "OpenAI (compatible)", timeout)
    if raw is None:
        return None, model_gone
    result = json.loads(raw.decode("utf-8"))
    choices = result.get("choices", [])
    if not choices:
        print("  ❌ OpenAI returned no choices.")
        return None, False
    if choices[0].get("finish_reason") not in (None, "stop"):
        print("  ❌ OpenAI-compatible response was incomplete: {}".format(choices[0].get("finish_reason")))
        return None, False
    return choices[0].get("message", {}).get("content", ""), False


def call_anthropic(api_key, model, prompt, timeout=DEFAULT_API_TIMEOUT):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = {
        "model": model,
        "max_tokens": 16384,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    raw, model_gone = _urlopen_with_retries(req, "Anthropic", timeout)
    if raw is None:
        return None, model_gone
    result = json.loads(raw.decode("utf-8"))
    content = result.get("content", [])
    if not content:
        print("  ❌ Anthropic returned no content.")
        return None, False
    if result.get("stop_reason") not in (None, "end_turn"):
        print("  ❌ Anthropic response was incomplete: {}".format(result.get("stop_reason")))
        return None, False
    return "".join(block.get("text", "") for block in content if block.get("type") == "text"), False


def _call_provider(provider, api_key, model, prompt, base_url=None, timeout=DEFAULT_API_TIMEOUT):
    """Dispatches to the right API. Returns (text, model_not_found)."""
    if provider == "gemini":
        return call_gemini(api_key, model, prompt, timeout)
    elif provider == "openai":
        url = base_url if base_url else "https://api.openai.com/v1/chat/completions"
        return call_openai_compatible(api_key, url, model, prompt, timeout)
    elif provider == "anthropic":
        return call_anthropic(api_key, model, prompt, timeout)
    else:
        print(f"❌ Unknown provider: {provider}")
        return None, False


def translate_xml(provider, api_key, model, source_xml, target_folder_name, app_context,
                  base_url=None, fallback_models=None, timeout=DEFAULT_API_TIMEOUT, only_resources=None,
                  source_language="en-US"):
    """
    Calls the selected provider API to translate the XML.
    If the model is not found and fallback_models are provided, retries with the next one.
    Returns (translated_xml, model_used).
    """
    prompt = build_prompt(source_xml, target_folder_name, app_context, source_language)
    if only_resources is not None:
        prompt += "\nMISSING-ONLY UPDATE: The source above provides context. Return a <resources> document " \
                  "containing ONLY these resource types and names, retaining their original attributes " \
                  "and structure: {}. Do not return the other resources.\n".format(json.dumps(only_resources))
    models_to_try = [model] + (fallback_models or [])

    for attempt_model in models_to_try:
        if attempt_model != model:
            print(f"  ↩️  Falling back to model: {attempt_model}")
        result, model_not_found = _call_provider(
            provider, api_key, attempt_model, prompt, base_url, timeout
        )
        if result is not None:
            return clean_xml_response(result), attempt_model
        if not model_not_found:
            # Failed for a non-model reason (auth, quota, network) — don't try fallbacks
            return None, attempt_model

    return None, models_to_try[-1]


def _parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Translate source XML using LLMs; validate output before saving. Existing locale files are refreshed unless --missing-only or --skip-existing is set.",
        epilog="Use python -m android_localisation translate --help for workflow examples, or python -m android_localisation models for model defaults.",
    )
    parser.add_argument("--res-dir", default=DEFAULT_RES_DIR, help="Path to the Android res/ directory (default: app/src/main/res)")
    add_flexible_arguments(parser)
    parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini", help="AI provider (default: gemini)")
    parser.add_argument("--model", help="Pin any supported model and disable fallbacks (default: provider default; see models)")
    parser.add_argument("--api-key", help="API key, or set GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / API_KEY")
    parser.add_argument("--base-url", help="Custom OpenAI-compatible endpoint URL (required for 'custom' provider)")
    parser.add_argument("--app-context", help="Short description of your app for better translations")
    parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between API requests (default: 5.0)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_API_TIMEOUT,
                        help=f"Seconds to wait for each API response, up to {MAX_TIMEOUT_RETRIES + 1} attempts on timeout (default: {DEFAULT_API_TIMEOUT})")
    parser.add_argument("--languages", help="Comma-separated Android or Play tags and/or 'all' (hi,es-ES,b+zh+Hans,all,zu)")
    parser.add_argument("--missing-only", action="store_true", help="Translate missing resources while retaining existing translations")
    parser.add_argument("--dry-run", action="store_true", help="Generate and validate translations, then show a diff without writing files (API usage applies)")
    return parser.parse_args(args)


def add_flexible_arguments(parser):
    parser.add_argument("--source", help="Source XML path (default: RES_DIR/values/strings.xml)")
    parser.add_argument("--source-language", default="en-US", help="Source XML language tag (default: en-US)")
    parser.add_argument("--output-dir", help="Destination Android res/ directory (default: --res-dir)")
    parser.add_argument("--languages-file", help="UTF-8 comma/newline language list; combines with --languages")
    parser.add_argument("--exclude-languages", help="Comma-separated Android or Play tags to exclude after selection")
    parser.add_argument("--skip-existing", action="store_true", help="Validate and skip existing files without API calls; incompatible with --missing-only")


def main(args=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    missing_only = getattr(args, "missing_only", False)
    dry_run = getattr(args, "dry_run", False)
    skip_existing = getattr(args, "skip_existing", False)
    if skip_existing and missing_only:
        print("❌ ERROR: Choose --skip-existing or --missing-only, not both.")
        return 1
    if not math.isfinite(args.sleep) or args.sleep < 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
        print("❌ ERROR: --sleep must be finite and nonnegative; --timeout must be finite and positive.")
        return 1

    provider = args.provider
    user_pinned_model = bool(args.model)  # True if user explicitly chose a model

    # Resolve model + fallback chain
    if args.model:
        # User pinned a specific model — use it, no fallbacks
        model = args.model
        fallback_models = []
    else:
        if provider == "custom":
            print("❌ ERROR: You must specify --model when using a custom provider.")
            return 1
        model_list = PROVIDER_MODELS.get(provider, [])
        model = model_list[0] if model_list else None
        fallback_models = model_list[1:]

    # Resolve API key
    api_key = args.api_key
    if not api_key:
        if provider == "gemini":                  api_key = os.environ.get("GEMINI_API_KEY")
        elif provider in ("openai", "custom"):    api_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "anthropic":             api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            api_key = os.environ.get("API_KEY")

    if not api_key and provider != "custom":
        print("❌ ERROR: Please provide an API key via --api-key or the appropriate environment variable.")
        return 1

    if provider == "custom" and not args.base_url:
        print("❌ ERROR: You must provide --base-url when using a custom provider.")
        return 1

    res_dir = getattr(args, "output_dir", None) or args.res_dir
    source_strings_xml = getattr(args, "source", None) or os.path.join(args.res_dir, "values", "strings.xml")

    print(f"🔍 Reading source XML from: {source_strings_xml}")
    if not os.path.exists(source_strings_xml):
        print("❌ ERROR: Could not find source XML at the specified path.")
        return 1

    try:
        source_xml = read_source_xml(source_strings_xml)
        parse_resources(source_xml)
        source_language = normalize_play_locale(getattr(args, "source_language", "en-US"))
        # Translation never needs to create folders before the response is valid.
        if args.languages is not None or getattr(args, "languages_file", None):
            items = language_items(args.languages, getattr(args, "languages_file", None))
        else:
            items = get_target_directories(res_dir)
        target_dirs = ensure_locale_dirs(res_dir, items, create=False,
                                        excluded=language_items(getattr(args, "exclude_languages", None)))
        for folder in target_dirs:
            path = os.path.join(res_dir, folder, "strings.xml")
            if os.path.normcase(os.path.realpath(path)) == os.path.normcase(os.path.realpath(source_strings_xml)) or (
                    os.path.exists(path) and os.path.samefile(path, source_strings_xml)):
                raise ValueError("output would replace the source XML: {}".format(path))
    except (OSError, ValueError) as exc:
        print("❌ ERROR: {}".format(exc))
        return 1

    if not target_dirs:
        print(f"⚠️  No locale directories found in {res_dir}.")
        print("    Either create values-<lang>/ folders manually, or use --languages to specify them:")
        print("    Example: android-localise translate --languages hi,es,fr,de --api-key YOUR_KEY")
        return 1

    print(f"🌍 Found {len(target_dirs)} language directories.")
    fallback_note = "" if user_pinned_model else f" (fallbacks: {', '.join(fallback_models)})" if fallback_models else ""
    print(f"🤖 Provider: {provider.upper()} | Model: {model}{fallback_note}")

    actual_provider = "openai" if provider == "custom" else provider

    succeeded = failed = skipped = 0
    for folder in target_dirs:
        target_path = os.path.join(res_dir, folder, "strings.xml")
        is_new_file = not os.path.exists(target_path)

        if is_new_file:
            print(f"⏳ [{folder}] No strings.xml found — creating and translating...")
        elif skip_existing:
            print(f"⏳ [{folder}] Validating existing strings.xml...")
        else:
            print(f"⏳ [{folder}] Updating existing strings.xml...")

        try:
            existing_xml = read_source_xml(target_path) if not is_new_file else ""
            if skip_existing and not is_new_file:
                validate_resources(source_xml, existing_xml)
                print("⏭️  [{}] Existing valid file skipped.".format(folder))
                skipped += 1
                continue
            if missing_only and not is_new_file and not existing_xml.strip():
                raise ValueError("existing file is empty XML; use normal translation to regenerate it")
            missing = missing_resources(source_xml, existing_xml) if missing_only else None
            if missing_only and not missing:
                print("⏭️  [{}] No missing resources. Skipping API request.".format(folder))
                skipped += 1
                continue
            translated_xml, used_model = translate_xml(
                actual_provider, api_key, model, source_xml,
                folder, args.app_context, args.base_url, fallback_models, args.timeout,
                only_resources=missing, source_language=source_language
            )
            if not translated_xml:
                raise ValueError("API returned no usable translation")
            if missing_only:
                translated_xml = merge_missing(source_xml, existing_xml, translated_xml, missing)
            else:
                validate_resources(source_xml, translated_xml)
            if dry_run:
                diff = difflib.unified_diff(existing_xml.splitlines(True), translated_xml.splitlines(True),
                                            fromfile=target_path, tofile=target_path + " (preview)")
                print("".join(diff))
            else:
                atomic_write(target_path, translated_xml)
            suffix = f" (via {used_model})" if used_model != model else ""
            action = "Previewed" if dry_run else "Created" if is_new_file else "Updated"
            print(f"✅ {action} {folder}/strings.xml{suffix}")
            succeeded += 1
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            print("❌ [{}] {}. Existing file preserved.".format(folder, exc))
            failed += 1

        if args.sleep > 0:
            time.sleep(args.sleep)

    print("\nTranslation summary: {} succeeded, {} failed, {} skipped{}.".format(
        succeeded, failed, skipped, " (preview only)" if dry_run else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
