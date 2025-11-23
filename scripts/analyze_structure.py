#!/usr/bin/env python3
import json

def count_open_close(content):
    """Count opening and closing braces/brackets"""
    open_braces = content.count('{')
    close_braces = content.count('}')
    open_brackets = content.count('[')
    close_brackets = content.count(']')
    
    print(f"Braces: {open_braces} open, {close_braces} close (diff: {open_braces - close_braces})")
    print(f"Brackets: {open_brackets} open, {close_brackets} close (diff: {open_brackets - close_brackets})")
    
    # Show imbalance
    if open_braces != close_braces:
        print(f"  Need {abs(open_braces - close_braces)} more {'closing braces' if open_braces > close_braces else 'opening braces'}")
    
    if open_brackets != close_brackets:
        print(f"  Need {abs(open_brackets - close_brackets)} more {'closing brackets' if open_brackets > close_brackets else 'opening brackets'}")

def main():
    input_file = 'data/structured/deepseek_json_20251121_185f13.json'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Structural analysis:")
    count_open_close(content)
    
    # Try to load and catch error
    try:
        json.loads(content)
        print("\nJSON is valid!")
    except json.JSONDecodeError as e:
        print(f"\nJSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
        
        # Show the last few lines
        lines = content.split('\n')
        print("\nLast 10 lines of file:")
        for i in range(max(0, len(lines)-10), len(lines)):
            print(f"{i+1}: {lines[i]}")

if __name__ == '__main__':
    main()
