#!/usr/bin/env python3
"""
TREND SCOUT V4 — Pre-Searcher Agent (Omega Matrix Routing)
==========================================================
Fase 1 del Relay-Race: Busca tendencias reales usando HackerNews + Google News RSS
+ Exa + Gemini Grounding y guarda los 3 mejores temas en un JSON por categoría.

Enrutamiento LLM (Waterfall):
  1. OpenRouter (Llama 3.3 70B) — Cuota Gratuita / Rápida
  2. HuggingFace Serverless (Qwen2.5-7B) — Cuota de Emergencia
  3. Gemini 2.0 Flash —Grounding & Fallback Final
"""

import os
import sys
import json
import re
import random
import argparse
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Importación segura de SDKs externas
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Error: google-genai no instalado. Ejecuta: pip install google-genai")
    sys.exit(1)

try:
    from exa_py import Exa
except ImportError:
    Exa = None

load_dotenv()

# --- Configuración de APIs ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
EXA_KEY = os.getenv("EXA_API_KEY")
OPENROUTER_SCOUT_KEY = os.getenv("OPENROUTER_SCOUT_KEY")
HF_SCOUT_KEY = os.getenv("HF_SCOUT_API_KEY")

# Inicialización de clientes
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
exa = Exa(EXA_KEY) if EXA_KEY and Exa else None


# ============================================================
# OMEGA MATRIX: Waterfall LLM Router
# ============================================================

def _llm_generate(prompt: str, force_json: bool = False) -> Optional[str]:
    """
    Enrutamiento en cascada para optimizar costes y disponibilidad.
    """
    
    # ── [1] OPENROUTER (Llama 3.3 70B) ──
    if OPENROUTER_SCOUT_KEY:
        print("   🧠 [Omega] Intento 1: OpenRouter (Llama 3.3 70B)...")
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_SCOUT_KEY}",
                "Content-Type": "application/json",
                "X-Title": "TrendScout"
            }
            payload = {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            if force_json: payload["response_format"] = {"type": "json_object"}

            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                if len(text) > 20: return text
        except Exception as e:
            print(f"      ⚠️ OpenRouter falló: {e}")

    # ── [2] HUGGINGFACE SERVERLESS (Qwen 2.5) ──
    if HF_SCOUT_KEY:
        print("   🧠 [Omega] Intento 2: HF Serverless (Qwen 2.5 7B)...")
        try:
            hf_url = "https://router.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct/v1/chat/completions"
            headers = {"Authorization": f"Bearer {HF_SCOUT_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
            }
            resp = requests.post(hf_url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                return text
            elif resp.status_code == 503:
                print("      ⚠️ HF Modelo en 'Cold Start'. Saltando a Gemini...")
        except Exception as e:
            print(f"      ⚠️ HF falló: {e}")

    # ── [3] GEMINI 2.0 FLASH (Fallback Final) ──
    if client:
        print("   🚨 [Omega] Intento 3: Gemini 2.0 Flash (Emergencia)...")
        try:
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            if resp.text: return resp.text.strip()
        except Exception as e:
            print(f"      ❌ Gemini falló: {e}")

    return None

# ============================================================
# FUENTES DE DATOS (Scrapers)
# ============================================================

def fetch_hackernews(tags: List[str], limit: int = 5) -> List[Dict]:
    if not tags: return []
    headlines = []
    try:
        t_72h_ago = int(time.time()) - (72 * 3600)
        tag_query = " OR ".join(tags)
        url = f"https://hn.algolia.com/api/v1/search?query={tag_query}&tags=story&numericFilters=created_at_i>{t_72h_ago}&hitsPerPage={limit}"
        resp = requests.get(url, timeout=10)
        for hit in resp.json().get("hits", []):
            headlines.append({
                "title": hit.get("title", ""), "source": "hackernews", "lang": "en", "score": hit.get("points", 0), "url": hit.get("url", "")
            })
    except Exception as e: print(f"   ⚠️ [HN] Error: {e}")
    return headlines

def fetch_google_news(query: str, lang: str = "es", limit: int = 5) -> List[Dict]:
    headlines = []
    try:
        safe_kw = requests.utils.quote(f"{query} when:24h")
        rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl={'es-ES' if lang=='es' else 'en-US'}"
        resp = requests.get(rss_url, timeout=10)
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:limit]:
            title = item.find("title").text.split(" - ")[0].strip()
            headlines.append({"title": title, "source": "google_news", "lang": lang, "score": 0, "url": ""})
    except Exception as e: print(f"   ⚠️ [GNews] Error: {e}")
    return headlines

def fetch_exa_news(query: str, domains: List[str], limit: int = 5) -> List[Dict]:
    if not exa or not domains: return []
    headlines = []
    try:
        start_date = (datetime.now() - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        res = exa.search(query, num_results=limit, type="neural", include_domains=domains, start_published_date=start_date)
        for r in res.results:
            is_es = any(d in (r.url or "") for d in [".es", "as.com", "3djuegos"])
            headlines.append({"title": r.title, "source": "exa", "lang": "es" if is_es else "en", "score": 0, "url": r.url or ""})
    except Exception as e: print(f"   ⚠️ [Exa] Error: {e}")
    return headlines

# ============================================================
# SELECTOR Y PIPELINE
# ============================================================

def select_best_topics(all_headlines: List[Dict], category: str, lang: str = "es") -> List[Dict]:
    if not all_headlines: return []
    
    context = "\n".join([f"- [{h['source']}] {h['title']}" for h in all_headlines])
    prompt = f"""ACT AS: Senior Editorial Director. Category: {category}. Language: {lang.upper()}.
HEADLINES:
{context}

TASK: Select the TOP 3 most viral/important topics. Rewrite them as catchy blog titles.
NEGATIVE CONSTRAINTS: DO NOT use "En conclusión", "TL;DR", "Magia", "Descubre como". NO corporate fluff.

OUTPUT FORMAT (3 lines only):
[{lang.upper()}] rewritten title 1
[{lang.upper()}] rewritten title 2
[{lang.upper()}] rewritten title 3"""

    resp = _llm_generate(prompt)
    selected = []
    if resp:
        for line in resp.strip().split('\n')[:3]:
            clean = re.sub(r'^\[.*?\]', '', line).strip().strip('"')
            selected.append({"title": clean, "lang": lang, "source": "llm_selected"})
    return selected or all_headlines[:3]

def scout(category: str, target_lang: str = "es"):
    print(f"\n🔭 SCOUTING: {category.upper()} [{target_lang.upper()}]")
    
    # Aquí iría la lógica de recolección (simplificada para el ejemplo)
    all_headlines = fetch_google_news(category, lang=target_lang)
    best = select_best_topics(all_headlines, category, lang=target_lang)
    
    output = {
        "category": category, "lang": target_lang, "scouted_at": datetime.now(timezone.utc).isoformat(),
        "topics": [{"rank": i+1, "title": t["title"], "lang": target_lang} for i, t in enumerate(best)]
    }
    
    os.makedirs("data", exist_ok=True)
    out_path = f"data/trends_{category}_{target_lang}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ Guardado en: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True)
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default='es')
    args = parser.parse_args()
    scout(args.category, args.lang)
