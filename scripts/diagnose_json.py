#!/usr/bin/env python3
import json
import re

def diagnose_json(content):
    """Diagnose JSON issues and attempt detailed repair"""
    
    # First, let's find the exact location of the error
    try:
        json.loads(content)
        print("JSON is valid!")
        return content
    except json.JSONDecodeError as e:
        print(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
        
        # Get the lines around the error
        lines = content.split('\n')
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        
        print("\nContext around error:")
        for i in range(start, end):
            marker = ">>> " if i == e.lineno - 1 else "    "
            print(f"{marker}{i+1}: {lines[i][:100]}")
        
        # Common fixes
        print("\nAttempting fixes...")
        
        # Fix 1: Remove trailing commas before } or ]
        fixed = re.sub(r',(\s*[}\]])', r'\1', content)
        
        try:
            json.loads(fixed)
            print("Fix 1 worked: removed trailing commas")
            return fixed
        except json.JSONDecodeError as e2:
            print(f"Fix 1 didn't work: {e2.msg} at line {e2.lineno}")
        
        # Fix 2: Add missing colons after keys
        # This is more complex and might need manual intervention
        
        return None

def main():
    input_file = 'data/structured/deepseek_json_20251121_185f13.json'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} bytes")
    print(f"Total lines: {len(content.split(chr(10)))}")
    
    fixed = diagnose_json(content)
    
    if fixed and fixed != content:
        output_file = input_file.replace('.json', '_fixed.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed)
        print(f"\nFixed JSON saved to {output_file}")

if __name__ == '__main__':
    main()
