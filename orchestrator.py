import os
import re
import json
import random
import glob
from datetime import datetime, timedelta
import hashlib
import logging
import text_cleaner
from llm_router import LLMRouter
from utils import LinkManager, ContentCleaner
from novum_visual import get_image
import indexing_api
from openai import OpenAI
from google import genai
from google.genai import types

from prompts_factory import (
    PROMPT_PERSONA_ES, PROMPT_PERSONA_EN,
    PROMPT_FITNESS_ES, PROMPT_FITNESS_EN,
    PROMPT_CRYPTO_ES,  PROMPT_CRYPTO_EN,
    PROMPT_YOUTUBE_ES, PROMPT_YOUTUBE_EN,
    PROMPT_VIRAL_ES,   PROMPT_VIRAL_EN,
    PROMPT_TOOLS_ES,   PROMPT_TOOLS_EN,
    SYSTEM_FORMAT_RULES,
    PromptFactory,
)
from niche_registry import NICHES, STRUCTURE_TEMPLATES

try:
    from prompts_tools import PROMPT_BLUEPRINT_EN, PROMPT_BLUEPRINT_ES
except ImportError:
    # Fallback
    PROMPT_BLUEPRINT_EN = "ACT AS TECH GURU..."
    PROMPT_BLUEPRINT_ES = "ACTUA COMO ESTRATEGA..."

GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
except Exception:
    client = None

COMPLETED_FILE = "data/completed.txt"

# --- FENIX V3: Bloqueo de Redundancia Semántica ---
STOPWORDS = {'the', 'and', 'of', 'in', 'to', 'a', 'is', 'for', 'on', 'with', 'that', 'it', 'as', 'by', 'an', 'at',
             'el', 'la', 'de', 'en', 'y', 'los', 'las', 'del', 'al', 'un', 'una', 'es', 'por', 'que', 'se', 'con',
             'su', 'no', 'para', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue', 'este', 'ha', 'son', 'its',
             'are', 'was', 'be', 'been', 'has', 'have', 'not', 'but', 'from', 'or', 'which', 'we', 'they', 'will',
             'about', 'today', 'why', 'how', 'what', 'trending', 'analysis', 'new', 'latest'}

def is_topic_redundant(new_topic, category):
    """Bloquea temas con más de 60% de solapamiento semántico con temas completados en la misma categoría."""
    if not os.path.exists(COMPLETED_FILE):
        return False
    
    with open(COMPLETED_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f if l.strip()]
    
    # Filtrar solo temas de la misma categoría
    category_topics = []
    for line in lines:
        if line.startswith(f"{category}:"):
            topic_text = line.split(":", 1)[1].strip().lower()
            category_topics.append(topic_text)
    
    if not category_topics:
        return False
    
    # Extraer keywords del nuevo tema (sin stopwords)
    new_keywords = {w for w in new_topic.lower().split() if w not in STOPWORDS and len(w) > 2}
    
    if not new_keywords:
        return False
    
    # Comparar contra cada tema existente
    for existing_topic in category_topics:
        existing_keywords = {w for w in existing_topic.split() if w not in STOPWORDS and len(w) > 2}
        if not existing_keywords:
            continue
        
        # Solapamiento bidireccional
        overlap = len(new_keywords & existing_keywords)
        similarity = overlap / min(len(new_keywords), len(existing_keywords))
        
        if similarity > 0.4:
            print(f"  ⚠️ REDUNDANCY: '{new_topic}' overlaps {similarity*100:.0f}% with '{existing_topic}'")
            return True
    
    return False

def safety_check(topic):
    try:
        prompt = f"ACT AS: Content Safety Moderator. TOPIC: '{topic}'. OUTPUT: SAFE or UNSAFE.\nRULES: Allow clickbait, sensationalism, drama, controversies, and gossip (SAFE). ONLY reply 'UNSAFE' if it promotes real-world physical violence, terrorism, self-harm, or explicit adult content/pornography. Otherwise, it is SAFE."
        
        # Fallback core para safety (Gemini)
        def fallback(p, s):
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=p)
            return resp.text.strip()
            
        res = LLMRouter.route_call(prompt, "You are a content safety moderator.", fallback, model_type="parsing")
        if res and "UNSAFE" in res.upper():
            return False
        return True
    except Exception as e:
        logging.warning(f"[safety_check] Error checking topic '{topic[:50]}': {type(e).__name__}: {e}")
        return True

def planificar_articulo(tema, contexto, lang, category_config):
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    lang_instruction = (
        f"\n\nCRITICAL LANGUAGE RULE: The 'titulo' MUST be written ENTIRELY in {'SPANISH (Español)' if lang == 'es' else 'ENGLISH'}. "
        f"{'Do NOT use any English words in the title except proper nouns (brand names like Bitcoin, NBA, etc.).' if lang == 'es' else 'Do NOT use any Spanish words in the title.'} "
        f"Please follow this rule strictly."
    )
    # Handle V4 dict format
    ctx_text = contexto.get('content', '')[:1000] if isinstance(contexto, dict) else str(contexto)[:1000]
    prompt = f"{prompt_persona}\n{SYSTEM_FORMAT_RULES}{lang_instruction}\nTopic: {tema}\nContext: {ctx_text}\nLanguage: {lang}\nSTRICT JSON: {{ \"titulo\": \"...\", \"slug_sugerido\": \"...\" }}"
    
    def fallback_plan(p, s):
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=p, config=types.GenerateContentConfig(response_mime_type="application/json"))
        return resp.text.strip()

    try:
        raw_text = LLMRouter.route_call(prompt, "You are a professional editor planning an article structure. Titles MUST be ≤70 characters, magnetic, and avoid generic patterns like 'Analysis of...'.", fallback_plan, model_type="reasoning", temperature=0.95)
        if not raw_text:
            raise Exception("No response from Router in planning")
            
        if '```' in raw_text:
            raw_text = raw_text.replace('```json', '').replace('```', '')
        plan = json.loads(raw_text.strip())
        
        # === BLINDAJE SEO: Título ≤70 caracteres ===
        if len(plan.get('titulo', '')) > 70:
            original_title = plan['titulo']
            # Truncar en la última palabra completa antes de 70 chars
            truncated = original_title[:70].rsplit(' ', 1)[0]
            plan['titulo'] = truncated
            print(f"   ✂️ [SEO] Título recortado: '{original_title}' → '{truncated}' ({len(truncated)} chars)")
        
        suffix = "-en" if lang == "en" else ""
        plan['slug'] = text_cleaner.sanitize_slug(plan['slug_sugerido']) + suffix
        return plan
    except Exception as e:
        logging.warning(f"[planificar_articulo] Fallo al planificar '{tema[:50]}': {type(e).__name__}: {e}")
        return {"titulo": f"{tema} Analysis", "slug": text_cleaner.sanitize_slug(tema) + ("-en" if lang=="en" else "")}

# --- E-E-A-T OUTBOUND LINK INJECTION RULES (v3.0) ---
EEAT_LINK_RULES = """
═══════════════════════════════════════════════════
🔗 LINKING SHIELD v3.0 — STRICT PROTOCOL
═══════════════════════════════════════════════════

EXTERNAL LINKS (Authority):
1. You MUST include a MINIMUM of 3 outbound hyperlinks in Markdown format: [Source Name](https://exact-url.com)
2. These links MUST use URLs from the "FUENTES VALIDADAS DISPONIBLES" section when available, copy-pasted VERBATIM.
3. If no verified URL exists, use the publication's homepage (e.g., https://www.reuters.com, https://www.bloomberg.com).
4. NEVER cite a source using only bold text (**Source**). Every source MUST be a clickable hyperlink.
5. Please avoid placeholder citations like **FUENTES INFORMADAS**, **source**, or **unnamed sources**.
6. Do NOT use scholar.google.com or google.com/search as placeholder links.
7. A single fabricated URL will cause the ENTIRE article to be rejected.

INTERNAL LINKS (Retention):
8. You MUST include at LEAST 1 internal link using the URLs from the "ENLAZADO INTERNO OBLIGATORIO" section.
9. Internal links MUST be contextually relevant — weave them naturally into a sentence.
10. Format: [descriptive anchor text](relative-path)

TRIGGERS (When you MUST add a link):
- A statistic or data point → link to the original report/study
- An expert's name or quote → link to their profile or publication
- A company action → link to a credible news article
- A study or research paper → link to PubMed, arXiv, IEEE, or the journal

MINIMUM: 3 outbound + 1 internal per article.
MAXIMUM: 12 outbound links (avoid appearing spammy).

QUALITY GATE: Articles missing ](http or ](/ will be REJECTED and re-generated.
"""

# ============================================================
# PROTOCOLO SPIDERWEB: Internal Linking Engine
# ============================================================

def _get_internal_links(category, lang, current_slug=""):
    """
    Lee los últimos 15 artículos de la misma categoría/idioma
    y devuelve una lista de (título, ruta_relativa) para interlinking.
    """
    pattern = f"content/{lang}/{category}/*.md"
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:15]
    links = []
    for fpath in files:
        slug = os.path.basename(fpath).replace('.md', '')
        if slug == current_slug or slug == '_index':
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read(500)
            # Extract title from frontmatter
            import re as _re
            m = _re.search(r'^title:\s*"?([^"\n]+)"?', content, _re.MULTILINE)
            if m:
                title = m.group(1).strip().strip('"').strip("'")
                # FIX BILINGÜE: EN es raíz /{cat}/{slug}/, ES es /es/{cat}/{slug}/
                if lang == "es":
                    rel_path = f"/es/{category}/{slug}/"
                else:
                    rel_path = f"/en/{category}/{slug}/"
                links.append((title, rel_path))
        except Exception as e:
            logging.debug(f"[_get_internal_links] Error reading {fpath}: {type(e).__name__}: {e}")
            continue
    return links[:10]  # Max 10 candidates


def _call_nvidia_nim(prompt_text, model_id, calibration_tag, nvidia_key, max_tokens=8192, force_json=False):
    """
    Helper genérico para llamadas a NVIDIA NIM API.
    Retorna (result_text, success_bool).
    Si force_json=True, fuerza respuesta JSON estricta.
    """
    try:
        nvidia_client = OpenAI(
            api_key=nvidia_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        extra_kwargs = {}
        system_msg = calibration_tag
        if force_json:
            extra_kwargs["response_format"] = {"type": "json_object"}
            system_msg += "\n\n[JSON MODE]: Debes devolver ÚNICAMENTE un objeto JSON válido con la estructura solicitada. Sin formato markdown, sin texto adicional, sin ```json. Solo el JSON puro."
        
        resp = nvidia_client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt_text + system_msg}],
            temperature=0.85,
            max_tokens=max_tokens,
            timeout=300,
            **extra_kwargs
        )
        result = resp.choices[0].message.content.strip()
        return result, bool(result and len(result) > 200)
    except Exception as e:
        logging.warning(f"🚨 NVIDIA NIM ({model_id}) error: [{type(e).__name__}]: {e}")
        return "", False


def _call_en_engine_v3_core(prompt_text, system_prompt=""):
    """
    Jerarquía Original EN (Tier 1-5).
    """
    import time as _time
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    or_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    full_prompt = prompt_text + system_prompt

    # ═══ CALIBRACIONES POR MODELO ═══
    CAL_GLM = "\n\n[SYSTEM CALIBRATION: GLM-NIM]: You are a GLM analytical model hosted on NVIDIA NIM. Prioritize absolute factual accuracy, concise transitions, deep analytical reasoning, and STRICT adherence to the provided data without hallucination. Your output must be journalistic-grade."
    CAL_LLAMA = "\n\n[SYSTEM CALIBRATION: LLAMA-3]: You are a highly narrative open-weight model. Focus on seamless journalistic transitions, engaging prose, and avoiding repetitive AI-like sentence structures. Do not use filler introductions."
    CAL_GEMINI = "\n\n[SYSTEM CALIBRATION: GEMINI]: You are a fast, analytical model. Focus on precise formatting, avoiding repetitive introductions, and strictly following the negative constraints."

    # --- TIER 1: NVIDIA NIM / GLM-4.7 (Redactor Premium) ---
    if nvidia_key:
        print("   🟢 [Omega EN] TIER 1: NVIDIA NIM / GLM-4.7 (Redactor)...")
        result, ok = _call_nvidia_nim(prompt_text, "z-ai/glm4.7", CAL_GLM, nvidia_key)
        if ok: return result

    # --- TIER 2: OpenRouter / GLM-4.5-Air (Free) ---
    if or_key:
        print("   🧠 [Omega EN] TIER 2: OpenRouter / GLM-4.5-Air...")
        try:
            or_client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
            resp = or_client.chat.completions.create(
                model="z-ai/glm-4.5-air:free",
                messages=[{"role": "user", "content": prompt_text + CAL_GLM}],
                temperature=0.85,
                max_tokens=8192,
                timeout=300
            )
            result = resp.choices[0].message.content.strip()
            if result and len(result) > 200: return result
        except Exception as e:
            logging.warning(f"[Omega EN] TIER 2 GLM-4.5-Air failed: {type(e).__name__}: {str(e)[:150]}")

    # --- TIER 3: OpenRouter / Llama 3.3 70B (con RETRY + BACKOFF) ---
    if or_key:
        max_retries = 3
        backoff_seconds = [10, 25, 60]
        for attempt in range(max_retries):
            print(f"   🔄 [Omega EN] TIER 3: Llama-3.3-70B (intento {attempt+1}/{max_retries})...")
            try:
                or_client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
                resp = or_client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=[{"role": "user", "content": prompt_text + CAL_LLAMA}],
                    temperature=0.85,
                    max_tokens=8192,
                    timeout=300
                )
                result = resp.choices[0].message.content.strip()
                if result and len(result) > 200: return result
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    _time.sleep(backoff_seconds[attempt])
                else: break

    # --- TIER 4: NVIDIA NIM / Llama-3.1-70B (Fallback de Élite) ---
    if nvidia_key:
        print("   🟠 [Omega EN] TIER 4: NVIDIA NIM / Llama-3.1-70B (Fallback Élite)...")
        result, ok = _call_nvidia_nim(prompt_text, "meta/llama-3.1-70b-instruct", CAL_LLAMA, nvidia_key)
        if ok: return result

    # --- TIER 5 (ÚLTIMO RECURSO): Gemini 2.0 Flash ---
    print("   🚨 [Omega EN] TIER 5: Gemini 2.0 Flash (Último Recurso)...")
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_text + CAL_GEMINI)
    return resp.text.strip()


def _call_en_engine(prompt_text):
    """
    Enrutador EN con Capa Cero.
    """
    return LLMRouter.route_call(
        prompt_text, 
        PROMPT_PERSONA_EN, 
        _call_en_engine_v3_core, 
        model_type="reasoning"
    )


def _call_es_engine_v3_core(prompt_text, system_prompt=""):
    """
    Jerarquía Original ES (Tier 1-5).
    """
    import time as _time
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    or_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    
    CAL_GLM_ES = "\n\n[SYSTEM CALIBRATION: GLM-NIM]: Eres un modelo GLM analítico. Prioriza la precisión lógica, la fluidez nativa en español, y el uso estricto de los datos proporcionados sin alucinaciones."
    CAL_LLAMA_ES = "\n\n[SYSTEM CALIBRATION: LLAMA-3]: Eres un modelo narrativo de código abierto. Céntrate en transiciones fluidas de periodismo."
    CAL_GEMINI_ES = "\n\n[SYSTEM CALIBRATION: GEMINI]: Eres un modelo rápido y analítico."

    # TIER 1: NVIDIA
    if nvidia_key:
        print("   🟢 [Omega ES] TIER 1: NVIDIA NIM / GLM-4.7...")
        res, ok = _call_nvidia_nim(prompt_text, "z-ai/glm4.7", CAL_GLM_ES, nvidia_key)
        if ok: return res

    # TIER 2: OpenRouter GLM-4.5
    if or_key:
        try:
            or_client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
            resp = or_client.chat.completions.create(model="z-ai/glm-4.5-air:free", messages=[{"role": "user", "content": prompt_text + CAL_GLM_ES}])
            res = resp.choices[0].message.content.strip()
            if res and len(res) > 200: return res
        except Exception as e:
            logging.warning(f"[Omega ES] TIER 2 GLM-4.5-Air failed: {type(e).__name__}: {str(e)[:150]}")

    # TIER 3: Llama 3.3
    if or_key:
        try:
            or_client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
            resp = or_client.chat.completions.create(model="meta-llama/llama-3.3-70b-instruct:free", messages=[{"role": "user", "content": prompt_text + CAL_LLAMA_ES}])
            res = resp.choices[0].message.content.strip()
            if res and len(res) > 200: return res
        except Exception as e:
            logging.warning(f"[Omega ES] TIER 3 Llama-3.3-70B failed: {type(e).__name__}: {str(e)[:150]}")

    # TIER 5: Gemini
    print("   🚨 [Omega ES] TIER 5: Gemini (Último Recurso)...")
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_text + CAL_GEMINI_ES)
    return resp.text.strip()


def _call_es_engine(prompt_text):
    """
    Enrutador ES con Capa Cero.
    """
    return LLMRouter.route_call(
        prompt_text, 
        PROMPT_PERSONA_ES, 
        _call_es_engine_v3_core, 
        model_type="reasoning"
    )


def escribir_articulo(meta, contexto, lang, category_config, category="ia"):
    print(f"✍️ PULITZER PIPELINE ({lang.upper()}): {meta['titulo']}...")
    # === AISLAMIENTO ESTRICTO DE VARIABLES ===
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    structure = random.choice(list(STRUCTURE_TEMPLATES.values()))
    
    # Extract content string from research dict
    if isinstance(contexto, dict):
        research_text = contexto.get('content', '')
        research_layer = contexto.get('layer', 'unknown')
        print(f"   📊 Research source: {research_layer}")
    else:
        research_text = str(contexto)
    
    # === PROTOCOLO SPIDERWEB V2: Solo si hay artículos diversos ===
    internal_links = _get_internal_links(category, lang, meta.get('slug', ''))
    spiderweb_instruction = ""
    if len(internal_links) >= 2:
        unique_links = []
        seen_words = set()
        for title, path in internal_links:
            title_words = {w.lower() for w in title.split() if len(w) > 3}
            if len(title_words & seen_words) < len(title_words) * 0.5:
                unique_links.append((title, path))
                seen_words.update(title_words)
        
        if len(unique_links) >= 2:
            links_text = "\n".join([f"  - [{t}]({p})" for t, p in unique_links[:5]])
            spiderweb_instruction = f"""\nINTERNAL LINKING (Spiderweb Protocol — ONLY if naturally relevant):
You MAY insert UP TO 2 internal links to other articles on our site, but ONLY if they are genuinely relevant to the current topic.
Do NOT force a link if it doesn't fit naturally. A forced, irrelevant internal link is WORSE than no link at all.
Insert them NATURALLY inside paragraphs as contextual hyperlinks. Do NOT put them in a list at the end.
Available articles to link to:
{links_text}
Format: [descriptive anchor text](relative-path)
IF NONE OF THESE ARTICLES ARE RELEVANT TO THE CURRENT TOPIC, DO NOT LINK TO ANY OF THEM.
"""

    # ============================================================
    # FASE 1: ESPECIALISTA EN CLICKBAIT ÉTICO — Genera título viral
    # ============================================================
    print(f"   🎯 [Fase 1/3] Especialista en Clickbait Ético...")
    
    lang_name = "ESPAÑOL" if lang == "es" else "ENGLISH"
    # Regla de capitalización solicitada por el editor: Capitalizar cada inicial excepto preposiciones y artículos
    cap_rule = "TITLE CASE MANDATORY: Capitalize the first letter of all major words (nouns, verbs, adjectives). DO NOT capitalize minor words like articles (el, la, los, las, un, una, a, the, an), prepositions (de, en, a, por, para, con, sin, in, on, at, for, to, with), or conjunctions (y, o, e, and, or, but) UNLESS they are the very first word of the title or subtitle. Example: 'Acciona el Pánico: La IA Amenaza 300 Millones de Euros Invertidos en Startups Españolas'."
    
    title_prompt = f"""ACT AS: Viral headline editor for TechCrunch (EN) or Xataka (ES). You write titles that DEMAND clicks.

TASK: Generate 5 candidate titles for an article about: "{meta['titulo']}"
LANGUAGE: {lang_name} ONLY. {"ABSOLUTAMENTE PROHIBIDO usar palabras en inglés excepto nombres propios (Bitcoin, ChatGPT, etc.)." if lang == "es" else ""}

RESEARCH CONTEXT (use the juiciest data points):
{research_text[:3000]}

RULES:
- Each title MUST contain a specific NUMBER, NAME, or SHOCKING CLAIM from the research
- FORBIDDEN WORDS: "crecimiento exponencial", "panorama", "landscape", "comprehensive", "overview", "deep dive", "guía completa", "todo lo que necesitas saber"
- FORBIDDEN: Titles that are questions. NO question marks allowed. Make STATEMENTS, not questions.
- TITLES MUST provoke emotion: outrage, curiosity, fear, or disbelief
- Use patterns like: "X did Y and nobody noticed", "The hidden X behind Y", "Why X is lying about Y", "X just broke: what it means for Y"
- Maximum 15 words per title. Minimum 8 words.
- {cap_rule}
- {"Los títulos deben estar COMPLETAMENTE en español. Cero spanglish." if lang == "es" else ""}

OUTPUT FORMAT (exactly 6 lines):
1. [title option 1]
2. [title option 2]
3. [title option 3]
4. [title option 4]
5. [title option 5]
BEST: [paste the single best title here]

OUTPUT ONLY THESE 6 LINES. NOTHING ELSE."""

    try:
        def fallback_title(p, s):
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=p)
            return resp.text.strip()
            
        raw_title_text = LLMRouter.route_call(title_prompt, "You are a professional headline editor for a viral tech magazine.", fallback_title, model_type="parsing")
        title_lines = raw_title_text.strip().split('\n') if raw_title_text else []
        
        # Extraer el BEST title
        viral_title = meta['titulo']  # fallback
        for line in title_lines:
            if line.strip().upper().startswith('BEST:'):
                candidate = line.split(':', 1)[1].strip().strip('"').strip("'")
                if len(candidate.split()) >= 4:
                    viral_title = candidate
                    break
        
        # Si no encontró BEST:, tomar el último título válido
        if viral_title == meta['titulo']:
            for line in reversed(title_lines):
                clean = re.sub(r'^\d+\.\s*', '', line.strip()).strip('"').strip("'")
                if len(clean.split()) >= 4 and not clean.upper().startswith('BEST'):
                    viral_title = clean
                    break
        
        meta['titulo'] = viral_title
        print(f"   ✅ [Fase 1/3] Título viral: {viral_title}")
    except Exception as e:
        print(f"   ⚠️ [Fase 1/3] Error generando título viral: {e}. Usando título original.")

    # ============================================================
    # FASE 2: REDACTOR DE DATOS DUROS — Escribir el artículo
    # Con blindaje militar anti-chatbot, anti-alucinación, anti-leak
    # ============================================================
    print(f"   ✍️ [Fase 2/3] Redactor de Datos Duros (Blindaje Militar)...")
    
    # Outline rápido (mantener la pre-digestión de datos)
    outline_prompt = f"""ACT AS: Senior Editorial Strategist for a publication like Autoblog, TechCrunch, or Xataka.
TASK: Create a CONCISE article outline for: "{meta['titulo']}"
LANGUAGE: {lang}

RESEARCH DATA:
{research_text[:8000]}

OUTPUT a structured outline with this EXACT structure:

TL;DR BULLETS (exactly 3):
- [Bullet 1: The single most important fact. Must be a complete sentence with a specific number or name. This should answer the article's core question in one line.]
- [Bullet 2: The second most surprising data point. Include the source name.]
- [Bullet 3: The practical consequence or "so what" for the reader. What changes for them.]

## [Descriptive Subtitle based on Tension/Conflict] {"(EN ESPAÑOL)" if lang == "es" else ""} (e.g. "The $200M Problem" or "El elefante en la habitación del Open Source")
- Narrative focus on technological tension, money, conflict, or failure.
- Named Entity: [MUST name at least one real person, company, or institution]
- Key data point from research with source.

## [Descriptive Subtitle based on Tension/Conflict] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Deep context and why the official corporate narrative is flawed.
- Named Entity: [different person/institution]
- Key data point from research with source.

## [Descriptive Subtitle based on Tension/Conflict] {"(EN ESPAÑOL)" if lang == "es" else ""}
- The Contrarian Crack: what the industry consensus is completely ignoring.
- Named Entity: [different person/institution]
- Key data point from research with source.

## [Descriptive Subtitle based on Tension/Conflict] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Real-world limitations, execution hurdles, or hidden costs.
- Named Entity: [different person/institution]
- Key data point from research with source.

## [Descriptive Subtitle based on Tension/Conflict] {"(EN ESPAÑOL)" if lang == "es" else ""}
- The actual impact going forward (the 'So What?'), devoid of marketing hype.
- Key data point from research with source.

## {"Nuestra lectura" if lang == "es" else "The Bottom Line"}
- Author's definitive stance (pick a side)
- One specific actionable recommendation
- Punchy closing one-liner

CRITICAL RULES:
- Section titles must be DESCRIPTIVE and SPECIFIC (e.g. "The $20K Price Cut That Changes Everything"), NEVER generic ("Section 1", "The Current Landscape").
- ONLY use facts from the RESEARCH DATA.
- Do NOT invent numbers or perform calculations.
- Every section must name at least one real person, company, or institution.
"""

    try:
        def fallback_outline(p, s):
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=p)
            return resp.text.strip()

        outline = LLMRouter.route_call(outline_prompt, "You are a specialized content researcher creating a detailed outline.", fallback_outline, model_type="research")
        print(f"   ✅ Outline: {len(outline) if outline else 0} chars")
    except Exception as e:
        print(f"   ⚠️ Outline error: {e}. Modo directo.")
        outline = ""

    outline_section = f"\n\nARTICLE OUTLINE (follow this structure strictly):\n{outline}\n" if outline else ""

    # Configurar ejemplos dinámicos por idioma y CATEGORÍA para inyectar en el prompt militar (Protocolo Camaleón)
    if lang == "es":
        if category == "fitness":
            # ── Estilo Vitónica / Fitness Revolucionario: Científico, longevidad, geroprotección ──
            ex_opening = '"Las personas que incluyen polifenoles en su dieta son las que mejor envejecen y viven más años, según los últimos estudios sobre zonas azules."'
            ex_bullets = """   * Los polifenoles actúan como "geroprotectores" naturales, ralentizando el deterioro celular al influir en los mecanismos que regulan el envejecimiento.
   * En zonas como Okinawa, el consumo de antocianinas presentes en la batata morada es clave para la salud cardiovascular de sus centenarios. 
   * La evidencia publicada en el Aging Research Reviews asocia directamente la ingesta de estos compuestos con una reducción drástica de la inflamación sistémica."""
            ex_link1 = '"Lo más interesante de estos compuestos, según explica [Vitónica](https://...), es que no solo previenen enfermedades, sino que alargan la vida saludable."'
            ex_link2 = '"Al igual que ocurre con el [aceite de oliva virgen extra](https://...), el café aporta estilbenos y ácidos fenólicos que protegen el cerebro."'
        elif category == "crypto":
            # ── Estilo BeInCrypto / CoinTelegraph ES: Institucional, frío, datos on-chain ──
            ex_opening = '"Bitdeer, con sede en Singapur y actualmente el mayor self-miner que cotiza en bolsa a nivel mundial, liquidó toda su tesorería de Bitcoin reportando cero BTC en posesión al 20 de febrero."'
            ex_bullets = """   * Bitdeer ha liquidado toda su tesorería de Bitcoin, reportando cero BTC en posesión al 20 de febrero, tras vender su producción reciente de 189.8 BTC.
   * La medida se produce mientras la dificultad de la red aumenta un 14.7% y el hashprice cae por debajo de 30 dólares por PH/s por día.
   * Para extender su runway, Bitdeer anunció una ampliación de su emisión de notas convertibles por 325 millones de dólares, acelerando su giro hacia la IA."""
            ex_link1 = '"Tras una breve recuperación causada por tormentas invernales, según [BeInCrypto](https://...), la red de Bitcoin vivió una recuperación en forma de V."'
            ex_link2 = '"Bitdeer destinará 138,2 millones de dólares a [recomprar sus notas convertibles senior](https://...) con vencimiento en 2029."'
        elif category == "viral":
            # ── Estilo Magnet/Xataka: Análisis sociológico, micro-headers, títulos magnéticos ──
            ex_opening = '"En un momento geopolítico tenso a escala mundial con varios frentes abiertos, China acaba de lograr un hito histórico: está fabricando submarinos nucleares más rápido que cualquier otro país, según un informe del IISS."'
            ex_bullets = """   * China ha superado a Estados Unidos en el ritmo de lanzamiento de submarinos nucleares: 10 unidades entre 2021-2025 frente a 7 de Washington.
   * John Phelan, secretario de Marina de EEUU, reconoció en el Congreso que "todos nuestros programas son un desastre".
   * El sorpasso amenaza la hegemonía que Washington ha mantenido bajo el agua durante décadas."""
            ex_link1 = '"China acaba de lograr un hito histórico, [según un informe del IISS](https://...), al superar a EEUU en producción de submarinos nucleares."'
            ex_link2 = '"John Phelan, secretario de Marina de EEUU, [reconocía en el Congreso](https://...) que todos sus programas llevan retraso."'
        elif category == "youtube":
            # ── Estilo Areajugones / Dexerto ES: Ritmo altísimo, citas de streamers, métricas ──
            ex_opening = '"Ibai Llanos ha confirmado la segunda edición de la Streamers Cup 3x3, el torneo de baloncesto que organiza junto a la FIBA para dar visibilidad al formato 3 contra 3."'
            ex_bullets = """   * La Streamers Cup 3x3 se celebrará el 21 de abril a las 18:00 hora española, con retransmisión en el canal de Twitch de Ibai.
   * El evento llega apenas seis meses después de la primera edición, que superó los 400.000 espectadores simultáneos.
   * Ibai confirmó la noticia con un simple "Dos eventos en una semana, al viejo estilo", señalando su vuelta a la hiperactividad de contenidos."""
            ex_link1 = '"Ibai dijo textualmente: \"Quiero que otros creadores repitan La Velada\", en [una entrevista con Dexerto](https://...)."'
            ex_link2 = '"El evento llega tras el éxito de [Disaster Chefs](https://...), que arrancó su segunda temporada esta misma semana."'
        else:
            # ── Estilo Genbeta/Xataka: Negocio tech, IA, impacto corporativo ──
            ex_opening = '"Meta acaba de cerrar una de las operaciones más llamativas del año: la compra de Manus por 2.000 millones de dólares para liderar la carrera de los agentes de IA."'
            ex_bullets = """   * La adquisición de Manus, una startup de origen chino con sede en Singapur, busca dotar a Meta de agentes capaces de ejecutar tareas complejas con mínima supervisión.
   * La operación, valorada en más de 2.000 millones de dólares, responde al cambio de paradigma: de los chatbots que hablan a los agentes que "hacen".
   * Meta integrará esta tecnología en sus servicios globales, centrándose en automatizar flujos de trabajo de oficina como análisis de datos y generación de informes autónomos."""
            ex_link1 = '"Según el análisis de [un experto en X](https://x.com/...), el movimiento de Zuckerberg no es solo talento, es una barrera geopolítica contra China."'
            ex_link2 = '"Manus saltó a la fama por ser el [primer trabajador digital autónomo](https://...), superando la barrera de los simples chatbots de [conversación generativa](https://...)."'
    else:
        if category == "fitness":
            # ── Stronger By Science / BarBend: Academic, mechanism-first ──
            ex_opening = '"Without question, creatine is the gold standard by which all strength-related supplements are judged — and the science behind it is more nuanced than most fitness influencers would have you believe."'
            ex_bullets = """   * Compared to rest, the rate of ATP demand increases up to 1,000-fold during intense exercise, making phosphocreatine the body's emergency energy currency.
   * A McMaster University study (n=40, 12 weeks) showed low-load training to failure produces comparable hypertrophy to heavy training.
   * Creatine may also promote lean body mass by directly affecting myostatin, myogenic regulatory factors, and satellite cell activation."""
            ex_link1 = '"As reviewed by [Chilibeck et al](https://ncbi.nlm.nih.gov/...), creatine may promote increases in lean body mass by directly affecting myostatin and satellite cell activation."'
            ex_link2 = '"The rate of ATP demand [increases up to 1,000-fold](https://ncbi.nlm.nih.gov/...) during intense exercise, making phosphocreatine the body\'s rapid-fire energy system."'
        elif category == "crypto":
            # ── CoinDesk / The Block: Macro-first, institutional ──
            ex_opening = '"Bitcoin see-saws around $68,000 as tariff uncertainty weighs on risk assets after President Trump raised the global tariff rate to 15% despite a Supreme Court ruling."'
            ex_bullets = """   * Bitcoin echoes 'late 2022' bear market bottom, K33 says, with on-chain metrics showing capitulation-level selling pressure.
   * ProShares' stablecoin-ready ETF sees $17 billion debut, sparking speculation about Circle's reserve strategy.
   * SEC makes quiet shift to brokers' stablecoin holdings that may pack big results for institutional adoption."""
            ex_link1 = '"Bitcoin echoes \'late 2022\' bear market bottom, [K33 says](https://...), with on-chain metrics showing capitulation."'
            ex_link2 = '"Ripple\'s Brad Garlinghouse says [CLARITY bill has \'80% chance\'](https://...) of passing by April."'
        elif category == "viral":
            # ── Vox / The Atlantic: Think-piece, narrative ──
            ex_opening = '"AI agents could change your life — if they don\'t ruin it first. ChatGPT is boring compared to what comes next."'
            ex_bullets = """   * AI's threat to white-collar jobs just got more real: you've become increasingly replaceable, according to labor economists at MIT.
   * Gadgets are getting worse and more expensive at the same time — blame AI's insatiable appetite for memory chips and data center capacity.
   * Gen Z's obsession with the 2010s isn't mere nostalgia: it's an escape mechanism from entering the workforce at the lowest real wage in 40 years."""
            ex_link1 = '"As [Vox reported](https://...), the new TikTok is freaking people out — and the censorship concerns are warranted."'
            ex_link2 = '"Claude has an 80-page \'soul document.\' As [The Atlantic explains](https://...), the real question is whether that\'s enough to make it good."'
        elif category == "youtube":
            # ── Tubefilter / Dexerto: Creator economy metrics ──
            ex_opening = '"Snapchat pledges to unlock scalable creator revenue with a new Subscriptions product — a direct response to YouTube\'s dominance in the long-form creator economy."'
            ex_bullets = """   * YouTube's 'pester power' converts kids' requests into purchases, making it the most important platform for Generation Alpha.
   * TikTok wants to use its commanding position in the recording industry to assist its podcast push — but can it stay 'In the Mix'?
   * Spotter is bringing its Showcase back to New York to build buzz around 'Creator TV', signaling the next phase of creator monetization."""
            ex_link1 = '"As [Tubefilter reported](https://...), YouTube\'s first video now belongs in a museum — \'Me at the Zoo\' is on display at the V&A."'
            ex_link2 = '"Snapchat pledges to [unlock scalable creator revenue](https://...) with a new Subscriptions product."'
        else:
            # ── TechCrunch / The Verge: Silicon Valley insider ──
            ex_opening = '"OpenAI CEO Sam Altman addressed concerns about AI\'s environmental impact this week, calling water usage claims \"completely untrue, totally insane, no connection to reality.\""'
            ex_bullets = """   * OpenAI reportedly finalizing $100B deal at more than $850B valuation, making it the most valuable private company in history.
   * Google's new Gemini Pro model has record benchmark scores — again — but the real question is whether benchmarks still matter.
   * Peak XV raises $1.3B, doubling down on AI as global VC rivalry in India heats up."""
            ex_link1 = '"Sam Altman [addressed concerns](https://...) about AI\'s environmental impact, calling water usage claims \"completely untrue.\""'
            ex_link2 = '"As [TechCrunch reported](https://...), How Ricursive Intelligence raised $335M at a $4B valuation in just 4 months."'

    # === PROMPT MILITAR ===
    anti_chatbot_shield = f"""
════════════════════════════════════════════════════
 ███ IMPORTANT OUTPUT RULES - PLEASE FOLLOW STRICTLY ███
════════════════════════════════════════════════════

🚫 ANTI-CHATBOT SHIELD:
- START the article IMMEDIATELY with a powerful opening sentence with a hard fact.
- DO NOT write introductory phrases: "Here is the article", "Aquí está el artículo", "Aquí tienes", "Sure", "Claro", "Of course", "Let me", "I'll write".
- DO NOT write meta-commentary about writing or instructions.
- The FIRST character of your output must be part of the article content.

📐 AUTOBLOG STRUCTURE (follow this EXACT layout):

1. OPENING PARAGRAPH: The very first sentence MUST be a cynical hypothesis, a contrarian perspective, or a harsh reality check. NO generic market size introductions. Start with the pain, the controversy, or the money. Max 2 sentences. Like Autoblog: {ex_opening}

2. TL;DR BULLET BLOCK (immediately after opening, NO header, NO "## Key Takeaways"):
   Write exactly 3 bullet points starting with "*". Each must be:
   - A COMPLETE, self-contained sentence that answers one key question about the topic
   - Contains at least ONE specific number, name, or date
   - Could be directly quoted by Google AI Overview as a standalone fact
   Example from Autoblog:
{ex_bullets}

3. BODY SECTIONS: Use descriptive ## H2 headers (NEVER "Section 1", "Section 2"). Then short paragraphs.

4. CLOSING: A punchy editorial one-liner. Declarative. No questions.

✂️ PARAGRAPH RULES (Autoblog standard):
- MAXIMUM 3 sentences per paragraph. If a paragraph has 4+ sentences, SPLIT IT.
- Every paragraph must introduce exactly ONE new fact or data point. No fluff.
- AVOID question marks (? and ¿). Please strictly avoid them everywhere in the article.
  BAD: "Is AI really replacing jobs?" → GOOD: "AI is already eliminating 34% of entry-level roles, according to McKinsey."
  BAD: "¿Qué significa esto?" → GOOD: "Esto implica una reducción del 40% en costos operativos."
- FORBIDDEN: Repeating the same idea. Every paragraph = new information.
- FORBIDDEN: Vague filler like "This is important because...", "It's worth noting...", "Es importante destacar..."
- Lead each paragraph with its most important fact (Inverted Pyramid).

🚫 CORPORATE FLUFF BAN & CYNICAL LEXICON MANDATE:
- NEVER use these empty words: "democratizar", "estrategia", "sinergia", "potencial", "transformar las operaciones", "fomentar la colaboración", "híbrido", "abordar desafíos".
- NEVER use AI transition words: "en conclusión", "para resumir", "en resumen", "es importante destacar", "it is important to note", "in conclusion".
- TONE MANDATE: You MUST be ruthless and critical. You MUST use cynical framing words organically in the text, such as: 'bubble' (burbuja), 'myth' (mito), 'trap' (trampa), 'failure' (fracaso), 'scam' (estafa), 'overrated' (sobrevalorado), or 'lies' (mentiras). Use them to challenge the official narrative.
- Use aggressive, precise verbs and cynical finance/tech terminology instead.

🛠️ HARDCORE TECH REQUIREMENT:
- DO NOT talk about "AI" as a magical box. You MUST mention specific infrastructure specs to prove authority: context window sizes (e.g. 1M tokens), GPU compute costs (H100/B200), API pricing paradigms, RAG bottlenecks, latency vectors, or parameter sizes.

🔢 MATH SHIELD:
- DO NOT perform any calculations. Report numbers EXACTLY as stated by sources.
- NEVER write "if we divide X by Y" or "this works out to".

🌐 LANGUAGE SHIELD:
- {"EVERY word must be in SPANISH including ALL H2/H3 headers. ZERO English words except proper nouns (ChatGPT, Bitcoin, etc.)." if lang == "es" else "EVERY word must be in ENGLISH."}
- {"DO NOT use 'Editorial Verdict'. Use 'Nuestra lectura' or 'El veredicto' IN SPANISH." if lang == "es" else ""}
- {"DO NOT leave ANY English instruction text in the output." if lang == "es" else "DO NOT leave ANY Spanish text in the output."}

🔗 LINK SHIELD (Autoblog style — links WOVEN into sentences):
- Include at least 3 outbound links woven naturally INTO sentences.
- Autoblog example: {ex_link1}
- Autoblog example: {ex_link2}
- 📌 PRIORITY: Check the section "### FUENTES VALIDADAS DISPONIBLES" at the END of the RESEARCH DATA. These URLs have been pre-verified and MUST be your primary source for outbound links. Use at least 3 of them.
- ONLY use URLs that appear VERBATIM in the RESEARCH DATA. Copy-paste the exact URL.
- If a URL is missing or cannot be used, cite the REAL publication name in simple bold (e.g. **Forbes**, **Reuters**). 
- 🚨 CRITICAL BAN: NEVER cite "Gemini Grounding", "E-E-A-T", "NotebookLM", "Context", or "Source" as a publication. You MUST extract the actual real-world media outlet name from the text. If you can't find one, do not name the source.
- 🚨 CRITICAL BAN: Do NOT use 4 asterisks like ****Name****. Use exactly two for bold: **Name**.
- 🚨 CRITICAL BAN: NEVER cite "unnamed sources", "market analysis", "technical analysis", or "legal experts" as attribution. Either name the real person/outlet or remove the attribution.
- Please do not fabricate URLs under any circumstances.
- NEVER paste a naked URL. Every URL must be inside [Anchor Text](URL) format.
- NEVER use bracket-only references like [source name] without a proper (URL).

📏 LENGTH: Minimum 1500 words. Articles under 1200 words are REJECTED.

🌐 GEO-DOMINANCE & FORMATTING:
- The 3 TL;DR bullets (described above) ARE the GEO signal. No separate "Key Takeaways" header needed.
- ZERO TABLES ALLOWED: NO Markdown tables (|---|) under ANY circumstances. They frequently break the frontend. Format any comparisons as prose or simple text.
- SPACED LISTS: Whenever you use a bulleted list (* ), ALWAYS add a blank line between each bullet point so they don't render bunched together.
- ENTITY DENSITY: Always write "Satya Nadella, CEO de Microsoft" never "el CEO". Full names everywhere.
- CITATION FORMAT: Weave source names into sentences: "Según [nombre de la fuente](URL), dato..." Never cite anonymously.
════════════════════════════════════════════════════
"""

    # === FIX 3: PRE-HOC URL INJECTION ===
    # Extract verified URLs from research data and inject them BEFORE generation
    verified_urls_block = ""
    if isinstance(contexto, dict):
        # Collect URLs from all research layers
        all_urls = []
        raw_content = contexto.get('content', '')
        # Extract URLs from research text via regex
        found_urls = re.findall(r'https?://[^\s\)\]"\'<>]+', raw_content)
        for u in found_urls:
            u = u.rstrip('.,;:')
            if u.startswith('http') and 'vertexaisearch' not in u and 'google.com/search' not in u:
                if u not in all_urls:
                    all_urls.append(u)
        
        # Also check for explicit sources list
        sources = contexto.get('sources', [])
        if isinstance(sources, list):
            for src in sources:
                if isinstance(src, dict):
                    url = src.get('url', '')
                    if url and url.startswith('http') and url not in all_urls:
                        all_urls.append(url)
        
        if all_urls:
            urls_list = "\n".join([f"  - {u}" for u in all_urls[:15]])
            verified_urls_block = f"""

### FUENTES VALIDADAS DISPONIBLES (SOLO ESTAS URLs)
Las siguientes URLs han sido PRE-VERIFICADAS y son reales.
Debes insertar obligatoriamente estos enlaces como hipervínculos Markdown (ej. [texto](url)) de forma natural en el cuerpo del artículo.
ESTÁ ABSOLUTAMENTE PROHIBIDO inventar, adivinar o fabricar URLs. Si necesitas un enlace que no está aquí, cita la fuente en texto plano con **negrita**.
{urls_list}
"""
            print(f"   🔗 [Pre-Hoc] {len(all_urls)} URLs pre-verificadas inyectadas en el prompt")

    # === FIX ENLAZADO INTERNO ===
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

    prompt = (
        f"{prompt_persona}\n"
        f"{SYSTEM_FORMAT_RULES}\n"
        f"{anti_chatbot_shield}\n"
        f"{EEAT_LINK_RULES}\n"
        f"{spiderweb_instruction}\n"
        f"WRITE ARTICLE: {meta['titulo']}\n"
        f"{outline_section}"
        f"ORIGINAL RESEARCH DATA (use as factual foundation — cite sources with links):\n{research_text}\n"
        f"{verified_urls_block}"
        f"{internal_links_block}"
        f"TEMPLATE: {structure}\n"
        f"LANG: {lang}"
    )

    # === BLINDAJE FINAL DE IDIOMA (Recency Bias) ===
    if lang == "es":
        prompt += "\n\n[🔴 DIRECTIVA FINAL CRÍTICA]: DEBES ESCRIBIR EL 100% DEL CONTENIDO DEL ARTÍCULO EN ESPAÑOL. Si escribes los párrafos en inglés, HAS FALLADO. Traduce mentalmente todos los datos de investigación antes de redactar. Los H2, los H3, los bullets, las frases, los párrafos: TODO en español. Solo los nombres propios (ChatGPT, Bitcoin, OpenAI) pueden quedar en inglés."
    else:
        prompt += "\n\n[🔴 CRITICAL FINAL DIRECTIVE]: YOU MUST WRITE 100% OF THE ARTICLE CONTENT IN ENGLISH. If you write any paragraph in Spanish, YOU FAIL. All H2s, H3s, bullets, sentences, paragraphs: ALL in English. Only proper nouns stay as-is."

    # ┌──────────────────────────────────────────────────────────┐
    # │ MOTOR INTEGRADO [Omega ES/EN] — CAPA CERO + WATERFALL    │
    # └──────────────────────────────────────────────────────────┘
    if lang == "es":
        resultado = _call_es_engine(prompt)
    else:
        resultado = _call_en_engine(prompt)
        
    # === VALIDACIÓN DE LONGITUD MÍNIMA (Ambos idiomas) ===
    word_count = len(resultado.split()) if resultado else 0
    if word_count < 1500:
        print(f"   ⚠️ [Quality] Artículo demasiado corto ({word_count} palabras). Re-enrutando para EXPANDIR...")
        extended_prompt = prompt + f"\n\nCRITICAL: The article MUST be at LEAST 1500 words. You only wrote {word_count} words! Write a comprehensive, in-depth analysis. Do NOT be brief. Expand every single section with deep analysis, data context, and expert commentary."
        
        # Usamos el router con el core del idioma correspondiente
        core_func = _call_es_engine_v3_core if lang == "es" else _call_en_engine_v3_core
        retry_result = LLMRouter.route_call(extended_prompt, "You are a professional editor expanding an article to reach 1500 words.", core_func, model_type="research")

        if retry_result and len(retry_result.split()) > word_count:
            resultado = retry_result
            print(f"   ✅ [Quality] Regenerado expandido: {len(resultado.split())} palabras")

    word_count_draft = len(resultado.split()) if resultado else 0
    print(f"   📊 [Fase 2/3] Borrador: {word_count_draft} palabras")

    # === POST-PROCESADO REGEX: Limpieza de artefactos residuales ===
    resultado = text_cleaner.clean_markdown(resultado)
    return resultado



def escribir_blueprint(tutorial_data, lang="en"):
    """Genera el post de herramienta reescribiendo con personalidad según idioma."""
    print(f"🛠️ Escribiendo Blueprint ({lang.upper()}): {tutorial_data['title']}...")
    
    prompt_base = PROMPT_BLUEPRINT_EN if lang == "en" else PROMPT_BLUEPRINT_ES
    
    prompt = prompt_base.format(
        title=tutorial_data['title'],
        transcript=tutorial_data['transcript'][:30000]
    ) + f"\n{SYSTEM_FORMAT_RULES}"
    
    # === OMEGA MATRIX: NIM/OR Waterfall para ES, Cascada para EN ===
    if lang == "es":
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        or_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        resultado = None

        if nvidia_key:
            resultado_nim, ok = _call_nvidia_nim(prompt, "z-ai/glm4.7", "", nvidia_key)
            if ok:
                return resultado_nim
        
        if not resultado and or_key:
            try:
                or_client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
                resp = or_client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.85,
                    max_tokens=4096
                )
                resultado = resp.choices[0].message.content.strip()
                if resultado and len(resultado) > 200:
                    return resultado
            except Exception as e:
                logging.warning(f"Llama-3.3-70B error en blueprint: {e}. Cayendo a Gemini...", exc_info=True)
        
        # Fallback Gemini si fallan los anteriores
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return resp.text.strip()
    else:
        return _call_en_engine(prompt)

def guardar_post(meta, contenido, lang, category, forced_image=None, translation_key=None):
    """Guarda el post con imagen validada y frontmatter blindado."""
    # Lógica Blindada de Silos: content/{lang}/{category}
    output_dir = f"content/{lang}/{category}"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = f"{output_dir}/{meta['slug']}.md"
    
    # Lógica de Imagen: Si viene forzada, se usa. Si no, se genera.
    imagen = forced_image if forced_image else get_image(meta['titulo'], contenido, meta['slug'], category)
    
    # VALIDACIÓN BLINDADA: Si la imagen es una URL externa o vacía, usar fallback local
    if not imagen or imagen.startswith("http"):
        print(f"   ⚠️ Imagen inválida detectada: '{imagen}'. Usando fallback local...")
        imagen = f"/images/defaults/default-{category}.jpg"
        print(f"   🛡️ Fallback aplicado: {imagen}")
    
    now = datetime.now()
    backdate = random.randint(15, 30) if lang == 'es' else random.randint(2, 10)
    date_str = (now - timedelta(minutes=backdate)).strftime("%Y-%m-%dT%H:%M:%S")
    # VALIDACIÓN BLINDADA: Translation Key jamás puede ser None
    if not translation_key or translation_key == "None":
        raw_hash = meta['titulo'].strip().lower()
        t_hash = hashlib.md5(raw_hash.encode('utf-8')).hexdigest()
        translation_key = f"{t_hash[:8]}-{t_hash[8:12]}-{t_hash[12:16]}-{t_hash[16:20]}-{t_hash[20:]}"

    # Generación inteligente de meta description (Fenix V3: evita descriptions genéricas)
    try:
        desc_prompt = f"Write a unique, compelling meta description of EXACTLY 140-155 characters in {'Spanish' if lang == 'es' else 'English'} for an article titled '{meta['titulo']}'. Output ONLY the description text, nothing else. No quotes around it. DO NOT use trailing ellipses (...)."
        def fallback_meta(p, s):
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=p)
            return resp.text.strip()
            
        desc_resp_text = LLMRouter.route_call(desc_prompt, "You are an SEO specialist writing meta descriptions.", fallback_meta, model_type="parsing")
        raw_desc = desc_resp_text.replace('"', "'") if desc_resp_text else meta['titulo']
        # Forzar un recorte estricto a 155 sin puntos suspensivos
        if len(raw_desc) > 155:
            clean_text = raw_desc[:155].rsplit(' ', 1)[0] + '.'
        else:
            clean_text = raw_desc if raw_desc.endswith('.') else raw_desc + '.'
    except Exception:
        clean_text = ""
    
    # Text Cleaner para resolver la descripción (anti-errores)
    clean_text = text_cleaner.sanitize_description(clean_text, contenido)
    
    # Resolver nombre legible de la categoría (FIX: config['name'] → NICHES lookup)
    niche_info = NICHES.get(category, {})
    niche_name = niche_info.get("name", category.capitalize())
    
    clean_title = meta['titulo'].replace('"', '').replace('\\$', '$').replace('\\[', '[').replace('\\]', ']')
    clean_desc = clean_text.replace('\\$', '$').replace('\\[', '[').replace('\\]', ']')
    
    # ── PROGRAMMATIC INTERNAL LINK INJECTION ──
    internal_links_footer = ""
    footer_links = LinkManager.get_latest_internal_links(lang=lang, limit=2)
    if footer_links:
        internal_links_footer += "\n\n### Artículos Relacionados\n" if lang == 'es' else "\n\n### Related Articles\n"
        for fl in footer_links:
            internal_links_footer += f"- [{fl['title']}]({fl['url']})\n"
    
    # ── PROGRAMMATIC JSON-LD INJECTION ──
    # Extraer URLs de imagen absoluta (asumiendo novumworld.com)
    abs_image = f"https://novumworld.com{imagen}" if imagen.startswith('/') else imagen
    
    # Calcular Canonical URL
    if lang == 'es':
        canonical_url = f"https://novumworld.com/es/{category}/{meta['slug']}/"
    else:
        canonical_url = f"https://novumworld.com/{category}/{meta['slug']}/"
    
    json_ld = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{clean_title}",
  "description": "{clean_desc}",
  "image": "{abs_image}",
  "datePublished": "{date_str}",
  "author": {{
    "@type": "Organization",
    "name": "NovumWorld Editorial Team"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "NovumWorld",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://novumworld.com/images/logo.png"
    }}
  }}
}}
</script>
"""
    # ── PROGRAMMATIC E-E-A-T AUTHORSHIP & DISCLAIMERS ──
    # Caja de Autoría
    author_box = f"""
---

<div class="author-box" style="padding: 20px; background-color: #f8f9fa; border-left: 4px solid #0056b3; margin-top: 30px; border-radius: 4px;">
    {("<h4>✍️ Sobre el Analista</h4><p><strong>NovumWorld Financial Intelligence</strong> es un equipo de expertos en mercados dedicados a decodificar tendencias institucionales y flujos de capital. Nuestros reportes cruzan datos on-chain y macroeconomía para ofrecer proyecciones libres de ruido corporativo.</p>" if lang == 'es' else "<h4>✍️ About the Analyst</h4><p><strong>NovumWorld Financial Intelligence</strong> is a team of market experts dedicated to decoding institutional trends and capital flows. Our reports cross-reference on-chain data and macroeconomics to deliver noise-free projections.</p>")}
</div>
""" if category in ['crypto', 'funds', 'stocks'] else ""

    # Disclaimer Financiero (YMYL)
    yml_disclaimer = f"""
> [!CAUTION]
> **{("Aviso de Riesgo y Exención de Responsabilidad" if lang == 'es' else "Risk Warning & Disclaimer")}:** {("El contenido expuesto tiene carácter puramente educativo e informativo. No constituye asesoramiento financiero, legal ni recomendación de inversión. Opere bajo su propio riesgo y consulte a un profesional certificado." if lang == 'es' else "The content provided is strictly for educational and informational purposes. It does not constitute financial, legal, or investment advice. Trade at your own risk and consult a certified professional.")}
""" if category in ['crypto', 'funds', 'stocks'] else ""

    # Agregar Disclaimers, Cajas de Autor, Footer Links y JSON-LD al contenido
    contenido_enrich = contenido.strip() + "\n\n" + yml_disclaimer.strip() + "\n" + author_box.strip() + "\n" + internal_links_footer + "\n\n" + json_ld.strip()

    # Frontmatter YAML original
    front_matter = f"""---
title: "{clean_title}"
date: {date_str}
draft: false
description: "{clean_desc}"
featured_image: "{imagen}"
slug: "{meta['slug']}"
canonical: "{canonical_url}"
tags: ["{niche_name}"]
categories: ["{category}"]
type: "{category}"
language: "{lang}"
translationKey: "{translation_key}"
---
"""
    
    # VALIDACIÓN ESTRICTA DEL YAML ANTES DE GUARDADO (P0)
    import yaml
    try:
        # Aislar bloque YAML y parsear
        yaml_content = front_matter.strip().strip('-').strip()
        yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        print(f"   🚨 [YAML ERROR] Se detectó bloque corrupto: {e}. Auto-regenerando para evitar Ghost Article...")
        safe_meta = {
            "title": clean_title,
            "date": date_str,
            "draft": False,
            "description": clean_desc,
            "featured_image": imagen,
            "slug": meta['slug'],
            "canonical": canonical_url,
            "tags": [niche_name],
            "categories": [category],
            "type": category,
            "language": lang,
            "translationKey": translation_key
        }
        yaml_str = yaml.dump(safe_meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
        front_matter = f"---\n{yaml_str}---\n"

    clean_titulo = meta['titulo'].replace('\"', '')
    final_content = f"{front_matter}\n![{clean_titulo}]({imagen})\n\n{contenido_enrich}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"✅ Guardado: {filepath}")
    
    # ⚡ NOTIFICACIÓN FAST-TRACK A GOOGLE INDEXING API
    if lang == 'es':
        final_url = f"https://novumworld.com/es/{category}/{meta['slug']}/"
    else:
        final_url = f"https://novumworld.com/{category}/{meta['slug']}/"
    indexing_api.notify_google(final_url)

def guardar_fuentes(slug, sources):
    """
    Link Deposit: Guarda las fuentes E-E-A-T encontradas durante la fase de investigación
    para que el Corrector (QA Editor) pueda inyectarlas si el artículo fue generado sin enlaces.
    """
    if not sources:
        return
        
    try:
        os.makedirs("data", exist_ok=True)
        file_path = "data/source_links.json"
        
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                    
        data[slug] = sources
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"   📦 [Link Deposit] {len(sources)} fuentes guardadas para el slug '{slug}'")
    except Exception as e:
        print(f"   ⚠️ [Link Deposit] Error guardando fuentes: {e}")

