import os
import time
import argparse
import urllib.request
import urllib.error
import json

DEFAULT_RES_DIR = "app/src/main/res"
API_TIMEOUT = 60  # seconds

# Ordered list of models per provider.
# First entry = default. Rest = automatic fallbacks (used only when user hasn't pinned a model).
PROVIDER_MODELS = {
    "gemini": [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-latest",
    ],
    "custom": [],  # user must specify --model
}


def get_target_directories(res_dir):
    """Finds all values-* directories inside the provided res/ directory."""
    dirs = []
    if not os.path.exists(res_dir):
        return dirs
    for d in os.listdir(res_dir):
        if d.startswith("values-") and os.path.isdir(os.path.join(res_dir, d)):
            dirs.append(d)
    return sorted(dirs)


def ensure_locale_dirs(res_dir, languages):
    """
    Creates values-<lang> directories for each language code in the list.
    Returns the list of folder names created or already existing.
    """
    created = []
    for lang in languages:
        lang = lang.strip()
        if not lang:
            continue
        folder = f"values-{lang}" if not lang.startswith("values-") else lang
        folder_path = os.path.join(res_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            print(f"📁 Created {folder}/")
            created.append(folder)
        else:
            created.append(folder)
    return created


def read_source_xml(source_path):
    with open(source_path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(source_xml, target_folder_name, app_context):
    context_str = f"an Android app ({app_context})" if app_context else "an Android application"
    return f"""You are a professional mobile app localization expert.

I am sending you the complete English `strings.xml` for {context_str}.
Your job is to translate it into the language corresponding to the Android resource directory: `{target_folder_name}`.
For example, `values-hi` is Hindi, `values-es-rES` is Spanish (Spain), `values-zh-rTW` is Traditional Chinese, etc.

STRICT GUIDELINES:
1. Preserve the exact meaning and intent of the English text.
2. The language must be clear, natural, human-sounding, and understandable by all users (from rural to tier-1 cities).
3. Do not sound like a machine translation. Use simple, everyday mobile UI language.
4. NEVER modify string keys, XML structure, placeholders (like %s, %1$d), escape characters, \\n line breaks, or HTML tags.
5. Keep it short and UI friendly.
6. Return ONLY the raw updated XML content. Do not add markdown formatting like ```xml or any conversational text.

SOURCE XML:
{source_xml}
"""


def clean_xml_response(result):
    if not result:
        return ""
    result = result.strip()
    if result.startswith("```xml"):
        result = result[6:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()


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


def call_gemini(api_key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if not candidates:
                print("  ❌ Gemini returned no candidates.")
                return None, False
            return result["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", ""), False
    except urllib.error.HTTPError as e:
        body = _read_error_body(e)
        model_gone = _is_model_not_found(e.code, body)
        print(f"  ❌ Gemini API Error: {e.code} - {body}")
        return None, model_gone


def call_openai_compatible(api_key, base_url, model, prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key or ''}",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(base_url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            choices = result.get("choices", [])
            if not choices:
                print("  ❌ OpenAI returned no choices.")
                return None, False
            return choices[0].get("message", {}).get("content", ""), False
    except urllib.error.HTTPError as e:
        body = _read_error_body(e)
        model_gone = _is_model_not_found(e.code, body)
        print(f"  ❌ OpenAI (compatible) API Error: {e.code} - {body}")
        return None, model_gone


def call_anthropic(api_key, model, prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result.get("content", [])
            if not content:
                print("  ❌ Anthropic returned no content.")
                return None, False
            return content[0].get("text", ""), False
    except urllib.error.HTTPError as e:
        body = _read_error_body(e)
        model_gone = _is_model_not_found(e.code, body)
        print(f"  ❌ Anthropic API Error: {e.code} - {body}")
        return None, model_gone


def _call_provider(provider, api_key, model, prompt, base_url=None):
    """Dispatches to the right API. Returns (text, model_not_found)."""
    if provider == "gemini":
        return call_gemini(api_key, model, prompt)
    elif provider == "openai":
        url = base_url if base_url else "https://api.openai.com/v1/chat/completions"
        return call_openai_compatible(api_key, url, model, prompt)
    elif provider == "anthropic":
        return call_anthropic(api_key, model, prompt)
    else:
        print(f"❌ Unknown provider: {provider}")
        return None, False


def translate_xml(provider, api_key, model, source_xml, target_folder_name, app_context,
                  base_url=None, fallback_models=None):
    """
    Calls the selected provider API to translate the XML.
    If the model is not found and fallback_models are provided, retries with the next one.
    Returns (translated_xml, model_used).
    """
    prompt = build_prompt(source_xml, target_folder_name, app_context)
    models_to_try = [model] + (fallback_models or [])

    for attempt_model in models_to_try:
        if attempt_model != model:
            print(f"  ↩️  Falling back to model: {attempt_model}")
        result, model_not_found = _call_provider(provider, api_key, attempt_model, prompt, base_url)
        if result is not None:
            return clean_xml_response(result), attempt_model
        if not model_not_found:
            # Failed for a non-model reason (auth, quota, network) — don't try fallbacks
            return None, attempt_model

    return None, models_to_try[-1]


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description="Translate Android strings.xml using LLMs.")
    parser.add_argument("--res-dir", default=DEFAULT_RES_DIR)
    parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini")
    parser.add_argument("--model", help="Any model name for the chosen provider. Uses provider default if not set.")
    parser.add_argument("--api-key")
    parser.add_argument("--base-url")
    parser.add_argument("--app-context")
    parser.add_argument("--sleep", type=float, default=5.0)
    parser.add_argument("--languages", help="Comma-separated language codes to translate into, e.g. hi,es,fr,de. Creates folders automatically if they don't exist.")
    return parser.parse_args(args)


def main(args=None):
    if args is None or isinstance(args, list):
        args = _parse_args(args)

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
            return
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
        return

    if provider == "custom" and not args.base_url:
        print("❌ ERROR: You must provide --base-url when using a custom provider.")
        return

    res_dir = args.res_dir
    source_strings_xml = os.path.join(res_dir, "values", "strings.xml")

    print(f"🔍 Reading source XML from: {source_strings_xml}")
    if not os.path.exists(source_strings_xml):
        print("❌ ERROR: Could not find English strings.xml at the specified path.")
        return

    source_xml = read_source_xml(source_strings_xml)

    # Build target directory list — from --languages flag or by scanning res_dir
    if args.languages:
        lang_codes = [l.strip() for l in args.languages.split(",") if l.strip()]
        target_dirs = ensure_locale_dirs(res_dir, lang_codes)
    else:
        target_dirs = get_target_directories(res_dir)

    if not target_dirs:
        print(f"⚠️  No locale directories found in {res_dir}.")
        print("    Either create values-<lang>/ folders manually, or use --languages to specify them:")
        print("    Example: android-localise translate --languages hi,es,fr,de --api-key YOUR_KEY")
        return

    print(f"🌍 Found {len(target_dirs)} language directories.")
    fallback_note = "" if user_pinned_model else f" (fallbacks: {', '.join(fallback_models)})" if fallback_models else ""
    print(f"🤖 Provider: {provider.upper()} | Model: {model}{fallback_note}")

    actual_provider = "openai" if provider == "custom" else provider

    for folder in target_dirs:
        target_path = os.path.join(res_dir, folder, "strings.xml")
        is_new_file = not os.path.exists(target_path)

        if is_new_file:
            print(f"⏳ [{folder}] No strings.xml found — creating and translating...")
        else:
            print(f"⏳ [{folder}] Updating existing strings.xml...")

        translated_xml, used_model = translate_xml(
            actual_provider, api_key, model, source_xml,
            folder, args.app_context, args.base_url, fallback_models
        )

        if translated_xml and "<resources>" in translated_xml and "</resources>" in translated_xml:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(translated_xml)
            suffix = f" (via {used_model})" if used_model != model else ""
            action = "Created" if is_new_file else "Updated"
            print(f"✅ {action} {folder}/strings.xml{suffix}")
        else:
            if translated_xml is None:
                print(f"⚠️  [{folder}] API call failed — see error above. Skipping.")
            elif "<resources>" not in translated_xml:
                preview = translated_xml[:200].replace("\n", " ") if translated_xml else "(empty response)"
                print(f"⚠️  [{folder}] Response missing <resources> tag. Skipping.")
                print(f"    Response preview: {preview}")
            else:
                print(f"⚠️  [{folder}] Response missing </resources> closing tag. Skipping.")

        if args.sleep > 0:
            time.sleep(args.sleep)

    print("\n🎉 Translation process completed!")


if __name__ == "__main__":
    main()
