import sys
import signal

def timeout_handler(signum, frame):
    print("Import timed out!")
    sys.exit(1)

# This won't work on Windows, but let's try importing directly
try:
    from main import app
    print("✓ main.app imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
