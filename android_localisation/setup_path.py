"""One-time Windows user PATH setup; never run implicitly during imports."""

import argparse
import os
from pathlib import Path
import sys
import sysconfig


def _script_directory():
    directories = [sysconfig.get_path("scripts")]
    if "nt_user" in sysconfig.get_scheme_names():
        user_scripts = sysconfig.get_path("scripts", scheme="nt_user")
        user_library = sysconfig.get_path("purelib", scheme="nt_user")
        try:
            if os.path.normcase(os.path.commonpath([os.path.abspath(__file__), user_library])) == os.path.normcase(user_library):
                directories.insert(0, user_scripts)
            else:
                directories.append(user_scripts)
        except ValueError:
            directories.append(user_scripts)
    for directory in directories:
        if (Path(directory) / "android-localise.exe").is_file():
            return str(Path(directory).resolve())
    raise ValueError(
        "Cannot find android-localise.exe for this Python. Reinstall with: "
        "python -m pip install --upgrade android-localisation"
    )


def _contains_directory(path, directory):
    def normalized(value):
        return os.path.normcase(os.path.normpath(os.path.expandvars(value.strip().strip('"'))))
    return any(entry.strip() and normalized(entry) == normalized(directory)
               for entry in path.split(";"))


def _add_user_path(directory):
    import winreg
    if ";" in directory:
        raise ValueError("The Scripts directory contains a semicolon and cannot be added to PATH.")
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, "Environment", 0,
                           winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
        try:
            existing, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            existing, kind = "", winreg.REG_EXPAND_SZ
        if not isinstance(existing, str) or kind not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
            raise ValueError("User PATH has an unexpected registry type; no changes made.")
        if _contains_directory(existing, directory):
            return False
        separator = ";" if existing and not existing.endswith(";") else ""
        updated = existing + separator + directory
        if len(updated) >= 32767:
            raise ValueError("User PATH would exceed Windows' length limit; no changes made.")
        winreg.SetValueEx(key, "Path", 0, kind, updated)
    return True


def _notify_environment_change():
    # Let Windows shells refresh their environment; existing terminals still
    # inherit their original environment until the terminal application restarts.
    try:
        import ctypes
        from ctypes import wintypes
        notify = ctypes.WinDLL("user32", use_last_error=True).SendMessageTimeoutW
        notify.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                           ctypes.c_wchar_p, wintypes.UINT, wintypes.UINT,
                           ctypes.POINTER(ctypes.c_size_t)]
        notify.restype = wintypes.LPARAM
        result = ctypes.c_size_t()
        notify(0xffff, 0x001a, 0, "Environment", 2, 1000, ctypes.byref(result))
    except Exception:
        pass


def _parse_args(args=None):
    return argparse.ArgumentParser(description="Add this Python's CLI Scripts directory to Windows user PATH.").parse_args(args)


def main(args=None):
    if args is None or isinstance(args, list):
        args = _parse_args(args)
    if os.name != "nt":
        print("setup-path is for Windows. You can run the CLI with: python -m android_localisation --help")
        return 1
    if sys.prefix != sys.base_prefix or hasattr(sys, "real_prefix"):
        print("Virtual environment detected. Activate it to use android-localise; its temporary Scripts directory will not be added to user PATH.")
        return 1
    try:
        directory = _script_directory()
        changed = _add_user_path(directory)
    except (OSError, ValueError) as error:
        print("PATH setup failed: {}".format(error))
        return 1
    _notify_environment_change()
    print("{}: {}".format("Added to user PATH" if changed else "Already on user PATH", directory))
    print("Close and reopen your terminal application, then run: android-localise --help")
    print("You can use it immediately in this terminal with: python -m android_localisation --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
