"""
Unified CLI entry point for android-localisation.

Usage:
    android-localise translate --api-key KEY
    android-localise fix
    android-localise verify
"""

import sys
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
    translate_parser.add_argument("--model", help="Model name (e.g. gemini-2.5-flash, gpt-4o, claude-3-5-sonnet-latest)")
    translate_parser.add_argument("--api-key", help="API key (or set GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY)")
    translate_parser.add_argument("--base-url", help="Custom OpenAI-compatible endpoint URL (required for 'custom' provider)")
    translate_parser.add_argument("--app-context", help="Short description of your app for better translations")
    translate_parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between API requests (default: 5.0)")

    # --- fix ---
    fix_parser = subparsers.add_parser("fix", help="Fix XML escaping issues in translated strings.xml files")
    fix_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    # --- verify ---
    verify_parser = subparsers.add_parser("verify", help="Verify translated strings won't crash the app (requires javac)")
    verify_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    args = parser.parse_args()

    if args.command == "translate":
        from android_localisation.translate import main as translate_main
        # Pass remaining args through as a list
        extra = []
        if args.res_dir != "app/src/main/res": extra += ["--res-dir", args.res_dir]
        if args.provider != "gemini": extra += ["--provider", args.provider]
        if args.model: extra += ["--model", args.model]
        if args.api_key: extra += ["--api-key", args.api_key]
        if args.base_url: extra += ["--base-url", args.base_url]
        if args.app_context: extra += ["--app-context", args.app_context]
        if args.sleep != 5.0: extra += ["--sleep", str(args.sleep)]
        translate_main(extra)

    elif args.command == "fix":
        from android_localisation.fix import main as fix_main
        extra = []
        if args.res_dir != "app/src/main/res": extra += ["--res-dir", args.res_dir]
        fix_main(extra)

    elif args.command == "verify":
        from android_localisation.verify import main as verify_main
        extra = []
        if args.res_dir != "app/src/main/res": extra += ["--res-dir", args.res_dir]
        verify_main(extra)

if __name__ == "__main__":
    main()
