import os
import subprocess
import sys
import argparse
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from android_localisation.resources import locale_folders, parse_resources, validate_resources


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description="Verify Android strings formatting.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    return parser.parse_args(args)


def main(args=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    package_dir = os.path.dirname(os.path.abspath(__file__))
    java_file = os.path.join(package_dir, "java", "VerifyStrings.java")
    project_root = os.getcwd()

    try:
        with open(os.path.join(args.res_dir, "values", "strings.xml"), encoding="utf-8") as handle:
            source_xml = handle.read()
        parse_resources(source_xml)
        failures = 0
        for folder in locale_folders(args.res_dir):
            path = os.path.join(args.res_dir, folder, "strings.xml")
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as handle:
                    validate_resources(source_xml, handle.read())
            except (OSError, ValueError) as exc:
                print("[!] {}: {}".format(folder, exc))
                failures += 1
        if failures:
            print("[!] Resource verification failed for {} locale(s).".format(failures))
            return 1
    except (OSError, ValueError) as exc:
        print("[!] ERROR: {}".format(exc))
        return 1

    if not os.path.exists(java_file):
        print(f"[!] ERROR: Java verifier not found at {java_file}")
        print("    This may indicate a broken installation. Try:")
        print("      pip install --force-reinstall android-localisation")
        return 1

    # Compile outside the installed package (which may be read-only).
    with tempfile.TemporaryDirectory(prefix="android-localise-") as java_out_dir:
        print("Compiling VerifyStrings.java...")
        try:
            subprocess.run(["javac", "-encoding", "UTF-8", "-d", java_out_dir, java_file], check=True)
            print(f"Running String Verifier against {args.res_dir}...")
            run_result = subprocess.run(
                ["java", "-cp", java_out_dir, "VerifyStrings", args.res_dir], cwd=project_root)
        except FileNotFoundError:
            print("[!] ERROR: 'javac' and 'java' must be in PATH. Use a JDK or Android Studio's terminal.")
            return 1
        except subprocess.CalledProcessError:
            print("[!] Failed to compile VerifyStrings.java")
            return 1

    if run_result.returncode != 0:
        print("\n[!] VERIFICATION FAILED: Found broken string formatting that could crash the app.")
        return run_result.returncode
    else:
        print("\n[+] VERIFICATION PASSED: Resource checks and Java formatting checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
