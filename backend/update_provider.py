#!/usr/bin/env python
"""Update WEB_SEARCH_PROVIDER in .env file"""
import os
import sys

def update_env_provider(new_provider):
    """Update WEB_SEARCH_PROVIDER in .env file"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"ERROR: {env_path} not found")
        return False
    
    # Read current .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update or add WEB_SEARCH_PROVIDER
    updated = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('WEB_SEARCH_PROVIDER='):
            new_lines.append(f'WEB_SEARCH_PROVIDER={new_provider}\n')
            updated = True
            print(f"Updated: WEB_SEARCH_PROVIDER={new_provider}")
        else:
            new_lines.append(line)
    
    # If not found, add it
    if not updated:
        new_lines.append(f'\n# Web Search Provider\nWEB_SEARCH_PROVIDER={new_provider}\n')
        print(f"Added: WEB_SEARCH_PROVIDER={new_provider}")
    
    # Write back
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n✓ Successfully updated {env_path}")
    print(f"\nNext steps:")
    print(f"1. Restart your backend server (Ctrl+C, then restart)")
    print(f"2. Test Deep Research with a query")
    
    return True

if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "duckduckgo"
    
    valid_providers = ["tavily", "serpapi", "duckduckgo"]
    if provider not in valid_providers:
        print(f"ERROR: Invalid provider '{provider}'")
        print(f"Valid options: {', '.join(valid_providers)}")
        sys.exit(1)
    
    print(f"Updating WEB_SEARCH_PROVIDER to: {provider}")
    print("=" * 50)
    
    success = update_env_provider(provider)
    sys.exit(0 if success else 1)
