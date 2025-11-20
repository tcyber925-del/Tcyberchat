#!/usr/bin/env python3
"""
Interactive script to help configure Tavily API
"""

import os
import sys


def main():
    print("=" * 60)
    print("TAVILY API SETUP WIZARD")
    print("=" * 60)
    print()

    # Check current status
    current_key = os.getenv("TAVILY_API_KEY")
    if current_key:
        print(f"✓ TAVILY_API_KEY is already set (length: {len(current_key)} chars)")
        print(f"  Key preview: {current_key[:10]}...{current_key[-4:]}")
        response = input("\nDo you want to update it? (y/n): ").strip().lower()
        if response != "y":
            print("Keeping existing key.")
            return
    else:
        print("⚠ TAVILY_API_KEY is not set")

    print("\nTo get your Tavily API key:")
    print("1. Visit https://tavily.com")
    print("2. Sign up or log in")
    print("3. Go to Dashboard → API Keys")
    print("4. Copy your API key (starts with 'tvly-')")
    print()

    api_key = input("Enter your Tavily API key: ").strip()

    if not api_key:
        print("✗ No API key provided. Exiting.")
        return

    if not api_key.startswith("tvly-"):
        print("⚠ Warning: Tavily API keys usually start with 'tvly-'")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != "y":
            return

    print("\nChoose how to set the API key:")
    print("1. Set for current session only (PowerShell/CMD)")
    print("2. Create .env file (recommended)")
    print("3. Show instructions for permanent setup")
    print("4. Cancel")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        print("\n" + "=" * 60)
        print("SET FOR CURRENT SESSION")
        print("=" * 60)
        print("\nRun one of these commands in your terminal:")
        print()
        print("PowerShell:")
        print(f'  $env:TAVILY_API_KEY="{api_key}"')
        print()
        print("Command Prompt (CMD):")
        print(f"  set TAVILY_API_KEY={api_key}")
        print()
        print("Linux/Mac:")
        print(f'  export TAVILY_API_KEY="{api_key}"')
        print()
        print("⚠ Note: This only works for the current terminal session.")
        print("   Restart your backend server after setting this.")

    elif choice == "2":
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_example = os.path.join(os.path.dirname(__file__), ".env.example")

        # Check if .env exists
        if os.path.exists(env_file):
            print(f"\n⚠ {env_file} already exists.")
            response = input("Do you want to update it? (y/n): ").strip().lower()
            if response != "y":
                return

            # Read existing content
            with open(env_file) as f:
                content = f.read()

            # Update or add TAVILY_API_KEY
            lines = content.split("\n")
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith("TAVILY_API_KEY="):
                    new_lines.append(f"TAVILY_API_KEY={api_key}")
                    updated = True
                else:
                    new_lines.append(line)

            if not updated:
                new_lines.append(f"TAVILY_API_KEY={api_key}")
                new_lines.append("WEB_SEARCH_PROVIDER=tavily")

            with open(env_file, "w") as f:
                f.write("\n".join(new_lines))
        else:
            # Create new .env file
            content = f"""# Web Search Configuration
TAVILY_API_KEY={api_key}
WEB_SEARCH_PROVIDER=tavily

# Optional: Cache configuration
WEB_SEARCH_CACHE_TTL=3600
WEB_SEARCH_RATE_LIMIT=10
WEB_SEARCH_ENABLE_CACHE=true
"""
            with open(env_file, "w") as f:
                f.write(content)

        print(f"\n✓ Created/updated {env_file}")
        print("⚠ Note: Make sure your backend loads .env files (python-dotenv)")
        print("   Restart your backend server after creating this file.")

    elif choice == "3":
        print("\n" + "=" * 60)
        print("PERMANENT SETUP INSTRUCTIONS")
        print("=" * 60)
        print("\nWindows (System Environment Variables):")
        print("1. Press Win + R, type 'sysdm.cpl', press Enter")
        print("2. Go to 'Advanced' tab → 'Environment Variables'")
        print("3. Under 'User variables', click 'New'")
        print("4. Variable name: TAVILY_API_KEY")
        print(f"5. Variable value: {api_key}")
        print("6. Click OK and restart your terminal/IDE")
        print()
        print("Linux/Mac (.bashrc or .zshrc):")
        print(f"  echo 'export TAVILY_API_KEY=\"{api_key}\"' >> ~/.bashrc")
        print("  source ~/.bashrc")

    else:
        print("Cancelled.")
        return

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Restart your backend server")
    print("2. Test configuration: python test_tavily_config.py")
    print("3. Test with RAG: python test_web_search_rag.py")
    print()
    print("For more details, see: backend/CONFIGURE_TAVILY.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
