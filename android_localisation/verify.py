import os
import subprocess
import sys
import argparse

def main(args=None):
    parser = argparse.ArgumentParser(description="Verify Android strings formatting.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    args = parser.parse_args(args)

    # VerifyStrings.java lives inside the package's java/ folder
    package_dir = os.path.dirname(os.path.abspath(__file__))
    java_file = os.path.join(package_dir, "java", "VerifyStrings.java")
    java_out_dir = os.path.join(package_dir, "java")
    project_root = os.getcwd()

    # 1. Compile the Java verifier
    print("Compiling VerifyStrings.java...")
    try:
        subprocess.run(["javac", java_file], cwd=project_root, check=True)
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
