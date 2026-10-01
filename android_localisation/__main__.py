"""Run the CLI through Python when its console script is not on PATH."""

from android_localisation.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
