import os
import re
import argparse
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from android_localisation.resources import atomic_write, locale_folders, parse_resources

# Retain format-looking patterns rather than guessing corrections.
# The verifier checks actual conversions and argument compatibility.
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
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if args is None or isinstance(args, list):
        args = _parse_args(args)

    res_dir = args.res_dir
    print(f"Fixing strings in: {res_dir}")
    if not os.path.isdir(res_dir):
        print("ERROR: Resource directory does not exist: {}".format(res_dir))
        return 1
    files = [os.path.join(res_dir, folder, "strings.xml") for folder in locale_folders(res_dir)
             if os.path.isfile(os.path.join(res_dir, folder, "strings.xml"))]
    fixed_count = 0
    failed_count = 0

    for xml_file in files:
        try:
            with open(xml_file, 'r', encoding='utf-8', newline='') as f:
                content = f.read()
            parse_resources(content)
        except (OSError, ValueError) as exc:
            print("ERROR: {}: {}".format(xml_file, exc))
            failed_count += 1
            continue

        def fix_match(m):
            opening_tag = m.group(1)
            # Skip strings marked formatted="false" — their % signs are literal, not specifiers
            if re.search(r"\b(?:formatted|translatable)\s*=\s*['\"]false['\"]", opening_tag, flags=re.IGNORECASE):
                return m.group(0)
            # Only fix text segments; attributes inside inline markup are protected.
            parts = re.split(r"(<[^>]+>)", m.group(2))
            value = "".join(part if part.startswith("<") else _fix_text(part) for part in parts)
            return opening_tag + value + m.group(3)

        new_content = re.sub(
            r"(<string\b[^>]*\bname\s*=\s*['\"][^'\"]*['\"][^>]*>)(.*?)(</string>)",
            fix_match, content, flags=re.DOTALL
        )

        if content != new_content:
            try:
                parse_resources(new_content)
                atomic_write(xml_file, new_content)
                fixed_count += 1
            except (OSError, ValueError) as exc:
                print("ERROR: {}: {}. Existing file preserved.".format(xml_file, exc))
                failed_count += 1

    print(f"Done fixing strings. Fixed {fixed_count} files out of {len(files)}.")
    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
