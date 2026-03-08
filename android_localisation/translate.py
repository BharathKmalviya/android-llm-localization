import os
import time
import argparse
import urllib.request
import urllib.error
import json

DEFAULT_RES_DIR = "app/src/main/res"
API_TIMEOUT = 60  # seconds


def get_target_directories(res_dir):
    """Finds all values-* directories inside the provided res/ directory."""
    dirs = []
    if not os.path.exists(res_dir):
        return dirs
    for d in os.listdir(res_dir):
        if d.startswith("values-") and os.path.isdir(os.path.join(res_dir, d)):
            dirs.append(d)
    return sorted(dirs)


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
                return None
            return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Gemini API Error: {e.code} - {_read_error_body(e)}")
        return None


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
                return None
            return choices[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ OpenAI (compatible) API Error: {e.code} - {_read_error_body(e)}")
        return None


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
                return None
            return content[0].get("text", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Anthropic API Error: {e.code} - {_read_error_body(e)}")
        return None


def translate_xml(provider, api_key, model, source_xml, target_folder_name, app_context, base_url=None):
    """Calls the selected provider API to translate the XML into the target language."""
    prompt = build_prompt(source_xml, target_folder_name, app_context)
    if provider == "gemini":
        result = call_gemini(api_key, model, prompt)
    elif provider == "openai":
        url = base_url if base_url else "https://api.openai.com/v1/chat/completions"
        result = call_openai_compatible(api_key, url, model, prompt)
    elif provider == "anthropic":
        result = call_anthropic(api_key, model, prompt)
    else:
        print(f"❌ Unknown provider: {provider}")
        return None
    return clean_xml_response(result)


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description="Translate Android strings.xml using LLMs.")
    parser.add_argument("--res-dir", default=DEFAULT_RES_DIR)
    parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini")
    parser.add_argument("--model")
    parser.add_argument("--api-key")
    parser.add_argument("--base-url")
    parser.add_argument("--app-context")
    parser.add_argument("--sleep", type=float, default=5.0)
    return parser.parse_args(args)


def main(args=None):
    # Accept either a pre-parsed Namespace (from cli.py) or raw argv list
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    # Resolve model default
    model = args.model
    if not model:
        if args.provider == "gemini":       model = "gemini-2.5-flash"
        elif args.provider == "openai":     model = "gpt-4o-mini"
        elif args.provider == "anthropic":  model = "claude-3-5-sonnet-latest"
        elif args.provider == "custom":
            print("❌ ERROR: You must specify --model when using a custom provider.")
            return

    # Resolve API key
    api_key = args.api_key
    if not api_key:
        if args.provider == "gemini":                   api_key = os.environ.get("GEMINI_API_KEY")
        elif args.provider in ("openai", "custom"):     api_key = os.environ.get("OPENAI_API_KEY")
        elif args.provider == "anthropic":              api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            api_key = os.environ.get("API_KEY")

    if not api_key and args.provider != "custom":
        print("❌ ERROR: Please provide an API key via --api-key or the appropriate environment variable.")
        return

    if args.provider == "custom" and not args.base_url:
        print("❌ ERROR: You must provide --base-url when using a custom provider.")
        return

    res_dir = args.res_dir
    source_strings_xml = os.path.join(res_dir, "values", "strings.xml")

    print(f"🔍 Reading source XML from: {source_strings_xml}")
    if not os.path.exists(source_strings_xml):
        print("❌ ERROR: Could not find English strings.xml at the specified path.")
        return

    source_xml = read_source_xml(source_strings_xml)
    target_dirs = get_target_directories(res_dir)

    if not target_dirs:
        print(f"⚠️  No values-* localized directories found in {res_dir}")
        return

    print(f"🌍 Found {len(target_dirs)} language directories.")
    print(f"🤖 Using Provider: {args.provider.upper()} | Model: {model}")

    for folder in target_dirs:
        target_path = os.path.join(res_dir, folder, "strings.xml")
        print(f"⏳ Translating for {folder}...")

        provider_name = "openai" if args.provider == "custom" else args.provider
        translated_xml = translate_xml(
            provider_name, api_key, model, source_xml,
            folder, args.app_context, args.base_url
        )

        if translated_xml and "<resources>" in translated_xml and "</resources>" in translated_xml:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(translated_xml)
            print(f"✅ Saved translated strings.xml to {folder}")
        else:
            print(f"⚠️  Failed or got invalid XML for {folder}. Skipping.")

        if args.sleep > 0:
            time.sleep(args.sleep)

    print("\n🎉 Translation process completed!")


if __name__ == "__main__":
    main()
