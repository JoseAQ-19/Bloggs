import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("STOCKS_WRITER_API_KEY")

print("Key starts with:", key[:5] if key else "NO KEY")

for base_url in ["https://api.z.ai/v1/models", "https://api.z.ai/v4/models", "https://api.z.ai/paas/v4/models"]:
    try:
        r = requests.get(base_url, headers={"Authorization": f"Bearer {key}"}, timeout=10)
        print(f"URL: {base_url} -> Status: {r.status_code}")
        if r.status_code == 200:
            print([m['id'] for m in r.json().get('data', [])])
    except Exception as e:
        print(e)
