import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content("Say OK")
    print(f"RESPONSE: {resp.text}")
except Exception as e:
    import traceback
    traceback.print_exc()
