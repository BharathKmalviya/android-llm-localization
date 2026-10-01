"""Best-effort release notices for interactive CLI sessions."""

import json
import os
from pathlib import Path
import re
import sys
import threading
import time
import urllib.request

from android_localisation import __version__
from android_localisation.resources import atomic_write

CHECK_INTERVAL = 24 * 60 * 60
PYPI_URL = "https://pypi.org/pypi/android-localisation/json"


def _stable_version(value):
    # This package releases semantic versions; never advertise prereleases.
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,6}\.[0-9]{1,6}\.[0-9]{1,6}", value):
        return None
    return tuple(int(part) for part in value.split("."))


def _cache_path():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "android-localisation" / "update.json"


def start_update_check():
    """Return notice state; refresh in a daemon thread without waiting for network."""
    try:
        if os.environ.get("ANDROID_LOCALISE_NO_UPDATE_CHECK") or os.environ.get("CI"):
            return None
        if not sys.stdout.isatty() or not sys.stderr.isatty():
            return None
        if _stable_version(__version__) is None:
            return None
        path = _cache_path()
        now = time.time()
        state = {"latest": None}
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if _stable_version(cached.get("latest")):
                state["latest"] = cached["latest"]
            checked = cached.get("checked_at")
            if isinstance(checked, (int, float)) and 0 <= now - checked < CHECK_INTERVAL:
                return state
        except (OSError, ValueError, TypeError, AttributeError):
            pass

        def refresh():
            try:
                request = urllib.request.Request(
                    PYPI_URL,
                    headers={"User-Agent": "android-localisation/{}".format(__version__)},
                )
                with urllib.request.urlopen(request, timeout=1) as response:
                    payload = json.loads(response.read(512 * 1024).decode("utf-8"))
                latest = payload["info"]["version"]
                if _stable_version(latest):
                    state["latest"] = latest
            except Exception:
                # Offline, malformed replies and lookup failures never affect commands.
                pass
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(str(path), json.dumps({"checked_at": now, "latest": state["latest"]}))
            except Exception:
                pass

        threading.Thread(target=refresh, name="release-check", daemon=True).start()
        return state
    except Exception:
        return None


def show_update_notice(state):
    """Print only a completed/cached check, preserving stdout and exit status."""
    try:
        latest = state.get("latest") if state else None
        available = _stable_version(latest)
        installed = _stable_version(__version__)
        if available and installed and available > installed:
            print(
                "\nUpdate available: android-localisation {} (installed {}).\n"
                "Upgrade: pip install --upgrade android-localisation".format(latest, __version__),
                file=sys.stderr,
            )
    except Exception:
        pass
