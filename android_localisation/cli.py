"""
Unified CLI entry point for android-localisation.

Usage:
    android-localise translate --api-key KEY
    android-localise store-listing --source listing.json --languages hi,es-ES
    android-localise fix
    android-localise verify
    android-localise models
"""

import argparse
import sys
from android_localisation import __version__


def main(args=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="android-localise",
        description="Zero-dependency Android strings.xml and Google Play listing localization using LLMs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Typical workflow:
  android-localise translate --languages hi,es --app-context "a notes app"
  android-localise fix
  android-localise verify

Other examples:
  android-localise translate --languages all
  android-localise store-listing --source listing.json --languages all
  android-localise store-listing --source listing.json --languages hi,es-ES
  android-localise translate --languages hi --missing-only --dry-run
  android-localise models --provider openai
  python -m android_localisation setup-path          (Windows, one-time)

Use android-localise COMMAND --help for flags, defaults and examples.
All commands also work with: python -m android_localisation COMMAND
Keys: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or API_KEY.
Update notices: set ANDROID_LOCALISE_NO_UPDATE_CHECK=1 to disable them.""",
    )
    parser.add_argument("--version", action="version", version=f"android-localisation {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", title="commands")
    subparsers.required = True

    # --- translate ---
    translate_parser = subparsers.add_parser(
        "translate", help="Translate strings.xml into selected or existing locales",
        description="""Translate values/strings.xml using the selected provider and app context.
Output is validated before saving. Existing locale files are refreshed by
default; --missing-only preserves existing resources and fills missing ones.
Use --skip-existing to skip reviewed files, or --source/--output-dir for custom paths.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  android-localise translate --languages all
  android-localise translate --languages hi,es --app-context "a notes app"
  android-localise translate --provider openai --res-dir path/to/res
  android-localise translate --languages hi --missing-only --dry-run
  android-localise translate --provider custom --model YOUR_LOCAL_MODEL --base-url http://localhost:11434/v1/chat/completions

Source: RES_DIR/values/strings.xml unless --source is set. Existing destination
locale folders are used when --languages and --languages-file are omitted.
Combine all/custom languages and exclusions. --dry-run may incur API charges.
Exit codes: 0 success, 1 setup/API/validation/save failure, 2 invalid arguments.
Use android-localise models to see current defaults and fallbacks.""",
    )
    translate_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")
    from android_localisation.translate import add_flexible_arguments
    add_flexible_arguments(translate_parser)
    translate_parser.add_argument("--provider", choices=["gemini", "openai", "anthropic", "custom"], default="gemini", help="AI provider (default: gemini)")
    translate_parser.add_argument("--model", help="Pin any supported model and disable fallbacks (default: provider default; see models)")
    translate_parser.add_argument("--api-key", help="API key, or set GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / API_KEY")
    translate_parser.add_argument("--base-url", help="Custom OpenAI-compatible endpoint URL (required for 'custom' provider)")
    translate_parser.add_argument("--app-context", help="Short description of your app for better translations")
    translate_parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between API requests (default: 5.0)")
    from android_localisation.translate import DEFAULT_API_TIMEOUT, MAX_TIMEOUT_RETRIES
    translate_parser.add_argument(
        "--timeout", type=float, default=DEFAULT_API_TIMEOUT,
        help=f"Seconds to wait for each API response, up to {MAX_TIMEOUT_RETRIES + 1} attempts on timeout (default: {DEFAULT_API_TIMEOUT})",
    )
    translate_parser.add_argument("--languages", help="Comma-separated Android or Play tags and/or 'all' (hi,es-ES,b+zh+Hans,all,zu)")
    translate_parser.add_argument("--missing-only", action="store_true", help="Translate missing resources while retaining existing translations")
    translate_parser.add_argument("--dry-run", action="store_true", help="Generate and validate translations, then show a diff without writing files (API usage applies)")

    # --- store-listing ---
    from android_localisation.store_listing import add_arguments
    listing_parser = subparsers.add_parser(
        "store-listing", help="Translate Google Play app name and descriptions",
        description="""Translate a UTF-8 JSON listing into selected Google Play languages.
Validates required fields and 30/80/4000 character limits before atomic saves.
Existing files are skipped unless --overwrite is set. Review policy compliance
and translation quality before submitting to Google Play.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  android-localise store-listing --source listing.json --languages all
  android-localise store-listing --source listing.json --languages hi,es-ES
  android-localise store-listing --source listing.json --languages ja --keep-app-name --dry-run
  android-localise store-listing --source listing.json --languages pt-BR --overwrite

JSON keys: app_name, short_description, full_description (all required strings).
Outputs: OUTPUT_DIR/LOCALE.json. Use Play locales, not Android values- folders.
Invalid model output gets up to two correction requests (API usage applies).
Exit codes: 0 success, 1 setup/API/validation/save failure, 2 invalid arguments.""",
    )
    add_arguments(listing_parser)

    # --- fix ---
    fix_parser = subparsers.add_parser(
        "fix", help="Repair apostrophe and percent escaping in locale strings",
        description="""Repair escaping in locale <string> text and save validated XML atomically.
Skips formatted=false and translatable=false strings. Does not repair
malformed XML, double quotes, string-array items or plural items.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  android-localise fix
  android-localise fix --res-dir path/to/res

Run verify and your Android build afterward. Exit code 1 reports failures.""",
    )
    fix_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    # --- verify ---
    verify_parser = subparsers.add_parser(
        "verify", help="Check XML resources and Java format arguments (requires JDK)",
        description="""Compare localized strings.xml files with values/strings.xml, then run
Java formatting checks for strings, arrays and plurals. Checks cover XML,
resource coverage, protected content, attributes, markup and format arguments.
Requires java and javac on PATH; does not replace an Android build or review.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  android-localise verify
  android-localise verify --res-dir path/to/res

Exit code 0 means checks passed; 1 reports resource, Java or setup failures.""",
    )
    verify_parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory (default: app/src/main/res)")

    # --- models ---
    models_parser = subparsers.add_parser(
        "models", help="List configured model defaults and fallbacks",
        description="""List this CLI release's provider defaults and automatic fallback models.
Use translate --model to pin a model, including models not in this list.
Custom/local providers require an explicit --model.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  android-localise models
  android-localise models --provider openai""",
    )
    models_parser.add_argument("--provider", choices=["gemini", "openai", "anthropic"], default=None,
                               help="Filter by provider (shows all if not set)")

    subparsers.add_parser(
        "setup-path", help="Add the installed Scripts folder to Windows user PATH",
        description="""One-time Windows setup for an installed CLI that PowerShell cannot find.
Adds the installed Scripts folder to user PATH without administrator access,
preserving entries and avoiding duplicates. Virtual environments use activation.
Ordinary commands and pip installation do not change PATH.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Run with the same Python that installed the package:
  python -m android_localisation setup-path

Close and reopen your terminal application afterward. Until then, use:
  python -m android_localisation --help

Exit code 1 reports unsupported platforms, virtual environments or setup failures.""",
    )

    if args is None or isinstance(args, list):
        argv = sys.argv[1:] if args is None else args
        if not argv:
            parser.print_help()
            return 0
        args = parser.parse_args(argv)

    from android_localisation.updates import start_update_check, show_update_notice
    update_state = start_update_check()
    try:
        return _run_command(args)
    finally:
        show_update_notice(update_state)


def _run_command(args):
    if args.command == "setup-path":
        from android_localisation.setup_path import main as run
        return run(args)

    elif args.command == "translate":
        from android_localisation.translate import main as run
        return run(args)

    elif args.command == "store-listing":
        from android_localisation.store_listing import main as run
        return run(args)

    elif args.command == "fix":
        from android_localisation.fix import main as run
        return run(args)

    elif args.command == "verify":
        from android_localisation.verify import main as run
        return run(args)

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
        print("    android-localise translate --provider openai --model gpt-6-luna --api-key KEY")
        print()


if __name__ == "__main__":
    raise SystemExit(main())
