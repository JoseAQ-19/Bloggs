import os
import requests
from dotenv import load_dotenv

load_dotenv()
nvidia_key = os.getenv("NVIDIA_API_KEY")
print("Key length:", len(nvidia_key) if nvidia_key else 0)

headers = {
    "Authorization": f"Bearer {nvidia_key}",
    "Accept": "application/json",
}

payload = {
    "prompt": "Test image of a cat",
    "negative_prompt": "",
    "cfg_scale": 5.0,
    "aspect_ratio": "16:9",
    "steps": 10,
    "seed": 42
}

try:
    resp = requests.post(
        "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium",
        headers=headers,
        json=payload,
        timeout=30
    )
    print("Status:", resp.status_code)
    try:
        print("Response:", resp.json())
    except:
        print("Text:", resp.text[:200])
except Exception as e:
    print("Exception:", e)
