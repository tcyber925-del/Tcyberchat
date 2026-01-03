
import socket
import requests
import sys

def diagnose():
    target = "api.firecrawl.dev"
    print(f"--- Diagnosing connectivity to {target} ---")
    
    try:
        ip = socket.gethostbyname(target)
        print(f"✓ DNS Resolution: {target} -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
        
    print("\n--- Testing HTTP connection to Google (General Internet) ---")
    try:
        r = requests.get("https://www.google.com", timeout=5)
        print(f"✓ Google Reachable: Status {r.status_code}")
    except Exception as e:
        print(f"❌ Google Unreachable: {e}")

    print(f"\n--- Testing HTTPS connection to Firecrawl (Root) ---")
    try:
        # Note: Root might return 404 or 200 depending on API design
        r = requests.get(f"https://{target}", timeout=5)
        print(f"✓ Firecrawl Reachable: Status {r.status_code}")
    except Exception as e:
        print(f"❌ Firecrawl Unreachable: {e}")

if __name__ == "__main__":
    diagnose()
