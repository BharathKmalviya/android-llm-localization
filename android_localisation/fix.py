import os
import re
import glob
import argparse

# Matches any valid Java/Android format specifier:
# e.g. %s, %d, %f, %1$s, %2$d, %1$f, %-10s, %+d, etc.
_FORMAT_SPECIFIER = re.compile(
    r'%(\d+\$)?([-#+ 0,(<]*)?(\d+)?(\.\d+)?([tT]?[a-zA-Z])'
)

# Recognizes valid specifier suffixes so we don't double-escape them
_VALID_SPECIFIER = re.compile(
    r'%(\d+\$)?([-#+ 0,(<]*)?(\d+)?(\.\d+)?([tT]?[a-zA-Z%])'
)


def _fix_text(text):
    # Replace unicode curly apostrophes (common LLM hallucination)
    for curly in ('\u2019', '\u2018'):
        text = text.replace(curly, r"\'")

    # Unescape java-style unicode percent signs so we can process them uniformly
    text = text.replace(r'\u0025', '%')

    # Escape unescaped apostrophes (negative lookbehind to avoid double-escaping)
    text = re.sub(r"(?<!\\)'", r"\'", text)

    # Fix % symbols:
    # 1. Preserve valid format specifiers by replacing them with a placeholder
    placeholders = []
    def save_specifier(m):
        placeholders.append(m.group(0))
        return f"\x00FMTSPEC{len(placeholders) - 1}\x00"

    text = _VALID_SPECIFIER.sub(save_specifier, text)

    # 2. Any remaining bare % must be a literal — escape it
    text = text.replace('%', '%%')

    # 3. Restore the real format specifiers
    for i, spec in enumerate(placeholders):
        text = text.replace(f"\x00FMTSPEC{i}\x00", spec)

    return text


def _parse_args(args=None):
    parser = argparse.ArgumentParser(description="Fix common string formatting issues in Android strings.xml files.")
    parser.add_argument("--res-dir", default="app/src/main/res", help="Path to the Android res/ directory")
    return parser.parse_args(args)


def main(args=None):
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    res_dir = args.res_dir
    print(f"Fixing strings in: {res_dir}")
    files = glob.glob(os.path.join(res_dir, "values-*", "strings.xml"))
    fixed_count = 0

    for xml_file in files:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()

        def fix_match(m):
            return m.group(1) + _fix_text(m.group(2)) + m.group(3)

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
