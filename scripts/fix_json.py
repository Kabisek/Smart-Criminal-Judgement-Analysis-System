#!/usr/bin/env python3
import json
import re
import sys

def repair_json(content):
    """Repair common JSON structural issues"""
    
    # Remove trailing commas before closing brackets/braces
    content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    # Remove any null bytes or control characters that might cause issues
    content = content.replace('\x00', '')
    
    # Try to parse as JSON
    try:
        data = json.loads(content)
        # Return properly formatted JSON
        return json.dumps(data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"Error: Line {e.lineno}, Column {e.colno}: {e.msg}")
        
        # Try more aggressive fixes
        print("Attempting aggressive repair...")
        
        # Count braces and brackets
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        
        print(f"Braces: {open_braces} open, {close_braces} close")
        print(f"Brackets: {open_brackets} open, {close_brackets} close")
        
        # Add missing closing braces/brackets
        while open_braces > close_braces:
            content += '\n}'
            close_braces += 1
            
        while open_brackets > close_brackets:
            content += '\n]'
            close_brackets += 1
        
        # Try parsing again
        try:
            data = json.loads(content)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e2:
            print(f"Still error: Line {e2.lineno}, Column {e2.colno}: {e2.msg}")
            return None

def main():
    input_file = 'data/structured/deepseek_json_20251121_185f13.json'
    output_file = 'data/structured/deepseek_json_20251121_185f13_fixed.json'
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Read {len(content)} characters from {input_file}")
        
        fixed_content = repair_json(content)
        
        if fixed_content:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Successfully fixed and saved to {output_file}")
        else:
            print("Could not repair JSON")
            return 1
            
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
