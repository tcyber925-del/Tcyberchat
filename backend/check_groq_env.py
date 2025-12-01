from dotenv import load_dotenv
import os

load_dotenv()
print(f"GROQ_BASE_URL: '{os.getenv('GROQ_BASE_URL', 'NOT SET')}'")
