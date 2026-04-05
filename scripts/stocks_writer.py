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
from llm_router import LLMRouter

load_dotenv()

# --- API Keys ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENROUTER_KEY = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
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
from utils import SlugManager, LinkManager


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


from typing import List, Dict, Any, Optional, Union

# ============================================================
# MOTOR LLM CASCADA (Writer — Aislado)
# ============================================================

def _call_writer_engine_v3_core(prompt_text: str, lang: str = "en") -> Optional[str]:
    """
    Motor de escritura original (Cascada Tier 1-4).
    """
    or_key = OPENROUTER_KEY

    if lang == "es":
        # ── MOTOR ES 1: OpenRouter DeepSeek V3 ──
        if or_key:
            print("   🧠 [Stocks Writer ES] Motor 1: DeepSeek V3 (OpenRouter)...")
            try:
                ds_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: DEEPSEEK]: You are a logic-driven financial model."
                resp = or_client.chat.completions.create(model="deepseek/deepseek-chat-v3-0324:free", messages=[{"role": "user", "content": ds_prompt}], temperature=0.85)
                res = resp.choices[0].message.content.strip()
                if res and len(res) > 500: return res
            except Exception as e:
                logging.warning(f"[Stocks Writer ES] TIER 1 DeepSeek V3 failed: {type(e).__name__}: {str(e)[:150]}")

        # ── MOTOR ES 2: Groq (Llama 3.3 70B) ──
        if GROQ_API_KEY:
            try:
                llama_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: LLAMA-3]: You are a highly narrative model."
                resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": llama_prompt}])
                res = resp.choices[0].message.content.strip()
                if res and len(res) > 500: return res
            except Exception as e:
                logging.warning(f"[Stocks Writer ES] TIER 2 Groq Llama-3.3-70B failed: {type(e).__name__}: {str(e)[:150]}")
    else:
        # ── MOTOR EN 1: OpenRouter DeepSeek V3 ──
        if or_key:
            try:
                ds_prompt = prompt_text + "\n\n[SYSTEM CALIBRATION: DEEPSEEK]: Analytical depth required."
                resp = or_client.chat.completions.create(model="deepseek/deepseek-chat-v3-0324:free", messages=[{"role": "user", "content": ds_prompt}])
                res = resp.choices[0].message.content.strip()
                if res and len(res) > 500: return res
            except Exception as e:
                logging.warning(f"[Stocks Writer EN] TIER 1 DeepSeek V3 failed: {type(e).__name__}: {str(e)[:150]}")

        # ── MOTOR EN 2: Groq ──
        if GROQ_API_KEY:
            try:
                resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt_text}])
                res = resp.choices[0].message.content.strip()
                if res and len(res) > 500: return res
            except Exception as e:
                logging.warning(f"[Stocks Writer EN] TIER 2 Groq failed: {type(e).__name__}: {str(e)[:150]}")

    # TIER 3: NVIDIA NIM (GLM-4.7) — alineado con orquestator
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            nvidia_client = OpenAI(
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1",
            )
            calibration = (
                "\n\n[SYSTEM CALIBRATION: GLM-NIM]: You are a GLM analytical financial model "
                "hosted on NVIDIA NIM. Prioritize factual accuracy, clear structure and natural "
                "financial journalism tone."
            )
            extra_body = {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}}
            resp = nvidia_client.chat.completions.create(
                model="z-ai/glm4.7",
                messages=[{"role": "user", "content": prompt_text + calibration}],
                temperature=1,
                top_p=1,
                max_tokens=16384,
                extra_body=extra_body,
            )
            res = resp.choices[0].message.content.strip()
            if res and len(res) > 500:
                return res
        except Exception as e:
            logging.warning(
                f"[Stocks Writer] TIER 3 NVIDIA GLM-4.7 failed: {type(e).__name__}: {str(e)[:150]}"
            )

    # TIER 4: Gemini 
    if gemini_client:
        resp = gemini_client.models.generate_content(model='gemini-2.0-flash', contents=prompt_text)
        return resp.text.strip()
    return None


def _call_writer_engine(prompt_text: str, lang: str = "en") -> Optional[str]:
    """
    Motor de escritura con Capa Cero (GitHub Models).
    """
    system_prompt = "You are a senior financial analyst and fund manager."
    return LLMRouter.route_call(
        prompt_text, 
        system_prompt, 
        lambda p, s: _call_writer_engine_v3_core(p, lang), 
        model_type="reasoning"
    )


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
Las siguientes URLs han sido PRE-VERIFICADAS y son reales.
Debes insertar obligatoriamente estos enlaces como hipervínculos Markdown (ej. [texto](url)) de forma natural en el cuerpo del artículo.
ESTÁ ABSOLUTAMENTE PROHIBIDO inventar, adivinar o fabricar URLs. Si necesitas un enlace que no está aquí, cita la fuente en texto plano con **negrita**.
{urls_list}
"""
        print(f"   🔗 [Writer] {len(verified_urls)} URLs pre-verificadas inyectadas")

    internal_links_block = ""
    internal_links = LinkManager.get_latest_internal_links(lang=lang, limit=5)
    if internal_links:
        links_str = "\n".join([f"  - [{l['title']}]({l['url']})" for l in internal_links])
        internal_links_block = f"""

### 🔗 ENLAZADO INTERNO OBLIGATORIO (RETENCIÓN DE USUARIO)
Debes incluir al menos 1 enlace interno contextual hacia uno de estos artículos previos del blog NovumWorld.
Inyecta el enlace de forma natural en el texto usando el formato Markdown exacto proporcionado a continuación:
{links_str}
"""

    research_text = f"""HEADLINES FINANCIEROS RECIENTES:
{headlines_ctx}

ESTILOS DE COMPETIDORES:
{competitor_ctx}
{notebooklm_ctx}
{verified_urls_block}
{internal_links_block}"""

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

You MUST return ONLY a valid JSON object with this exact structure:
{{
  "candidates": ["title 1", "title 2", "title 3", "title 4", "title 5"],
  "best": "the single best title from the list above"
}}
Return ONLY the JSON object. No markdown, no explanations."""

    viral_title = tema  # fallback
    try:
        def fallback_stock_title(p, s):
            resp = gemini_client.models.generate_content(
                model='gemini-2.0-flash', contents=p,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return resp.text.strip()
            
        raw_json = LLMRouter.route_call(title_prompt, "You are a financial news editor creating JSON title candidates.", fallback_stock_title, model_type="reasoning")
        if raw_json:
            title_json = json.loads(raw_json.strip())
            best = title_json.get("best", "")
            if best and len(best.split()) >= 4:
                viral_title = best.strip('"').strip("'")
            elif title_json.get("candidates"):
                # Fallback: usar el último candidato
                for c in reversed(title_json["candidates"]):
                    if c and len(c.split()) >= 4:
                        viral_title = c.strip('"').strip("'")
                        break
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"   ⚠️ Error parseando JSON de título: {e}. Usando fallback...")
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
   - 🚨 PLEASE DO NOT FABRICATE URLs.
6. MINIMUM LENGTH: 1500 words. Please do not write articles under 1200 words.
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
        def fallback_stock_meta(p, s):
            resp = gemini_client.models.generate_content(model='gemini-2.0-flash', contents=p)
            return resp.text.strip()
            
        desc_text = LLMRouter.route_call(desc_prompt, "You are a financial SEO specialist.", fallback_stock_meta, model_type="parsing")
        raw_desc = desc_text.replace('"', "'") if desc_text else ""
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
