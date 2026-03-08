import os
import time
import argparse
import urllib.request
import urllib.error
import json

# ==========================================
# DEFAULT CONFIGURATION
# ==========================================
DEFAULT_RES_DIR = "app/src/main/res"

def get_target_directories(res_dir):
    """Finds all values-* directories inside the provided res/ directory"""
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
    """Builds the translation prompt."""
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
    """Removes markdown code blocks if the LLM accidentally includes them."""
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

# ==========================================
# LLM API CLIENTS (Using standard urllib)
# ==========================================

def call_gemini(api_key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Gemini API Error: {e.code} - {e.read().decode('utf-8')}")
        return None

def call_openai_compatible(api_key, base_url, model, prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    req = urllib.request.Request(base_url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ OpenAI (compatible) API Error: {e.code} - {e.read().decode('utf-8')}")
        return None

def call_anthropic(api_key, model, prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("content", [{}])[0].get("text", "")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Anthropic API Error: {e.code} - {e.read().decode('utf-8')}")
        return None

# ==========================================

def translate_xml(provider, api_key, model, source_xml, target_folder_name, app_context, base_url=None):
    """Calls the selected Provider API to translate the XML into the target language"""
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

def main():
    parser = argparse.ArgumentParser(description="Automate Android strings.xml translations using LLMs.")
    parser.add_argument("--res-dir", default=DEFAULT_RES_DIR, help="Path to the Android res/ directory (default: app/src/main/res)")
    parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini", help="AI provider to use (default: gemini)")
    parser.add_argument("--model", help="Specific model to use (e.g. gemini-2.5-flash, gpt-4o, claude-3-5-sonnet-latest). Defaults vary by provider.")
    parser.add_argument("--api-key", help="API Key (can also be set via environment variables like GEMINI_API_KEY, OPENAI_API_KEY)")
    parser.add_argument("--base-url", help="Custom base URL for OpenAI-compatible endpoints (required if provider is 'custom')")
    parser.add_argument("--app-context", help="A short description of your app to give the AI context (e.g., 'a fitness tracking app')")
    parser.add_argument("--sleep", type=float, default=5.0, help="Seconds to sleep between requests to avoid rate limits (default: 5.0)")

    args = parser.parse_args()

    # Determine Model
    model = args.model
    if not model:
        if args.provider == "gemini": model = "gemini-2.5-flash"
        elif args.provider == "openai": model = "gpt-4o-mini"
        elif args.provider == "anthropic": model = "claude-3-5-sonnet-latest"
        elif args.provider == "custom":
            print("❌ ERROR: You must specify --model when using a custom provider.")
            return

    # Determine API Key
    api_key = args.api_key
    if not api_key:
        if args.provider == "gemini": api_key = os.environ.get("GEMINI_API_KEY")
        elif args.provider == "openai" or args.provider == "custom": api_key = os.environ.get("OPENAI_API_KEY")
        elif args.provider == "anthropic": api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Allow simple fallback API_KEY env var
        if not api_key:
            api_key = os.environ.get("API_KEY")

    if not api_key and args.provider != "custom": # Custom might not need a key (e.g. local Ollama)
        print(f"❌ ERROR: Please provide an API key using --api-key or set the appropriate environment variable.")
        return
        
    if args.provider == "custom" and not args.base_url:
        print("❌ ERROR: You must provide a --base-url when using a custom provider.")
        return

    # Setup Paths
    res_dir = args.res_dir
    source_strings_xml = os.path.join(res_dir, "values", "strings.xml")

    print(f"🔍 Reading source XML from: {source_strings_xml}")
    if not os.path.exists(source_strings_xml):
        print("❌ ERROR: Could not find English strings.xml at the specified path.")
        return

    source_xml = read_source_xml(source_strings_xml)
    target_dirs = get_target_directories(res_dir)
    
    if not target_dirs:
        print(f"⚠️ No values-* localized directories found in {res_dir}")
        return
        
    print(f"🌍 Found {len(target_dirs)} language directories.")
    print(f"🤖 Using Provider: {args.provider.upper()} | Model: {model}")
    
    for folder in target_dirs:
        target_path = os.path.join(res_dir, folder, "strings.xml")
        
        print(f"⏳ Translating for {folder}...")
        
        provider_name = "openai" if args.provider == "custom" else args.provider
        translated_xml = translate_xml(provider_name, api_key, model, source_xml, folder, args.app_context, args.base_url)
        
        if translated_xml and "<resources>" in translated_xml:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(translated_xml)
            print(f"✅ Saved translated strings.xml to {folder}")
        else:
            print(f"⚠️ Failed or got invalid XML for {folder}. Skipping.")
        
        if args.sleep > 0:
            time.sleep(args.sleep)

    print("\n🎉 Translation process completed!")

if __name__ == "__main__":
    main()
