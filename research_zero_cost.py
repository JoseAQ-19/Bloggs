import requests
import json
import os

BRAVE_KEY = "BSAS35Nt2mMl3dXFUikJ4u_WkcIZ59c"

def brave_search(query):
    print(f"🔍 Investigando: {query}...")
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_KEY}
    params = {"q": query, "count": 5}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get('web', {}).get('results', [])
            print(f"   ✅ {len(results)} resultados encontrados.")
            for r in results:
                print(f"      - {r['title']} ({r['url']})")
                print(f"        Desc: {r['description'][:100]}...")
        else:
            print(f"   ❌ Error: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")

if __name__ == "__main__":
    queries = [
        "SiliconFlow SiliconCloud API free tier limits pricing 2026 image generation FLUX",
        "Hugging Face Serverless Inference API free rate limits 2026 black-forest-labs/FLUX.1-schnell",
        "Nebius AI Studio free trial image generation pricing",
        "Cloudflare Workers AI image generation free tier limits 2026",
        "Best free AI image generator API for developers 2026 no watermark"
    ]
    for q in queries:
        brave_search(q)
