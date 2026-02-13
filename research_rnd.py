import requests
import json
import os

BRAVE_KEY = "BSAS35Nt2mMl3dXFUikJ4u_WkcIZ59c"

def brave_search(query):
    print(f"🔍 Investigando: {query}...")
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_KEY}
    params = {"q": query, "count": 4}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get('web', {}).get('results', [])
            print(f"   ✅ Resultados para '{query}':")
            for r in results:
                print(f"      - {r['title']} ({r['url']})")
                print(f"        Desc: {r['description'][:150]}...")
        else:
            print(f"   ❌ Error: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")

if __name__ == "__main__":
    queries = [
        "yt-dlp youtube subtitle extraction issues 2025 2026",
        "best API to scrape documentation for LLM Exa.ai vs Firecrawl vs Tavily pricing free tier",
        "how to automate SaaS tutorials from documentation using AI",
        "technical writing frameworks for software documentation 2025"
    ]
    for q in queries:
        brave_search(q)
