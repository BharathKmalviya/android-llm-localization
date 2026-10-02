"""Explicit, user-scoped API key storage in Windows Credential Manager."""

import argparse
import ctypes
import getpass
import os
import sys
import warnings
from ctypes import wintypes


PROVIDERS = ("gemini", "openai", "anthropic")
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
_GENERIC = 1
_LOCAL_MACHINE = 2  # Persistent on this computer, still scoped to the user.
_NOT_FOUND = 1168
_MAX_BLOB = 2560


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)), ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


def _target(provider):
    if provider not in PROVIDERS:
        raise ValueError("Saved keys support gemini, openai and anthropic only.")
    return "android-localisation:api-key:" + provider


def _windows_api():
    if os.name != "nt":
        raise OSError("Saved key commands require Windows Credential Manager. Use environment variables on other platforms.")
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    pointer = ctypes.POINTER(_Credential)
    api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.POINTER(pointer)]
    api.CredReadW.restype = wintypes.BOOL
    api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    api.CredDeleteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def _failure():
    # Do not include credential values or structures in diagnostics.
    return OSError("Windows Credential Manager failed (error {}).".format(ctypes.get_last_error()))


def save_key(provider, key):
    target = _target(provider)
    if not key or any(ord(char) < 33 or ord(char) > 126 for char in key):
        raise ValueError("API key must be nonempty printable ASCII without whitespace.")
    encoded = key.encode("ascii")
    if len(encoded) > _MAX_BLOB:
        raise ValueError("API key exceeds Windows Credential Manager's size limit.")
    api = _windows_api()
    blob = (wintypes.BYTE * len(encoded)).from_buffer_copy(encoded)
    credential = _Credential()
    credential.Type = _GENERIC
    credential.TargetName = target
    credential.Comment = "API key for android-localisation"
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = blob
    credential.Persist = _LOCAL_MACHINE
    credential.UserName = provider
    try:
        if not api.CredWriteW(ctypes.byref(credential), 0):
            raise _failure()
    finally:
        ctypes.memset(blob, 0, len(encoded))


def _read_key(provider, presence_only=False):
    target = _target(provider)
    api = _windows_api()
    pointer = ctypes.POINTER(_Credential)()
    if not api.CredReadW(target, _GENERIC, 0, ctypes.byref(pointer)):
        if ctypes.get_last_error() == _NOT_FOUND:
            return False if presence_only else None
        raise _failure()
    try:
        credential = pointer.contents
        if presence_only:
            return True
        size = credential.CredentialBlobSize
        if not 0 < size <= _MAX_BLOB or not credential.CredentialBlob:
            raise ValueError("Saved API key is invalid; save it again with credentials set.")
        try:
            key = ctypes.string_at(credential.CredentialBlob, size).decode("ascii")
        except UnicodeDecodeError:
            raise ValueError("Saved API key is invalid; save it again with credentials set.") from None
        if any(ord(char) < 33 or ord(char) > 126 for char in key):
            raise ValueError("Saved API key is invalid; save it again with credentials set.")
        return key
    finally:
        # The Python string still exists while needed; this is not a memory vault.
        if pointer.contents.CredentialBlob and pointer.contents.CredentialBlobSize <= _MAX_BLOB:
            ctypes.memset(pointer.contents.CredentialBlob, 0, pointer.contents.CredentialBlobSize)
        api.CredFree(pointer)


def remove_key(provider):
    target = _target(provider)
    api = _windows_api()
    if api.CredDeleteW(target, _GENERIC, 0):
        return True
    if ctypes.get_last_error() == _NOT_FOUND:
        return False
    raise _failure()


def resolve_api_key(provider, supplied=None, base_url=None):
    """Preserve argument/env precedence; use saved keys only for built-in endpoints."""
    env_name = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY", "custom": "OPENAI_API_KEY"}.get(provider)
    key = supplied or (os.environ.get(env_name) if env_name else None) or os.environ.get("API_KEY")
    if key:
        return key
    if os.name != "nt" or provider not in PROVIDERS:
        return None
    if provider == "openai" and base_url and base_url != OPENAI_ENDPOINT:
        return None  # Never silently forward a saved OpenAI key to a custom host.
    return _read_key(provider)


def add_arguments(parser):
    parser.add_argument("action", choices=("set", "status", "remove"),
                        help="Save via hidden prompt, report presence, or remove the saved key")
    parser.add_argument("--provider", choices=PROVIDERS, default="gemini",
                        help="Provider credential to manage (default: gemini)")


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return parser.parse_args(args)


def main(args=None):
    if args is None or isinstance(args, list):
        args = _parse_args(args)
    try:
        if args.action == "set":
            if os.name != "nt":
                raise OSError("Saved key commands require Windows Credential Manager. Use environment variables on other platforms.")
            if not sys.stdin.isatty():
                raise ValueError("Run credentials set yourself in an interactive terminal; piped keys are not accepted.")
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                key = getpass.getpass("{} API key (hidden): ".format(args.provider))
            try:
                save_key(args.provider, key)
            finally:
                key = None
            print("Saved {} API key in Windows Credential Manager for this user.".format(args.provider))
        elif args.action == "status":
            present = _read_key(args.provider, presence_only=True)
            print("{}: {}".format(args.provider, "saved" if present else "not saved"))
        elif args.action == "remove":
            removed = remove_key(args.provider)
            print("{}: {}".format(args.provider, "saved key removed" if removed else "no saved key"))
        else:
            raise ValueError("Unknown credentials action.")
    except (OSError, ValueError, getpass.GetPassWarning) as error:
        # Specific errors above are safe; getpass fallback must never echo a key.
        print("ERROR: {}".format(error))
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Key entry cancelled; saved credentials unchanged.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
