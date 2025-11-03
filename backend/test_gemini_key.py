import os
import google.generativeai as genai

# IMPORTANT: Replace 'YOUR_API_KEY_HERE' with your actual Gemini API key.
# Alternatively, ensure GEMINI_API_KEY is set as an environment variable.
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAzxyrTis09q3mHKEznBbzvWz_uAb6DWfo")

if API_KEY == "YOUR_API_KEY_HERE":
    print("ERROR: Please replace 'YOUR_API_KEY_HERE' with your actual Gemini API key or set the GEMINI_API_KEY environment variable.")
else:
    try:
        genai.configure(api_key=API_KEY)
        print("Attempting to list models...")
        found_models = False
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(f"- {m.name}")
                found_models = True
        if not found_models:
            print("No models supporting generateContent found with this API key.")
        else:
            print("\nYour API key appears to be valid and models are listed above.")
    except Exception as e:
        print(f"Error: {e}")
        print("Your API key might be invalid or there's a connection issue. Please double-check your key.")
