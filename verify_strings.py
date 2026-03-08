import os
import subprocess
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Verify Android strings formatting.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    java_file = os.path.join(script_dir, "VerifyStrings.java")
    
    # 1. Compile the Java verifier
    print(f"Compiling VerifyStrings.java...")
    try:
        compile_result = subprocess.run(["javac", java_file], cwd=project_root, check=True)
    except FileNotFoundError:
        print("\n[!] ERROR: 'javac' command not found.")
        print("    Please ensure you have a Java JDK installed and 'javac' is in your system PATH.")
        print("    Alternatively, run this script from the Terminal inside Android Studio.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Failed to compile VerifyStrings.java")
        sys.exit(1)

    # 2. Run the Java verifier
    print(f"Running String Verifier against {args.res_dir}...")
    # Pass the res_dir as an argument to the Java program
    run_result = subprocess.run(["java", "-cp", script_dir, "VerifyStrings", args.res_dir], cwd=project_root)
    
    if run_result.returncode != 0:
        print("\n[!] VERIFICATION FAILED: Found broken string formatting that could crash the app.")
        sys.exit(run_result.returncode)
    else:
        print("\n[+] VERIFICATION PASSED: All localizations are syntactically safe.")

if __name__ == "__main__":
    main()
