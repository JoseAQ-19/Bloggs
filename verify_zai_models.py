import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("STOCKS_WRITER_API_KEY")

if not key:
    print("❌ STOCKS_WRITER_API_KEY no encontrada en .env")
    exit(1)

# Endpoint OpenAI compatible
url = "https://open.bigmodel.cn/api/paas/v4/models"
headers = {
    "Authorization": f"Bearer {key}"
}

print("Buscando modelos en Zhipu API...")
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        models = [m['id'] for m in data.get('data', [])]
        print("✅ Modelos disponibles:")
        for m in models:
            print(f"  - {m}")
    else:
        print(f"❌ Error: {resp.text}")
except Exception as e:
    print(f"❌ Excepción: {e}")

# Also test endpoints with a simple chat request to standard names just in case the models endpoint is blocked
test_models = ["glm-4-flash", "glm-4", "glm-4-air", "glm-4-plus"]

print("\nProbando inferencia directamente...")
for m in test_models:
    print(f"Probando {m}...")
    try:
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": m,
                "messages": [{"role": "user", "content": "Hola"}],
                "max_tokens": 10
            },
            timeout=10
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  ✅ Funciona: {resp.json()['choices'][0]['message']['content']}")
        else:
            print(f"  ❌ Falló: {resp.json().get('error', resp.text)}")
    except Exception as e:
         print(f"  ❌ Excepción: {e}")
