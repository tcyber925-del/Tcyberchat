#!/usr/bin/env python
"""Fix GROQ_BASE_URL in .env file"""
import os
import sys

def fix_groq_base_url():
    """Fix GROQ_BASE_URL in .env file"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"ERROR: {env_path} not found")
        return False
    
    # Read current .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update GROQ_BASE_URL
    updated = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('GROQ_BASE_URL='):
            # Fix the URL
            new_lines.append('GROQ_BASE_URL=https://api.groq.com/openai/v1\n')
            updated = True
            print("Fixed: GROQ_BASE_URL=https://api.groq.com/openai/v1")
        else:
            new_lines.append(line)
    
    if not updated:
        print("GROQ_BASE_URL not found in .env, nothing to fix.")
        return True
    
    # Write back
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n[OK] Successfully updated {env_path}")
    return True

if __name__ == "__main__":
    success = fix_groq_base_url()
    sys.exit(0 if success else 1)
