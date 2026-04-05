#!/usr/bin/env python3
"""
STOCKS_SCOUT.PY — Buscador de Tendencias para Fondos de Inversión
==================================================================
Scout especializado en fondos de inversión, ETFs y stocks.
Busca consejos de expertos vía RSS, Google News y APIs financieras,
y combina los resultados con el análisis de competidores.

REGLA DE ORO: Este archivo NO importa ni modifica NADA del núcleo existente.
"""

import os
import re
import sys
import json
import random
import time
import logging
import argparse
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from api_cache import cached_api_call
from llm_router import LLMRouter

# Configurar stdout/stderr para UTF-8 en Windows y evitar errores de "charmap"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

load_dotenv()

# --- API Keys (aisladas del núcleo) ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENROUTER_SCOUT_KEY = os.getenv("OPENROUTER_SCOUT_KEY")
HF_SCOUT_KEY = os.getenv("HF_SCOUT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Gemini SDK
try:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
except Exception:
    gemini_client = None

# Imports locales del módulo stocks (aislados)
from stocks_instructions import STOCKS_CATEGORY_CONFIG, COMPETITORS, PROMPTS
from stocks_researcher import get_cached_analysis, analyze_all_competitors


# ============================================================
# LLM WATERFALL (Copia aislada — NO reutiliza _llm_generate del núcleo)
# ============================================================

def _stocks_llm_generate_v3_core(prompt, system_prompt):
    """
    Original Stocks Waterfall (Tier 1-4).
    """
    # ── [1] OPENROUTER ──
    if OPENROUTER_SCOUT_KEY:
        max_retries = 3
        backoff_seconds = [10, 25, 60]
        for attempt in range(max_retries):
            try:
                print("   [Stocks Scout] TIER 1: OpenRouter...")
                headers = {"Authorization": f"Bearer {OPENROUTER_SCOUT_KEY}", "Content-Type": "application/json"}
                payload = {"model": "meta-llama/llama-4-scout:free", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2048}
                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    if len(text) > 20: return text
            except Exception as e:
                logging.warning(f"[Stocks Scout] TIER 1 OpenRouter attempt {attempt+1} failed: {type(e).__name__}: {str(e)[:150]}")

    # ── [2] HF Serverless ──
    if HF_SCOUT_KEY:
        try:
            print("   [Stocks Scout] TIER 2: HF Serverless...")
            resp = requests.post("https://router.huggingface.co/models/Qwen/Qwen3-32B/v1/chat/completions", headers={"Authorization": f"Bearer {HF_SCOUT_KEY}", "Content-Type": "application/json"}, json={"model": "Qwen/Qwen3-32B", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2048}, timeout=120)
            if resp.status_code == 200: return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logging.warning(f"[Stocks Scout] TIER 2 HF Serverless (Qwen3-32B) failed: {type(e).__name__}: {str(e)[:150]}")

    # ── [3] GROQ ──
    if GROQ_API_KEY:
        try:
            print(f"   🚀 [Stocks Scout] TIER 3: Groq...")
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2048}, timeout=90)
            if resp.status_code == 200: return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logging.warning(f"[Stocks Scout] TIER 3 Groq (Llama-3.3-70B) failed: {type(e).__name__}: {str(e)[:150]}")

    # ── [4] GEMINI ──
    if gemini_client:
        try:
            print("   [Stocks Scout] TIER 4: Gemini 2.0 Flash...")
            resp = gemini_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            return resp.text.strip()
        except Exception as e:
            logging.warning(f"[Stocks Scout] TIER 4 Gemini Flash failed: {type(e).__name__}: {str(e)[:150]}")
    return None


def _stocks_llm_generate(prompt, force_json=False):
    """
    Enrutador con Capa Cero para Stocks.
    """
    return LLMRouter.route_call(
        prompt, 
        "You are an expert financial analyst selecting investment trends.", 
        _stocks_llm_generate_v3_core, 
        model_type="parsing"
    )

# ============================================================
# FUENTE 1: Google News RSS — Noticias Financieras
# ============================================================

@cached_api_call(ttl_hours=12)
def fetch_financial_news(lang="es", limit=8):
    """Busca noticias financieras recientes vía Google News RSS."""
    config = STOCKS_CATEGORY_CONFIG["funds"]
    queries = config["news_queries"].get(lang, [])
    headlines = []

    for query in queries:
        try:
            actual_query = f"{query} when:3d"
            safe_kw = requests.utils.quote(actual_query)
            if lang == "es":
                rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=es-ES&gl=ES&ceid=ES:es"
            else:
                rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en-US&gl=US&ceid=US:en"

            resp = requests.get(rss_url, timeout=10)
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:limit]

            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                if title_el is not None and title_el.text:
                    clean = title_el.text.split(" - ")[0].strip()
                    if len(clean.split()) >= 4:
                        headlines.append({
                            "title": clean,
                            "source": "google_news_finance",
                            "lang": lang,
                            "url": link_el.text if link_el is not None else "",
                            "score": 0
                        })

            print(f"   📰 [Finance News/{lang.upper()}] {len(headlines)} titulares: '{query[:40]}...'")
        except Exception as e:
            print(f"   [Finance News] Error: {e}")

    return headlines


# ============================================================
# FUENTE 2: RSS de Competidores Financieros
# ============================================================

@cached_api_call(ttl_hours=12)
def fetch_competitor_rss(lang="es", limit=5):
    """Busca artículos recientes de los RSS de competidores (Morningstar, etc.)."""
    competitors = COMPETITORS.get(lang, {})
    headlines = []

    for comp_id, comp_info in competitors.items():
        rss_url = comp_info.get("rss")
        if not rss_url:
            continue

        try:
            resp = requests.get(rss_url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; NovumBot/1.0)"
            }, timeout=10)

            if resp.status_code != 200:
                print(f"   [RSS] [{comp_info['name']}] HTTP {resp.status_code}")
                continue

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:limit]

            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                if title_el is not None and title_el.text:
                    clean = title_el.text.strip()
                    if len(clean.split()) >= 3:
                        headlines.append({
                            "title": clean,
                            "source": f"rss_{comp_id}",
                            "lang": lang,
                            "url": link_el.text if link_el is not None else "",
                            "score": 0
                        })

            print(f"   📡 [{comp_info['name']}] {len(items)} artículos RSS")
        except Exception as e:
            print(f"   [RSS] [{comp_info['name']}] Error: {e}")

    return headlines


# ============================================================
# FUENTE 3: Gemini Grounding — Tendencias Financieras en Tiempo Real
# ============================================================

def fetch_financial_grounding(lang="es"):
    """Usa Gemini con Google Search grounding para detectar tendencias financieras."""
    if not gemini_client:
        return []

    headlines = []
    try:
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        current_date = datetime.now().strftime("%B %Y")

        if lang == "es":
            prompt = f"""Search for the MOST IMPORTANT mutual fund, ETF, and investment fund news happening RIGHT NOW in Spain and Europe ({current_date}).

Focus on: fund performance rankings, Morningstar rating changes, new fund launches, fee reductions, 
regulatory changes (CNMV, MiFID), roboadvisor performance updates (Indexa Capital, MyInvestor).

OUTPUT: List 6 specific, data-rich headlines in this format:
[ES] headline in Spanish
[ES] headline in Spanish
[ES] headline in Spanish
[ES] headline in Spanish
[ES] headline in Spanish
[ES] headline in Spanish

RULES: Each headline MUST contain a specific fund name, percentage, or financial data point. No generic headlines."""
        else:
            prompt = f"""Search for the MOST IMPORTANT mutual fund, ETF, and index fund news happening RIGHT NOW in the US and globally ({current_date}).

Focus on: Vanguard/Fidelity/BlackRock fund performance, Morningstar rating changes, new ETF launches, 
expense ratio cuts, SEC regulatory changes, fund flow data, market outlook reports.

OUTPUT: List 6 specific, data-rich headlines in this format:
[EN] headline in English
[EN] headline in English
[EN] headline in English
[EN] headline in English
[EN] headline in English
[EN] headline in English

RULES: Each headline MUST contain a specific fund name, ticker, percentage, or financial data point. No generic headlines."""

        resp = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(tools=[google_search_tool])
        )

        if resp.text:
            for line in resp.text.strip().split('\n'):
                line = line.strip()
                tag = f"[{lang.upper()}]"
                if line.startswith(tag):
                    clean = line[len(tag):].strip().lstrip('- ').strip()
                    if len(clean.split()) >= 4:
                        headlines.append({
                            "title": clean,
                            "source": "gemini_grounding_finance",
                            "lang": lang,
                            "url": "",
                            "score": 0
                        })

            print(f"   🌐 [Grounding Finance/{lang.upper()}] {len(headlines)} titulares en tiempo real")
    except Exception as e:
        print(f"   [Grounding Finance] Error: {e}")

    return headlines


# ============================================================
# SELECTOR LLM: Elige los 3 mejores temas financieros
# ============================================================

def select_best_financial_topics(all_headlines, lang="es", count=3):
    """LLM selector especializado en finanzas."""
    if not all_headlines:
        return []

    headlines_text = ""
    for i, h in enumerate(all_headlines):
        headlines_text += f"{i+1}. [{h['source']}] {h['title']}\n"

    selector_prompt = f"""ACT AS: Senior Financial Editorial Director for {'Morningstar España' if lang == 'es' else 'Morningstar.com'}.

You have these candidate financial headlines:

{headlines_text}

SELECTION CRITERIA (for investment fund content):
- Pick topics with SPECIFIC FUND NAMES, PERFORMANCE DATA, or FEE COMPARISONS
- Prefer topics that compare multiple funds or highlight surprising performance
- REJECT generic "how to invest" or "what is an ETF" topics
- REJECT old news or evergreen content
- Prefer topics with contrarian angles or unexpected data
- Prefer topics relevant to {'Spanish/European investors' if lang == 'es' else 'US/Global investors'}

TASK: Select the TOP {count} topics. For each, rewrite it as a compelling blog title 
with a specific data point that promises unique insight.

OUTPUT FORMAT (exactly {count} lines, no numbering, no quotes):
[{lang.upper()}] Rewritten title
[{lang.upper()}] Rewritten title
[{lang.upper()}] Rewritten title

OUTPUT ONLY THESE {count} LINES. Nothing else."""

    resp_text = _stocks_llm_generate(selector_prompt)
    if resp_text:
        selected = []
        tag = f"[{lang.upper()}]"
        for line in resp_text.strip().split('\n'):
            line = line.strip()
            if line.startswith(tag):
                title = line[len(tag):].strip().lstrip('- ').strip()
                if title and len(title.split()) >= 4:
                    selected.append({
                        "title": title,
                        "lang": lang,
                        "source": "llm_selected_finance"
                    })

        if selected:
            print(f"   [Finance Selector] {len(selected)} temas seleccionados")
            return selected[:count]

    # Fallback
    return all_headlines[:count]


# ============================================================
# PIPELINE PRINCIPAL: Scout Financiero Completo
# ============================================================

def scout_funds(lang="es"):
    """
    Pipeline completo del scout financiero para un idioma.
    
    Returns:
        dict con el contenido base, análisis de competidores y frases clave.
    """
    print(f"\n{'=' * 60}")
    print(f"STOCKS SCOUT — Fondos de Inversion | Idioma: {lang.upper()}")
    print(f"{'=' * 60}\n")

    all_headlines = []

    # === FUENTE 1: Google News RSS Finance ===
    news_headlines = fetch_financial_news(lang=lang, limit=8)
    all_headlines.extend(news_headlines)

    # === FUENTE 2: RSS de Competidores ===
    rss_headlines = fetch_competitor_rss(lang=lang, limit=5)
    all_headlines.extend(rss_headlines)

    # === FUENTE 3: Gemini Grounding Finance ===
    grounding_headlines = fetch_financial_grounding(lang=lang)
    all_headlines.extend(grounding_headlines)

    print(f"\n   TOTAL: {len(all_headlines)} titulares financieros recopilados [{lang.upper()}]")

    # === SELECCIÓN LLM ===
    best_topics = select_best_financial_topics(all_headlines, lang=lang, count=3)

    # === ANÁLISIS DE COMPETIDORES (cached) ===
    competitor_analysis = get_cached_analysis()
    if not competitor_analysis:
        print("   Ejecutando análisis de competidores fresco...")
        competitor_analysis = analyze_all_competitors()

    # Extraer frases clave del mercado relevante
    market_data = competitor_analysis.get("markets", {}).get(lang, {})
    key_phrases = {}
    for comp_id, comp_data in market_data.get("competitors", {}).items():
        phrases = comp_data.get("common_phrases", {})
        key_phrases.update(phrases)

    # === CONSTRUIR OUTPUT DEL SCOUT ===
    scout_output = {
        "category": "funds",
        "lang": lang,
        "scouted_at": datetime.now(timezone.utc).isoformat(),
        "total_candidates": len(all_headlines),
        "topics": [
            {
                "rank": i + 1,
                "title": t["title"],
                "lang": t.get("lang", lang),
                "source": t.get("source", "unknown")
            }
            for i, t in enumerate(best_topics)
        ],
        "competitor_analysis": {
            "key_phrases": dict(list(key_phrases.items())[:15]),
            "competitors_with_disclaimers": sum(
                1 for c in market_data.get("competitors", {}).values()
                if c.get("has_disclaimer", False)
            ),
            "sample_styles": {
                comp_id: comp_data.get("declared_style", "")
                for comp_id, comp_data in market_data.get("competitors", {}).items()
            }
        },
        "all_headlines": [
            {"title": h["title"], "source": h["source"], "url": h.get("url", "")}
            for h in all_headlines[:20]
        ]
    }

    # === GUARDAR JSON ===
    os.makedirs("data", exist_ok=True)
    output_path = f"data/trends_funds_{lang}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scout_output, f, ensure_ascii=False, indent=2)

    print(f"\n   Guardado: {output_path}")
    print(f"   📋 Temas seleccionados:")
    for t in scout_output["topics"]:
        print(f"      #{t['rank']} [{t['lang'].upper()}] {t['title']}")

    return scout_output


# ============================================================
# MAIN (ejecución independiente)
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stocks Scout — Fund Trend Finder")
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default='es',
                        help='Target language: es (Spain) or en (US/Global)')
    args = parser.parse_args()

    scout_funds(lang=args.lang)
