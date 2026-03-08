import os
import re
import glob
import argparse

def main(args=None):
    parser = argparse.ArgumentParser(description="Fix common string formatting issues in Android strings.xml files.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    args = parser.parse_args(args)

    res_dir = args.res_dir
    print(f"Fixing strings in: {res_dir}")
    files = glob.glob(os.path.join(res_dir, "values-*", "strings.xml"))
    fixed_count = 0

    for xml_file in files:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()

        def fix_match(m):
            prefix = m.group(1)
            text = m.group(2)
            suffix = m.group(3)

            # Replace literal unicode or escaped unicode apostrophes
            text = text.replace(r'\u2019', r"\'")
            text = text.replace('\u2019', r"\'")

            # Unescape java-style unicode percent signs so we can process them
            text = text.replace(r'\u0025', '%')

            # Escape apostrophes (that are not already escaped)
            text = re.sub(r"(?<!\\)'", r"\'", text)

            # Escape double quotes (that are not already escaped)
            text = re.sub(r'(?<!\\)"', r'\"', text)

            # Fix % symbols:
            # 1. Collapse consecutive '%' to a single '%'
            text = re.sub(r'%+', '%', text)

            # 2. Re-escape purely literal % symbols to '%%'
            text = re.sub(r'%(?!1\$d|1\$s|d|s)', '%%', text)

            return prefix + text + suffix

        new_content = re.sub(
            r'(<string[^>]*name="[^"]*"[^>]*>)(.*?)(</string>)',
            fix_match, content, flags=re.DOTALL
        )

        if content != new_content:
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            fixed_count += 1

    print(f"Done fixing strings. Fixed {fixed_count} files out of {len(files)}.")

if __name__ == "__main__":
    main()
