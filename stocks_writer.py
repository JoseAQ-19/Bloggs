#!/usr/bin/env python3
"""
STOCKS_WRITER.PY — Redactor LLM para Artículos de Fondos de Inversiónl
======================================================================
Recibe el output del stocks_scout, inyecta las instrucciones de tono y
estructura de stocks_instructions.py, genera el artículo con el LLM,
y CONCATENA AUTOMÁTICAMENTE el disclaimer legal al final.

REGLA DE ORO: Este archivo NO importa ni modifica NADA del núcleo existente.
"""

import os
import re
import json
import random
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
except Exception:
    gemini_client = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Imports del módulo stocks (aislados)
from stocks_instructions import (
    PROMPTS, DISCLAIMERS, ARTICLE_STRUCTURE,
    NICHE_CONFIG, FRONTMATTER_TEMPLATE
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


from typing import List, Dict, Any, Optional, Union

# ============================================================
# MOTOR LLM CASCADA (Writer — Aislado)
# ============================================================

def _call_writer_engine(prompt_text: str, lang: str = "en") -> Optional[str]:
    """
    Motor de escritura cascada para fondos de inversión.
    ES: Zhipu GLM-4.7 (via OpenRouter) → Gemini
    EN: OpenRouter GLM-4.5-Air → Llama 3.3 70B → Gemini
    """
    or_key = OPENROUTER_KEY

    if lang == "es":
        # ── MOTOR ES 1: OpenRouter DeepSeek V3 ──
        if or_key:
            print("   🧠 [Stocks Writer ES] Motor 1: DeepSeek V3 (OpenRouter)...")
            max_retries = 3
            backoff_seconds = [10, 25, 60]
            for attempt in range(max_retries):
                try:
                    ds_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: DEEPSEEK]: You are a logic-driven financial model. Prioritize analytical depth, accuracy, and structured reasoning. Skip any filler intro."
                    resp = or_client.chat.completions.create(
                        model="deepseek/deepseek-chat-v3-0324:free",
                        messages=[{"role": "user", "content": ds_prompt}],
                        temperature=0.85,
                        max_tokens=8192
                    )
                    result = resp.choices[0].message.content.strip()
                    if result and len(result) > 500:
                        print("   ✅ DeepSeek V3 respondió correctamente.")
                        return result
                    else:
                        print("   ⚠️ DeepSeek V3 respuesta muy corta. Reintentando...")
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "rate" in error_str.lower():
                        import time as _time
                        wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 60
                        logging.warning(f"⏳ RATE LIMIT 429 DeepSeek ES (intento {attempt+1}). Esperando {wait}s...")
                        _time.sleep(wait)
                    else:
                        logging.warning(f"DeepSeek V3 error: {e}")
                        break

        # ── MOTOR ES 2: Groq (Llama 3.3 70B) ──
        if GROQ_API_KEY:
            print("   🧠 [Stocks Writer ES] Motor 2: Groq (Llama 3.3 70B)...")
            max_retries = 2
            backoff_seconds = [5, 15]
            for attempt in range(max_retries):
                try:
                    llama_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: LLAMA-3]: You are a highly narrative open-weight model. Focus on seamless journalistic transitions, engaging prose, and avoiding repetitive AI-like sentence structures."
                    resp = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": llama_prompt}],
                        temperature=0.85,
                        max_tokens=8000
                    )
                    result = resp.choices[0].message.content.strip()
                    if result and len(result) > 500:
                        print("   ✅ Groq respondió correctamente a altísima velocidad.")
                        return result
                    else:
                        print("   ⚠️ Groq respuesta muy corta. Reintentando...")
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "rate" in error_str.lower():
                        import time as _time
                        wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 20
                        logging.warning(f"⏳ RATE LIMIT Groq ES (intento {attempt+1}). Esperando {wait}s...")
                        _time.sleep(wait)
                    else:
                        logging.warning(f"Groq API error: {e}")
                        break
    else:
        # ── MOTOR EN 1: OpenRouter DeepSeek V3 ──
        if or_key:
            print("   🧠 [Stocks Writer EN] Motor 1: DeepSeek V3 (OpenRouter)...")
            max_retries = 3
            backoff_seconds = [10, 25, 60]
            for attempt in range(max_retries):
                try:
                    ds_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: DEEPSEEK]: You are a logic-driven financial model. Prioritize analytical depth, accuracy, and structured reasoning. Skip any filler intro."
                    resp = or_client.chat.completions.create(
                        model="deepseek/deepseek-chat-v3-0324:free",
                        messages=[{"role": "user", "content": ds_prompt}],
                        temperature=0.85,
                        max_tokens=8192
                    )
                    result = resp.choices[0].message.content.strip()
                    if result and len(result) > 500:
                        print("   ✅ DeepSeek V3 respondió correctamente.")
                        return result
                    else:
                        print("   ⚠️ DeepSeek V3 respuesta muy corta. Reintentando...")
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "rate" in error_str.lower():
                        import time as _time
                        wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 60
                        logging.warning(f"⏳ RATE LIMIT 429 DeepSeek EN (intento {attempt+1}). Esperando {wait}s...")
                        _time.sleep(wait)
                    else:
                        logging.warning(f"DeepSeek V3 error: {e}")
                        break

        # ── MOTOR EN 2: Groq (Llama 3.3 70B) ──
        if GROQ_API_KEY:
            print("   🧠 [Stocks Writer EN] Motor 2: Groq (Llama 3.3 70B)...")
            max_retries = 2
            backoff_seconds = [5, 15]
            for attempt in range(max_retries):
                try:
                    llama_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: LLAMA-3]: You are a highly narrative open-weight model. Focus on seamless journalistic transitions, engaging prose, and avoiding repetitive AI-like sentence structures. Skip filler intros."
                    resp = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": llama_prompt}],
                        temperature=0.85,
                        max_tokens=8000
                    )
                    result = resp.choices[0].message.content.strip()
                    if result and len(result) > 500:
                        print("   ✅ Groq respondió correctamente a altísima velocidad.")
                        return result
                    else:
                        print("   ⚠️ Groq respuesta muy corta. Reintentando...")
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "rate" in error_str.lower():
                        import time as _time
                        wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 20
                        logging.warning(f"⏳ RATE LIMIT Groq EN (intento {attempt+1}). Esperando {wait}s...")
                        _time.sleep(wait)
                    else:
                        logging.warning(f"Groq API error: {e}")
                        break

    # ── MOTOR 3: NVIDIA API (Llama 3.1 70B / Nemotron) ──
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        print(f"   🟢 [Stocks Writer {lang.upper()}] Motor 3: NVIDIA API (Llama 3.1 70B)...")
        try:
            nvidia_client = OpenAI(api_key=nvidia_key, base_url="https://integrate.api.nvidia.com/v1")
            nvidia_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: LLAMA-3]: You are a highly narrative open-weight model. Focus on seamless journalistic transitions, engaging prose, and avoiding repetitive AI-like sentence structures."
            resp = nvidia_client.chat.completions.create(
                model="meta/llama-3.1-70b-instruct",
                messages=[{"role": "user", "content": nvidia_prompt}],
                temperature=0.85,
                max_tokens=4096
            )
            result = resp.choices[0].message.content.strip()
            if result and len(result) > 500:
                print("   ✅ NVIDIA API respondió correctamente.")
                return result
            else:
                print("   ⚠️ NVIDIA respuesta vacía. Activando emergencia...")
        except Exception as e:
            logging.warning(f"🚨 FALLBACK TRIGGERED: NVIDIA API falló por [{type(e).__name__}]: {e}. Cayendo a Gemini...")

    # ── EMERGENCIA: Gemini ──
    if gemini_client:
        print("   🚨 [Stocks Writer] Gemini 2.0 Flash (emergencia)...")
        try:
            gemini_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: GEMINI]: You are a fast, analytical model. Focus on precise formatting, avoiding repetitive introductions, and strictly following the negative constraints."
            resp = gemini_client.models.generate_content(
                model='gemini-2.0-flash', contents=gemini_prompt
            )
            return resp.text.strip()
        except Exception as e:
            logging.error(f"Gemini error: {e}")

    return None


# ============================================================
# GENERADOR DE SLUG LIMPIO
# ============================================================

def _generate_slug(text: str) -> str:
    """Genera un slug SEO-friendly a partir de un texto."""
    import unicodedata
    # Normalizar y eliminar acentos
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:80]  # Máximo 80 chars para el slug


# ============================================================
# LIMPIADOR POST-PROCESADOR
# ============================================================

def _clean_article(text: str) -> str:
    """Limpia artefactos comunes de LLM en el artículo generado."""
    if not text:
        return text

    # Eliminar encabezados H1 (solo permitimos H2+)
    text = re.sub(r'^#\s+.+$', '', text, flags=re.MULTILINE)

    # Eliminar frases de apertura de chatbot
    chatbot_openers = [
        r'^(Here is|Here\'s|Sure|Claro|Aquí tienes|Aquí está|Okay|Of course|Certainly)[,!.]?\s*.*?\n+',
        r'^(El siguiente|The following|A continuación).*?\n+',
    ]
    for pattern in chatbot_openers:
        text = re.sub(pattern, '', text, count=1, flags=re.IGNORECASE | re.MULTILINE)

    # Eliminar bloques markdown de código sueltos
    text = re.sub(r'^```\w*\s*$', '', text, flags=re.MULTILINE)

    # Limpiar líneas vacías excesivas
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text.strip()


# ============================================================
# PIPELINE DE ESCRITURA COMPLETO
# ============================================================

def write_fund_article(scout_data: Dict[str, Any], lang: str = "es") -> Optional[Dict[str, Any]]:
    """
    Pipeline completo de escritura para un artículo de fondos de inversión.
    
    Args:
        scout_data: dict del output de stocks_scout.scout_funds()
        lang: 'es' o 'en'
    
    Returns:
        dict con meta (titulo, slug, description) y contenido final (con disclaimer)
    """
    topics = scout_data.get("topics", [])
    if not topics:
        print("   ❌ [Stocks Writer] No hay temas del scout. Abortando.")
        return None

    # Seleccionar el primer tema válido
    topic = topics[0]
    tema = topic["title"]
    print(f"\n✍️ STOCKS WRITER ({lang.upper()}): {tema}")

    # === FASE 1: PLANIFICACIÓN (Título + Slug) ===
    print(f"   🎯 [Fase 1/3] Planificación editorial...")

    prompt_persona = PROMPTS.get(lang, PROMPTS["en"])

    # Contexto del scout (headlines + análisis de competidores)
    headlines_ctx = "\n".join([
        f"- {h['title']} (via {h['source']})"
        for h in scout_data.get("all_headlines", [])[:10]
    ])

    competitor_ctx = ""
    comp_analysis = scout_data.get("competitor_analysis", {})
    if comp_analysis:
        styles = comp_analysis.get("sample_styles", {})
        competitor_ctx = "\n".join([
            f"- {comp}: {style}"
            for comp, style in styles.items()
        ])

    # === NOTEBOOKLM DEEP RESEARCH (if available from stocks_main enrichment) ===
    notebooklm_ctx = ""
    notebooklm_research = scout_data.get("notebooklm_research", "")
    if notebooklm_research:
        notebooklm_ctx = f"\n\nDEEP RESEARCH (NotebookLM — verified sources, zero-hallucination):\n{notebooklm_research[:5000]}"
        print(f"   🧠 [Writer] NotebookLM research inyectado: {len(notebooklm_research)} chars")

    # === VERIFIED URLS (pre-hoc injection — FIX 3) ===
    verified_urls = scout_data.get("verified_urls", [])
    # Also extract URLs from scout headlines
    for h in scout_data.get("all_headlines", []):
        url = h.get("url", "")
        if url and url.startswith("http") and url not in verified_urls:
            verified_urls.append(url)
    
    verified_urls_block = ""
    if verified_urls:
        urls_list = "\n".join([f"  - {u}" for u in verified_urls[:15]])
        verified_urls_block = f"""

### FUENTES VALIDADAS DISPONIBLES (SOLO ESTAS URLs)
Las siguientes URLs han sido PRE-VERIFICADAS y son reales. DEBES usar al menos 3 de ellas como enlaces en el artículo.
ESTÁ ABSOLUTAMENTE PROHIBIDO inventar, adivinar o fabricar URLs. Si necesitas un enlace que no está aquí, cita la fuente en texto plano con **negrita**.
{urls_list}
"""
        print(f"   🔗 [Writer] {len(verified_urls)} URLs pre-verificadas inyectadas")

    research_text = f"""HEADLINES FINANCIEROS RECIENTES:
{headlines_ctx}

ESTILOS DE COMPETIDORES:
{competitor_ctx}
{notebooklm_ctx}
{verified_urls_block}"""

    # Generar título viral financiero
    lang_name = "ESPAÑOL" if lang == "es" else "ENGLISH"
    title_prompt = f"""ACT AS: Senior Financial Editor for {'Morningstar España' if lang == 'es' else 'Morningstar.com'}.

TASK: Generate 5 candidate titles for a mutual fund / investment article about: "{tema}"
LANGUAGE: {lang_name} ONLY.

RECENT FINANCIAL NEWS:
{headlines_ctx[:2000]}

RULES:
- Each title MUST contain a specific NUMBER, FUND NAME, PERCENTAGE, or FINANCIAL METRIC
- FORBIDDEN: "Guía completa", "Todo lo que necesitas saber", "Los mejores fondos" (generic)
- FORBIDDEN: Questions. Make STATEMENTS, not questions.
- Include data comparisons: "X vs Y", "X supera/beats Y by Z%"
- Maximum 15 words. Minimum 8 words.

OUTPUT FORMAT (exactly 6 lines):
1. [title 1]
2. [title 2]
3. [title 3]
4. [title 4]
5. [title 5]
BEST: [paste the single best title here]

OUTPUT ONLY THESE 6 LINES."""

    viral_title = tema  # fallback
    try:
        if gemini_client:
            title_resp = gemini_client.models.generate_content(
                model='gemini-2.0-flash', contents=title_prompt
            )
            for line in title_resp.text.strip().split('\n'):
                if line.strip().upper().startswith('BEST:'):
                    candidate = line.split(':', 1)[1].strip().strip('"').strip("'")
                    if len(candidate.split()) >= 4:
                        viral_title = candidate
                        break
            if viral_title == tema:
                for line in reversed(title_resp.text.strip().split('\n')):
                    clean = re.sub(r'^\d+\.\s*', '', line.strip()).strip('"').strip("'")
                    if len(clean.split()) >= 4 and not clean.upper().startswith('BEST'):
                        viral_title = clean
                        break
    except Exception as e:
        print(f"   ⚠️ Error generando título: {e}")

    slug = _generate_slug(viral_title) + ("-en" if lang == "en" else "")
    meta = {"titulo": viral_title, "slug": slug}
    print(f"   ✅ [Fase 1/3] Título: {viral_title}")

    # === FASE 2: REDACCIÓN CON ESTRUCTURA FINANCIERA ===
    print(f"   ✍️ [Fase 2/3] Redacción del artículo financiero...")

    write_prompt = f"""{prompt_persona}

CRITICAL FORMATTING RULES:
1. NO TITLE REPETITION: Do NOT include H1 at the beginning.
2. START IMMEDIATELY with the Hook paragraph.
3. Use H2 (##) for main sections. NEVER use H1 (#).
4. LANGUAGE PURITY: ALL text must be in {lang_name}. No mixing languages.
5. OUTBOUND LINKS (MANDATORY — PRE-VERIFIED ONLY):
   - You MUST include at least 3 hyperlinks to financial sources.
   - 📌 PRIORITY: Use ONLY the URLs listed in the "FUENTES VALIDADAS DISPONIBLES" section below.
   - Copy-paste the exact URL from the list. DO NOT modify, shorten or invent URLs.
   - If you need to cite a source not in the list, use bold text (**Source Name**) without a URL.
   - 🚨 FABRICATING A URL = INSTANT ARTICLE REJECTION. Zero tolerance.
6. MINIMUM LENGTH: 1500 words. Articles under 1200 words are REJECTED.
7. NO MARKDOWN TABLES. Use narrative prose with bullet points for data comparisons.
8. DO NOT include any disclaimer or legal notice — it will be added automatically.

ARTICLE TITLE: "{viral_title}"

RESEARCH CONTEXT:
{research_text[:8000]}

STRUCTURE: Follow the mandatory investment fund article structure:
- Hook with shocking financial data
- Comparative analysis of funds (performance 1Y/3Y/5Y, volatility, Sharpe, fees)
- Expert opinions with EXACT LITERAL QUOTES ("...") and named sources
- Contrarian angle / risks
- "The Machine's Verdict" (Cynical, robotic perspective, breaking neutrality)

WRITE THE FULL ARTICLE NOW. START IMMEDIATELY WITH THE FIRST SENTENCE (NO preamble, NO "here is the article")."""

    article_text = _call_writer_engine(write_prompt, lang=lang)

    if not article_text or len(article_text) < 300:
        print("   ❌ [Stocks Writer] Artículo vacío o muy corto. Abortando.")
        return None

    # === FASE 3: POST-PROCESADO + DISCLAIMER FORZADO ===
    print(f"   🛡️ [Fase 3/3] Post-procesado y disclaimer legal...")

    article_text = _clean_article(article_text)

    # === CRÍTICO: INYECCIÓN FORZADA DEL DISCLAIMER ===
    # Pase lo que pase, el disclaimer se concatena al final.
    disclaimer = DISCLAIMERS.get(lang, DISCLAIMERS["en"])
    article_with_disclaimer = article_text + disclaimer

    word_count = len(article_with_disclaimer.split())
    print(f"   📊 Longitud: {word_count} palabras (mín: 1200)")
    print(f"   ✅ [Stocks Writer] Artículo completado con disclaimer {lang.upper()} inyectado.")

    # Generar meta description
    description = ""
    try:
        if gemini_client:
            desc_prompt = (
                f"Write a unique, compelling meta description of EXACTLY 140-155 characters "
                f"in {'Spanish' if lang == 'es' else 'English'} for a mutual fund article titled "
                f"'{viral_title}'. Output ONLY the description text. No quotes. No trailing ellipses."
            )
            desc_resp = gemini_client.models.generate_content(
                model='gemini-2.0-flash', contents=desc_prompt
            )
            raw_desc = desc_resp.text.strip().replace('"', "'")
            if len(raw_desc) > 155:
                description = raw_desc[:155].rsplit(' ', 1)[0] + '.'
            else:
                description = raw_desc if raw_desc.endswith('.') else raw_desc + '.'
    except Exception:
        pass

    if not description or len(description) < 20:
        description = re.sub(r'[#*\[\]]', '', article_text)[:154].replace('\n', ' ').strip() + '.'

    meta["description"] = description

    return {
        "meta": meta,
        "content": article_with_disclaimer,
        "word_count": word_count,
        "lang": lang,
        "disclaimer_injected": True
    }


# ============================================================
# MAIN (ejecución independiente para testing)
# ============================================================

if __name__ == "__main__":
    # Test con datos mock del scout
    mock_scout = {
        "topics": [
            {"rank": 1, "title": "Vanguard FTSE All-World vs iShares MSCI World: Comparativa 2025", "lang": "es"}
        ],
        "all_headlines": [
            {"title": "Indexa Capital supera el 12% anualizado a 5 años", "source": "google_news"},
            {"title": "BlackRock lanza nuevo ETF de bonos europeos", "source": "rss_morningstar"}
        ],
        "competitor_analysis": {
            "sample_styles": {
                "morningstar_es": "Institucional, datos Morningstar",
                "bestinver": "Value investing, cartas trimestrales"
            }
        }
    }

    result = write_fund_article(mock_scout, lang="es")
    if result:
        print(f"\n{'=' * 60}")
        print(f"📝 RESULTADO:")
        print(f"   Título: {result['meta']['titulo']}")
        print(f"   Slug: {result['meta']['slug']}")
        print(f"   Palabras: {result['word_count']}")
        print(f"   Disclaimer: {'✅' if result['disclaimer_injected'] else '❌'}")
        print(f"   Preview: {result['content'][:200]}...")
