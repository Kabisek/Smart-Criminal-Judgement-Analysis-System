#!/usr/bin/env python3
import json
import re
from pathlib import Path

INPUT = Path('data/structured/deepseek_json_20251121_185f13.json')
OUTPUT = Path('data/structured/deepseek_json_20251121_185f13_fixed.json')

def remove_trailing_commas(s):
    # remove trailing commas before closing braces/brackets
    s = re.sub(r',\s*(\]|\})', r'\1', s)
    return s

def try_load(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        return e


def balance_and_fix(content):
    # Initial cleanup
    content = remove_trailing_commas(content)

    result = try_load(content)
    if not isinstance(result, json.JSONDecodeError):
        return json.dumps(result, indent=2, ensure_ascii=False)

    # Iteratively attempt fixes by appending missing closing brackets/braces
    for attempt in range(1, 11):
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_brackets = content.count('[')
        close_brackets = content.count(']')

        need_braces = open_braces - close_braces
        need_brackets = open_brackets - close_brackets

        # If there are more closing than opening, remove extra trailing closers if present
        if close_braces > open_braces:
            # try removing from the end
            while close_braces > open_braces and content.rstrip().endswith('}'):
                content = content.rstrip()[:-1]
                close_braces -= 1
        if close_brackets > open_brackets:
            while close_brackets > open_brackets and content.rstrip().endswith(']'):
                content = content.rstrip()[:-1]
                close_brackets -= 1

        # Recalculate needs
        need_braces = open_braces - close_braces
        need_brackets = open_brackets - close_brackets

        # Append missing closers in a reasonable order: close arrays first, then objects
        to_append = ''
        if need_brackets > 0:
            to_append += ']' * need_brackets
        if need_braces > 0:
            to_append += '}' * need_braces

        if to_append:
            # ensure we add newline before closers
            if not content.endswith('\n'):
                content += '\n'
            content += to_append + '\n'

        # Remove any trailing commas again
        content = remove_trailing_commas(content)

        result = try_load(content)
        if not isinstance(result, json.JSONDecodeError):
            return json.dumps(result, indent=2, ensure_ascii=False)

    return None


def main():
    if not INPUT.exists():
        print(f"Input file not found: {INPUT}")
        return 2

    content = INPUT.read_text(encoding='utf-8')
    fixed = balance_and_fix(content)
    if fixed:
        OUTPUT.write_text(fixed, encoding='utf-8')
        print(f"Fixed JSON written to: {OUTPUT}")
        return 0
    else:
        print("Automated balancing failed; manual edit required.")
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
