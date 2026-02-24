#!/usr/bin/env python3
"""
TREND SCOUT V4 — Pre-Searcher Agent (Omega Matrix Routing)
Fase 1 del Relay-Race: Busca tendencias reales usando HackerNews + Google News RSS
+ Exa + Gemini Grounding y guarda los 3 mejores temas en un JSON por categoría.

Enrutamiento LLM (Waterfall):
  1. OpenRouter (Llama 3.3 70B) — OPENROUTER_SCOUT_KEY
  2. HuggingFace Serverless (Qwen2.5-7B) — HF_SCOUT_API_KEY
  3. Gemini 2.0 Flash (Emergencia) — GEMINI_API_KEY

Uso: python trend_scout.py --category ia
Salida: data/trends_ia.json
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
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
EXA_KEY = os.getenv("EXA_API_KEY")
OPENROUTER_SCOUT_KEY = os.getenv("OPENROUTER_SCOUT_KEY")
HF_SCOUT_KEY = os.getenv("HF_SCOUT_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

try:
    from exa_py import Exa
    exa = Exa(EXA_KEY) if EXA_KEY else None
except ImportError:
    exa = None


# ============================================================
# OMEGA MATRIX: Waterfall LLM Router (Scout-Dedicated Keys)
# OpenRouter → HuggingFace Serverless → Gemini Emergency
# ============================================================

def _llm_generate(prompt, force_json=False):
    """
    Enrutamiento cascada para el Scout.
    Intento 1: OpenRouter (Llama 3.3 70B) — rápido, sin cold starts.
    Intento 2: HF Serverless (Qwen2.5-7B) — segunda cuota aislada.
    Intento 3: Gemini 2.0 Flash — paracaídas final.
    
    Si force_json=True, aplica limpieza regex agresiva para extraer JSON.
    """
    result = None

    # ── INTENTO 1: OpenRouter (Llama 3.3 70B) ──
    if OPENROUTER_SCOUT_KEY:
        print("   🧠 [Omega] Intento 1: OpenRouter / Llama-3.3-70B...")
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_SCOUT_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://novum.blog",
                "X-Title": "TrendScout"
            }
            payload = {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2048
            }
            if force_json:
                payload["response_format"] = {"type": "json_object"}

            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                if text and len(text) > 20:
                    print("   ✅ OpenRouter respondió correctamente.")
                    return text
                else:
                    print("   ⚠️ OpenRouter respuesta vacía. Saltando...")
            elif resp.status_code == 429:
                print(f"   ⚠️ OpenRouter rate-limit (429). Saltando...")
            else:
                print(f"   ⚠️ OpenRouter HTTP {resp.status_code}: {resp.text[:150]}")
        except requests.exceptions.Timeout:
            print("   ⚠️ OpenRouter timeout (60s). Cortocircuito → HF...")
        except Exception as e:
            print(f"   ⚠️ OpenRouter error: {e}")
    else:
        print("   ⚠️ OPENROUTER_SCOUT_KEY no configurada. Saltando...")

    # ── INTENTO 2: HuggingFace Serverless (Qwen2.5-7B-Instruct) ──
    if HF_SCOUT_KEY:
        print("   🤗 [Omega] Intento 2: HF Serverless / Qwen2.5-7B...")
        try:
            hf_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct/v1/chat/completions"
            hf_headers = {
                "Authorization": f"Bearer {HF_SCOUT_KEY}",
                "Content-Type": "application/json"
            }
            hf_payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2048,
                "stream": False
            }
            resp = requests.post(hf_url, headers=hf_headers, json=hf_payload, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                if text and len(text) > 20:
                    # Limpieza preventiva: extraer JSON si viene envuelto en markdown
                    if force_json:
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            text = json_match.group(0)
                    print("   ✅ HF/Qwen respondió correctamente.")
                    return text
                else:
                    print("   ⚠️ HF respuesta vacía. Saltando...")
            elif resp.status_code == 503:
                # Cold Start — cortocircuito inmediato, NO esperamos
                est = resp.json().get("estimated_time", 999)
                print(f"   ⚠️ HF modelo dormido (503). Tiempo estimado: {est:.0f}s. Cortocircuito → Gemini...")
            elif resp.status_code == 429:
                print("   ⚠️ HF rate-limit (429). Saltando...")
            else:
                print(f"   ⚠️ HF HTTP {resp.status_code}: {resp.text[:150]}")
        except requests.exceptions.Timeout:
            print("   ⚠️ HF timeout (120s). Cortocircuito → Gemini...")
        except Exception as e:
            print(f"   ⚠️ HF error: {e}")
    else:
        print("   ⚠️ HF_SCOUT_API_KEY no configurada. Saltando...")

    # ── INTENTO 3: Gemini 2.0 Flash (Paracaídas) ──
    if client:
        print("   🚨 [Omega] Intento 3 (Emergencia): Gemini 2.0 Flash...")
        try:
            config_kwargs = {}
            if force_json:
                config_kwargs["response_mime_type"] = "application/json"
            resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
            )
            if resp.text and len(resp.text.strip()) > 20:
                print("   ✅ Gemini respondió (emergencia).")
                return resp.text.strip()
        except Exception as e:
            print(f"   ❌ Gemini error: {e}")
    
    print("   ❌ [Omega] TODOS los motores fallaron.")
    return None

# ============================================================
# CONFIGURACIÓN POR CATEGORÍA
# ============================================================

CATEGORY_CONFIG = {
    "ia": {
        "type": "technical",
        "hn_tags": ["artificial-intelligence", "machine-learning", "llm", "chatgpt", "openai"],
        "news_queries": {
            "es": ["inteligencia artificial herramientas SaaS novedades", "ChatGPT Claude Gemini noticias España"],
            "en": ["AI tools SaaS LLM news this week", "GPT Claude Gemini enterprise adoption"]
        },
        "exa_domains": ["techcrunch.com", "arstechnica.com", "theverge.com", "venturebeat.com"],
        "seeds": ["Cursor AI", "Make.com", "n8n", "Claude 3.5", "ChatGPT Team", "Midjourney v6", "Zapier", "LangChain", "Hugging Face"]
    },
    "fitness": {
        "type": "technical",
        "hn_tags": [],
        "news_queries": {
            "es": ["ciencia ejercicio estudio pubmed hipertrofia", "biohacking longevidad España tendencia"],
            "en": ["exercise science study hypertrophy biohacking", "fitness trending research VO2max creatine"]
        },
        "exa_domains": ["pubmed.ncbi.nlm.nih.gov", "examine.com", "strongerbyscience.com", "menshealth.com"],
        "seeds": ["Zone 2 Cardio", "Creatine Monohydrate", "Hyrox training", "Sleep tracking", "Cold plunge", "Sauna protocols", "VO2 Max", "Protein intake", "Intermittent Fasting", "Hypertrophy"]
    },
    "crypto": {
        "type": "technical",
        "hn_tags": ["cryptocurrency", "bitcoin", "ethereum", "blockchain", "defi"],
        "news_queries": {
            "es": ["criptomonedas noticias hoy análisis on-chain", "Bitcoin Ethereum Solana España tendencia"],
            "en": ["cryptocurrency news on-chain analysis this week", "DeFi TVL whale movements SEC regulation"]
        },
        "exa_domains": ["coindesk.com", "theblock.co", "decrypt.co", "cointelegraph.com"],
        "seeds": ["Solana", "Base Chain", "Arbitrum", "Uniswap", "Metamask", "Staking ETH", "Memecoins", "Airdrops"]
    },
    "youtube": {
        "type": "news",
        "hn_tags": [],
        "news_queries": {
            "es": ["youtubers España polémica drama creadores", "tendencia viral TikTok España esta semana", "Ibai Auronplay TheGrefg noticias"],
            "en": ["YouTuber drama controversy this week", "MrBeast KSI Logan Paul news", "viral YouTube TikTok challenge trending"]
        },
        "exa_domains": ["dexerto.com", "dexerto.es", "tubefilter.com", "socialblade.com", "dotesports.com", "as.com", "3djuegos.com"],
        "seeds": []
    },
    "viral": {
        "type": "news",
        "hn_tags": [],
        "news_queries": {
            "es": ["tendencia viral España esta semana TikTok", "polémica redes sociales España", "meme viral España generación Z"],
            "en": ["viral trend this week TikTok Reddit", "Gen Z trend going viral internet culture", "social media controversy debate this week"]
        },
        "exa_domains": ["buzzfeed.com", "knowyourmeme.com", "mashable.com", "dailydot.com"],
        "seeds": []
    },
    "tools": {
        "type": "technical",
        "hn_tags": ["productivity", "automation", "saas", "developer-tools", "nocode"],
        "news_queries": {
            "es": ["herramientas automatización SaaS productividad España", "tutorial nocode IA Zapier Make.com"],
            "en": ["productivity SaaS automation tools this week", "nocode lowcode developer tools trend"]
        },
        "exa_domains": ["producthunt.com", "ycombinator.com", "news.ycombinator.com", "techcrunch.com", "indiehackers.com"],
        "seeds": ["Zapier", "Make.com", "n8n", "Cursor", "Notion", "Airtable", "Roo-Code", "Claude Desktop"]
    }
}


# ============================================================
# FUENTE 1: HackerNews API (100% gratis, sin auth)
# ============================================================

def fetch_hackernews(tags, limit=5):
    """Extrae top stories de HackerNews filtradas por tags."""
    headlines = []
    if not tags:
        return headlines
    
    try:
        import time
        t_72h_ago = int(time.time()) - (72 * 3600)
        # HN Algolia API — 100% público, sin auth
        tag_query = " OR ".join(tags)
        url = f"https://hn.algolia.com/api/v1/search?query={tag_query}&tags=story&numericFilters=created_at_i>{t_72h_ago}&hitsPerPage={limit}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            points = hit.get("points", 0)
            if title and len(title.split()) >= 4 and points >= 5:
                headlines.append({
                    "title": title,
                    "source": "hackernews",
                    "lang": "en",
                    "score": points,
                    "url": hit.get("url", "")
                })
        
        print(f"   📰 [HackerNews] {len(headlines)} titulares encontrados")
    except Exception as e:
        print(f"   ⚠️ [HackerNews] Error: {e}")
    
    return headlines


# ============================================================
# FUENTE 2: Google News RSS (Oficial, sin auth, sin rate limit)
# ============================================================

def fetch_google_news(query, lang="es", limit=5):
    """Extrae titulares reales de Google News RSS."""
    headlines = []
    try:
        actual_query = f"{query} when:24h"
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
            if title_el is not None and title_el.text:
                clean = title_el.text.split(" - ")[0].strip()
                if len(clean.split()) >= 4:
                    headlines.append({
                        "title": clean,
                        "source": "google_news",
                        "lang": lang,
                        "score": 0,
                        "url": ""
                    })
        
        print(f"   📰 [Google News/{lang.upper()}] {len(headlines)} titulares: '{query[:40]}...'")
    except Exception as e:
        print(f"   ⚠️ [Google News] Error: {e}")
    
    return headlines


# ============================================================
# FUENTE 3: Exa Neural Search (Sitios especializados)
# ============================================================

def fetch_exa_news(query, domains, limit=5):
    """Busca en sitios especializados via Exa neural search."""
    headlines = []
    if not exa or not domains:
        return headlines
    
    try:
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        res = exa.search(
            query,
            num_results=limit,
            type="neural",
            include_domains=domains,
            start_published_date=start_date
        )
        if res and res.results:
            for r in res.results:
                if r.title and len(r.title.split()) >= 4:
                    clean = r.title.split(" - ")[0].split(" | ")[0].strip()
                    is_es = any(d in (r.url or "") for d in [".es", "dexerto.es", "as.com", "3djuegos"])
                    headlines.append({
                        "title": clean,
                        "source": "exa",
                        "lang": "es" if is_es else "en",
                        "score": 0,
                        "url": r.url or ""
                    })
        print(f"   🔍 [Exa] {len(headlines)} titulares de dominios especializados")
    except Exception as e:
        print(f"   ⚠️ [Exa] Error: {e}")
    
    return headlines


# ============================================================
# FUENTE 4: Gemini Grounding (Búsqueda en tiempo real)
# ============================================================

def fetch_gemini_grounding(category, config, target_lang=None):
    """Usa Gemini con Google Search grounding para tendencias en tiempo real."""
    headlines = []
    if not client:
        return headlines
    
    try:
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        cat_type = config.get("type", "technical")
        lang_label = target_lang.upper() if target_lang else "BOTH"
        
        if target_lang == "es":
            market_instruction = "Search ONLY in SPANISH for trending topics in SPAIN (Madrid, Barcelona). NOT Latin America."
            output_format = "[ES] headline in Spanish\n" * 6
        elif target_lang == "en":
            market_instruction = "Search ONLY in ENGLISH for trending topics in the US and globally."
            output_format = "[EN] headline in English\n" * 6
        else:
            market_instruction = "For SPANISH market: search in Spanish for trending topics in Spain.\nFor ENGLISH market: search for trending topics in the US/global."
            output_format = "[ES] headline in Spanish\n[ES] headline in Spanish\n[ES] headline in Spanish\n[EN] headline in English\n[EN] headline in English\n[EN] headline in English"
        
        from datetime import datetime
        current_date_str = datetime.now().strftime("%B %Y")
        
        if cat_type == "news":
            prompt = f"""Search for the MOST TALKED ABOUT {category}-related events, drama, controversies, or viral moments happening RIGHT NOW (this week, {current_date_str}).

{market_instruction}

OUTPUT: List 6 specific, time-sensitive news headlines in this format:
{output_format}

RULES: No tutorials. No guides. Only NEWS, drama, and trending events."""
        else:
            prompt = f"""Search for the MOST INTERESTING {category}-related developments, launches, controversies, or breakthroughs happening RIGHT NOW (this week, {current_date_str}).

{market_instruction}

OUTPUT: List 6 specific, time-sensitive headlines in this format:
{output_format}

RULES: Focus on specific events, data, launches, or controversies. No generic evergreen content."""
        
        resp = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(tools=[google_search_tool])
        )
        
        if resp.text:
            for line in resp.text.strip().split('\n'):
                line = line.strip()
                if line.startswith('[ES]'):
                    clean = line[4:].strip().lstrip('- ').strip()
                    if len(clean.split()) >= 4:
                        headlines.append({"title": clean, "source": "gemini_grounding", "lang": "es", "score": 0, "url": ""})
                elif line.startswith('[EN]'):
                    clean = line[4:].strip().lstrip('- ').strip()
                    if len(clean.split()) >= 4:
                        headlines.append({"title": clean, "source": "gemini_grounding", "lang": "en", "score": 0, "url": ""})
            
            print(f"   🌐 [Grounding/{lang_label}] {len(headlines)} titulares en tiempo real")
    except Exception as e:
        print(f"   ⚠️ [Grounding] Error: {e}")
    
    return headlines


# ============================================================
# SELECTOR: LLM elige los 3 mejores temas
# ============================================================

def select_best_topics(all_headlines, category, config, count=3, target_lang=None):
    """LLM selector: elige los temas con más potencial viral y editorial."""
    if not all_headlines:
        return []
    
    if not client:
        # Sin LLM, devolver los primeros
        return all_headlines[:count]
    
    # Separar por idioma
    es_headlines = [h for h in all_headlines if h["lang"] == "es"]
    en_headlines = [h for h in all_headlines if h["lang"] == "en"]
    
    headlines_text = "### SPANISH HEADLINES:\n"
    for i, h in enumerate(es_headlines):
        headlines_text += f"{i+1}. [{h['source']}] {h['title']}\n"
    headlines_text += "\n### ENGLISH HEADLINES:\n"
    for i, h in enumerate(en_headlines):
        headlines_text += f"{i+1}. [{h['source']}] {h['title']}\n"
    
    cat_type = config.get("type", "technical")
    
    if cat_type == "news":
        criteria = """SELECTION CRITERIA (for viral/news content):
- Pick the most CONTROVERSIAL, DRAMATIC, or SURPRISING headlines
- Prefer topics with named people, specific events, or strong emotions
- REJECT tutorials, guides, or how-to topics
- REJECT generic/evergreen topics that could be written any time"""
    else:
        criteria = """SELECTION CRITERIA (for technical/analytical content):
- Pick topics with DATA, specific tools, or concrete problems
- Prefer contrarian angles, hidden risks, or surprising comparisons
- REJECT generic overview topics ("What is X", "Guide to Y")
- Prefer topics that target ADVANCED users, not beginners"""

    if target_lang == "es":
        output_format = "[ES] Rewritten Spanish title\n[ES] Rewritten Spanish title\n[ES] Rewritten Spanish title"
    elif target_lang == "en":
        output_format = "[EN] Rewritten English title\n[EN] Rewritten English title\n[EN] Rewritten English title"
    else:
        output_format = "[ES] Rewritten Spanish title\n[EN] Rewritten English title\n[ES or EN] Rewritten title in whichever language"

    selector_prompt = f"""ACT AS: Senior Editorial Director.

You have these candidate headlines for the "{category}" section:

{headlines_text}

{criteria}

TASK: Select the TOP 3 topics based on the criteria.

For each selected topic, rewrite it as a compelling, clickable blog title that promises unique insight.
You MUST write the titles in the target language.

OUTPUT FORMAT (exactly 3 lines, no numbering, no quotes):
{output_format}

OUTPUT ONLY THE 3 LINES. Nothing else."""

    # === OMEGA MATRIX: Selector usa la cascada waterfall ===
    resp_text = _llm_generate(selector_prompt)
    if resp_text:
        selected = []
        for line in resp_text.strip().split('\n'):
            line = line.strip()
            if line.startswith('[ES]'):
                title = line[4:].strip().lstrip('- ').strip()
                if title and len(title.split()) >= 4:
                    selected.append({"title": title, "lang": "es", "source": "llm_selected"})
            elif line.startswith('[EN]'):
                title = line[4:].strip().lstrip('- ').strip()
                if title and len(title.split()) >= 4:
                    selected.append({"title": title, "lang": "en", "source": "llm_selected"})
        
        if selected:
            print(f"   🏆 [Selector] {len(selected)} temas seleccionados")
            return selected[:count]
    
    # Fallback: devolver los primeros headlines raw
    return all_headlines[:count]


# ============================================================
# MAIN PIPELINE
# ============================================================

def scout(category, target_lang=None):
    """Pipeline completo de scouting para una categoría.
    Si target_lang es 'es' o 'en', busca SOLO en ese idioma.
    """
    config = CATEGORY_CONFIG.get(category)
    if not config:
        print(f"❌ Categoría '{category}' no reconocida.")
        sys.exit(1)
    
    lang_label = target_lang.upper() if target_lang else "BOTH"
    print(f"\n{'='*60}")
    print(f"🔭 TREND SCOUT V3 — Categoría: {category.upper()} | Idioma: {lang_label}")
    print(f"{'='*60}\n")
    
    all_headlines = []
    
    # === FUENTE 1: HackerNews (solo EN — es un foro anglosajón) ===
    if target_lang != "es" and config.get("hn_tags"):
        hn_results = fetch_hackernews(config["hn_tags"], limit=5)
        all_headlines.extend(hn_results)
    
    # === FUENTE 2: Google News RSS (solo el idioma objetivo) ===
    langs_to_search = [target_lang] if target_lang else ["es", "en"]
    for lang in langs_to_search:
        queries = config.get("news_queries", {}).get(lang, [])
        if queries:
            # Buscar con TODAS las queries para maximizar cobertura en modo monolingüe
            for query in queries:
                gn_results = fetch_google_news(query, lang=lang, limit=5)
                all_headlines.extend(gn_results)
    
    # === FUENTE 3: Exa Neural Search (solo EN — dominios anglosajones) ===
    if target_lang != "es" and config.get("exa_domains"):
        exa_query = random.choice(
            config.get("news_queries", {}).get("en", [f"trending {category} news"])
        )
        exa_results = fetch_exa_news(exa_query, config["exa_domains"], limit=5)
        all_headlines.extend(exa_results)
    
    # === FUENTE 4: Gemini Grounding (forzado al idioma objetivo) ===
    grounding_results = fetch_gemini_grounding(category, config, target_lang=target_lang)
    all_headlines.extend(grounding_results)
    
    print(f"\n   📊 TOTAL: {len(all_headlines)} titulares recopilados [{lang_label}]")
    
    # === SELECCIÓN LLM ===
    best_topics = select_best_topics(all_headlines, category, config, count=3, target_lang=target_lang)
    
    # Forzar el lang correcto en todos los topics seleccionados (monolingüe)
    if target_lang:
        for t in best_topics:
            t["lang"] = target_lang
    
    # === GUARDAR JSON ===
    output = {
        "category": category,
        "lang": target_lang or "mixed",
        "scouted_at": datetime.now(timezone.utc).isoformat(),
        "total_candidates": len(all_headlines),
        "topics": [
            {
                "rank": i + 1,
                "title": t["title"],
                "lang": t.get("lang", target_lang or "en"),
                "source": t.get("source", "unknown")
            }
            for i, t in enumerate(best_topics)
        ]
    }
    
    os.makedirs("data", exist_ok=True)
    # Fichero con sufijo de idioma: trends_ia_es.json / trends_ia_en.json
    lang_suffix = f"_{target_lang}" if target_lang else ""
    output_path = f"data/trends_{category}{lang_suffix}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n   ✅ Guardado: {output_path}")
    print(f"   📋 Temas seleccionados:")
    for t in output["topics"]:
        print(f"      #{t['rank']} [{t['lang'].upper()}] {t['title']}")
    
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trend Scout V3 — Pre-Searcher Agent")
    parser.add_argument('--category', type=str, required=True, help='Category: ia, fitness, crypto, youtube, viral')
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None, help='Force single-language search: es (Spain/LATAM) or en (US/Global)')
    args = parser.parse_args()
    
    scout(args.category.lower(), target_lang=args.lang)
