"""
Unified CLI entry point for android-localisation.

Usage:
    android-localise translate --api-key KEY
    android-localise fix
    android-localise verify
    android-localise models
"""

import argparse
from android_localisation import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="android-localise",
        description="Zero-dependency Android strings.xml localization using LLMs.",
    )
    parser.add_argument("--version", action="version", version=f"android-localisation {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- translate ---
    translate_parser = subparsers.add_parser("translate", help="Translate strings.xml into all locale directories")
    translate_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")
    translate_parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini", help="AI provider (default: gemini)")
    translate_parser.add_argument("--model", help="Any model name supported by the provider (uses provider default if not set)")
    translate_parser.add_argument("--api-key", help="API key (or set GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY)")
    translate_parser.add_argument("--base-url", help="Custom OpenAI-compatible endpoint URL (required for 'custom' provider)")
    translate_parser.add_argument("--app-context", help="Short description of your app for better translations")
    translate_parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between API requests (default: 5.0)")
    translate_parser.add_argument("--languages", help="Comma-separated language codes, e.g. hi,es,fr,de — creates folders and strings.xml automatically")

    # --- fix ---
    fix_parser = subparsers.add_parser("fix", help="Fix XML escaping issues in translated strings.xml files")
    fix_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    # --- verify ---
    verify_parser = subparsers.add_parser("verify", help="Verify translated strings won't crash the app (requires javac)")
    verify_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    # --- models ---
    models_parser = subparsers.add_parser("models", help="List all available models per provider")
    models_parser.add_argument("--provider", choices=["gemini", "openai", "anthropic"], default=None,
                               help="Filter by provider (shows all if not set)")

    args = parser.parse_args()

    if args.command == "translate":
        from android_localisation.translate import main as run
        run(args)

    elif args.command == "fix":
        from android_localisation.fix import main as run
        run(args)

    elif args.command == "verify":
        from android_localisation.verify import main as run
        run(args)

    elif args.command == "models":
        from android_localisation.translate import PROVIDER_MODELS
        providers = [args.provider] if args.provider else ["gemini", "openai", "anthropic"]
        print()
        for p in providers:
            models = PROVIDER_MODELS.get(p, [])
            print(f"  {p.upper()}")
            for i, m in enumerate(models):
                tag = " (default)" if i == 0 else f" (fallback {i})" if i < len(models) - 1 else " (fallback)"
                print(f"    {'→' if i == 0 else ' '} {m}{tag}")
            print()
        print("  CUSTOM (Ollama, LM Studio, etc.)")
        print("    → Any model name your local server supports (must use --model)")
        print()
        print("  Tip: use --model to pick any model, e.g:")
        print("    android-localise translate --provider openai --model gpt-4o --api-key KEY")
        print()


if __name__ == "__main__":
    main()
