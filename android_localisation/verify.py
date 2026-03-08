import os
import subprocess
import sys
import argparse


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description="Verify Android strings formatting.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    return parser.parse_args(args)


def main(args=None):
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    package_dir = os.path.dirname(os.path.abspath(__file__))
    java_file = os.path.join(package_dir, "java", "VerifyStrings.java")
    java_out_dir = os.path.join(package_dir, "java")
    project_root = os.getcwd()

    if not os.path.exists(java_file):
        print(f"[!] ERROR: Java verifier not found at {java_file}")
        print("    This may indicate a broken installation. Try:")
        print("      pip install --force-reinstall android-localisation")
        sys.exit(1)

    # 1. Compile the Java verifier
    print("Compiling VerifyStrings.java...")
    try:
        subprocess.run(["javac", "-d", java_out_dir, java_file], check=True)
    except FileNotFoundError:
        print("\n[!] ERROR: 'javac' command not found.")
        print("    Please ensure you have a Java JDK installed and 'javac' is in your system PATH.")
        print("    Alternatively, run this from the Terminal inside Android Studio.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Failed to compile VerifyStrings.java")
        sys.exit(1)

    # 2. Run the Java verifier
    print(f"Running String Verifier against {args.res_dir}...")
    run_result = subprocess.run(
        ["java", "-cp", java_out_dir, "VerifyStrings", args.res_dir],
        cwd=project_root
    )

    if run_result.returncode != 0:
        print("\n[!] VERIFICATION FAILED: Found broken string formatting that could crash the app.")
        sys.exit(run_result.returncode)
    else:
        print("\n[+] VERIFICATION PASSED: All localizations are syntactically safe.")


if __name__ == "__main__":
    main()
