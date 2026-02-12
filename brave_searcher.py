import requests
import json
import os

# Tu API Key
BRAVE_KEY = "BSAS35Nt2mMl3dXFUikJ4u_WkcIZ59c"

def brave_search(query):
    print(f"🔍 Buscando en Brave: {query}...")
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_KEY
    }
    params = {"q": query, "count": 5}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('web', {}).get('results', [])
            
            print(f"\n--- RESULTADOS PARA: {query} ---")
            for i, r in enumerate(results):
                print(f"[{i+1}] {r['title']}")
                print(f"    URL: {r['url']}")
                print(f"    DESC: {r['description'][:150]}...")
                print("-" * 40)
        else:
            print(f"❌ Error Brave: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Excepción: {e}")

if __name__ == "__main__":
    # Búsqueda estratégica sobre APIs de imagen gratuitas 2026
    brave_search("best free FLUX.1 image generation API python 2025 2026 without watermark")
    brave_search("SiliconFlow API free tier limits pricing image generation")
    brave_search("Hugging Face Inference API FLUX.1 free limits")
