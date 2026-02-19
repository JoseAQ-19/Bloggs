import os
import json
import re
import time
import random
import argparse
import urllib.parse
from datetime import datetime, timedelta
import unicodedata
from dotenv import load_dotenv

# Cargar variables de entorno (Prioridad .env)
load_dotenv()

from google import genai
from google.genai import types

# Importar Módulos Propios
import researcher
import trend_hunter 
import tools_hunter 
from utils import SlugManager 
from novum_visual import get_image 
# Importar Prompts Bilingües
try:
    from prompts_tools import PROMPT_BLUEPRINT_EN, PROMPT_BLUEPRINT_ES
except ImportError:
    # Fallback por si acaso
    PROMPT_BLUEPRINT_EN = "ACT AS TECH GURU..."
    PROMPT_BLUEPRINT_ES = "ACTUA COMO ESTRATEGA..."

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY.")
    client = None

# --- SYSTEM PROMPT GLOBAL (Fenix V3 Anti-AI) ---
SYSTEM_FORMAT_RULES = """
CRITICAL FORMATTING RULES (ZERO TOLERANCE — VIOLATION = ARTICLE REJECTED):

1. NO TITLE REPETITION: Do NOT include the article title or H1 at the beginning.
2. START IMMEDIATELY: Start with the Hook paragraph directly.
3. FORBIDDEN PHRASES (INSTANT REJECTION IF FOUND):
   - English: "TL;DR", "Key Takeaways", "In summary", "In conclusion", "It remains to be seen", "In the ever-evolving", "It's worth noting", "Navigating the complexities"
   - Spanish: "En resumen", "En conclusión", "En última instancia", "En el vertiginoso", "Cabe destacar", "Un arma de doble filo", "Queda por ver"
4. HEADERS: Use H2 (##) for main sections. NEVER use H1 (#).
5. OUTBOUND LINKS (MANDATORY — MINIMUM 3):
   Include at least 3 hyperlinks to REAL external authoritative sources in markdown format.
   Examples: academic papers, official reports, established news outlets (Reuters, Bloomberg, TechCrunch, ArsTechnica, PubMed).
   Format: [descriptive anchor text](https://real-verified-url.com)
   NEVER fabricate or hallucinate URLs. Only link to sources you are confident exist.
6. UNIQUE DATA POINT (MANDATORY — MINIMUM 1):
   Include at least ONE original comparative calculation, metric, or data insight that adds information gain.
   Example: "If we divide Meta's $70B investment by Horizon's 200K monthly users, that's $350,000 per user — more expensive than a median US house."
   The reader must learn something they CANNOT find in any other article.
7. PARAGRAPH LENGTH VARIATION (MANDATORY):
   Paragraphs MUST vary between 1 and 6 sentences. Include at least:
   - One single-sentence paragraph for dramatic effect
   - One longer analytical paragraph (5-6 sentences)
   UNIFORM paragraph length is FORBIDDEN.
8. NO CONSTANT BULLET LISTS:
   Do NOT use bullet point lists in every section. Maximum ONE bulleted list per article.
   Prefer narrative prose, numbered steps, comparison tables, or Q&A format.
9. PERSONAL VOICE (MANDATORY):
   Include at least ONE editorial hot take, personal opinion, or rhetorical question that shows genuine author personality.
   The article must NOT read like a Wikipedia summary.
10. LANGUAGE PURITY:
    If writing in Spanish, ALL text must be in Spanish. No Spanglish, no untranslated English headers.
    If writing in English, ALL text must be in English.
"""

# --- CONFIGURACIÓN DE NICHOS ---
NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news",
        "prompt_es": """ROL: Desarrollador Senior y Analista de SaaS. TONO: Técnico pero accesible.""",
        "prompt_en": """ROLE: Senior Developer & SaaS Analyst. TONE: Technical yet accessible."""
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed study",
        "prompt_es": """ROL: Entrenador Basado en Evidencia. TONO: Motivador, científico.""",
        "prompt_en": """ROLE: Evidence-Based Coach. TONE: Motivational, scientific."""
    },
    "crypto": {
        "name": "Crypto & Web3",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency technical analysis DeFi blockchain finance news",
        "prompt_es": """ROL: Inversor de Wall Street. TONO: Analítico, urgente.""",
        "prompt_en": """ROLE: Wall Street Investor. TONE: Analytical, urgent."""
    },
    "youtube": {
        "name": "Creator Economy",
        "output_dir": "content/youtube",
        "search_context": "creator economy youtube algorithm twitch stats influencer business",
        "prompt_es": """ROL: Estratega Digital. TONO: Analítico, enfocado en negocio.""",
        "prompt_en": """ROLE: Digital Strategist. TONE: Business-focused."""
    },
    "viral": {
        "name": "Viral & Trends",
        "output_dir": "content/viral",
        "search_context": "viral internet trends reddit twitter drama pop culture",
        "prompt_es": """ROL: Redactor Revista Digital. TONO: Emocional, curioso.""",
        "prompt_en": """ROLE: Senior Digital Editor. TONE: Emotional, engaging."""
    },
    "tools": {
        "name": "Novum Tools",
        "output_dir": "content/tools",
        "search_context": "tutorial guide"
    }
}

STRUCTURE_TEMPLATES = {
    'type_a': "INVESTIGATIVE JOURNALISM: Strong Opening Hook -> H2 Context & Background -> H2 Deep Analysis with Data -> H2 Expert Perspectives -> Final Editorial Take",
    'type_b': "NARRATIVE ESSAY: Personal Anecdote or Provocation -> The Core Problem (with numbers) -> Historical Parallel or Case Study -> Contrarian View -> Author's Verdict",
    'type_c': "DATA-DRIVEN REPORT: Striking Statistic Opening -> H2 The Numbers (tables/comparisons) -> H2 What It Means (analysis) -> H2 What Comes Next (prediction)",
    'type_d': "DEBATE FORMAT: Thesis Statement -> H2 The Case For -> H2 The Case Against -> H2 The Uncomfortable Truth -> Short Closing Provocation"
}

COMPLETED_FILE = 'data/completed.txt'

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
    
    with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
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
        
        if similarity > 0.6:
            print(f"  ⚠️ REDUNDANCY: '{new_topic}' overlaps {similarity*100:.0f}% with '{existing_topic}'")
            return True
    
    return False

def safety_check(topic):
    try:
        prompt = f"ACT AS: AdSense Moderator. TOPIC: '{topic}'. OUTPUT: SAFE or UNSAFE."
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        if "UNSAFE" in resp.text.strip().upper():
            return False
        return True
    except:
        return True

def planificar_articulo(tema, contexto, lang, category_config):
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    lang_instruction = (
        f"\n\nCRITICAL LANGUAGE RULE: The 'titulo' MUST be written ENTIRELY in {'SPANISH (Español)' if lang == 'es' else 'ENGLISH'}. "
        f"{'Do NOT use any English words in the title except proper nouns (brand names like Bitcoin, NBA, etc.).' if lang == 'es' else 'Do NOT use any Spanish words in the title.'} "
        f"VIOLATION = INSTANT REJECTION."
    )
    prompt = f"{prompt_persona}\n{SYSTEM_FORMAT_RULES}{lang_instruction}\nACT LIKE EDITOR. Topic: {tema}\nContext: {contexto[:1000]}\nLanguage: {lang}\nSTRICT JSON: {{ \"titulo\": \"...\", \"slug_sugerido\": \"...\" }}"
    try:
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
        plan = json.loads(resp.text.replace('```json', '').replace('```', '').strip())
        suffix = "-en" if lang == "en" else ""
        plan['slug'] = SlugManager.generate(plan['slug_sugerido']) + suffix
        return plan
    except:
        return {"titulo": f"{tema} Analysis", "slug": SlugManager.generate(tema) + ("-en" if lang=="en" else "")}

def escribir_articulo(meta, contexto, lang, category_config):
    print(f"✍️ Escribiendo ({lang}): {meta['titulo']}...")
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    structure = random.choice(list(STRUCTURE_TEMPLATES.values()))
    prompt = f"{prompt_persona}\n{SYSTEM_FORMAT_RULES}\nWRITE ARTICLE: {meta['titulo']}\nCONTEXT: {contexto}\nTEMPLATE: {structure}\nLANG: {lang}"
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return resp.text.strip()

def escribir_blueprint(tutorial_data, lang="en"):
    """Genera el post de herramienta reescribiendo con personalidad según idioma."""
    print(f"🛠️ Escribiendo Blueprint ({lang.upper()}): {tutorial_data['title']}...")
    
    prompt_base = PROMPT_BLUEPRINT_EN if lang == "en" else PROMPT_BLUEPRINT_ES
    
    prompt = prompt_base.format(
        title=tutorial_data['title'],
        transcript=tutorial_data['transcript'][:30000]
    ) + f"\n{SYSTEM_FORMAT_RULES}"
    
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return resp.text.strip()

def guardar_post(meta, contenido, lang, category, forced_image=None, translation_key=None):
    """Guarda el post con imagen validada y frontmatter blindado."""
    # Lógica Blindada de Silos: content/{lang}/{category}
    output_dir = f"content/{lang}/{category}"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = f"{output_dir}/{meta['slug']}.md"
    
    # Lógica de Imagen: Si viene forzada, se usa. Si no, se genera.
    imagen = forced_image if forced_image else get_image(meta['titulo'], meta['slug'], category)
    
    # VALIDACIÓN BLINDADA: Si la imagen es una URL externa o vacía, usar fallback local
    if not imagen or imagen.startswith("http"):
        print(f"   ⚠️ Imagen inválida detectada: '{imagen}'. Usando fallback local...")
        imagen = f"/images/defaults/default-{category}.jpg"
        print(f"   🛡️ Fallback aplicado: {imagen}")
    
    now = datetime.now()
    backdate = random.randint(15, 30) if lang == 'es' else random.randint(2, 10)
    date_str = (now - timedelta(minutes=backdate)).strftime("%Y-%m-%dT%H:%M:%S")
    # Generación inteligente de meta description (Fenix V3: evita descriptions genéricas)
    try:
        desc_prompt = f"Write a unique, compelling meta description of EXACTLY 140-155 characters in {'Spanish' if lang == 'es' else 'English'} for an article titled '{meta['titulo']}'. Output ONLY the description text, nothing else. No quotes around it."
        desc_resp = client.models.generate_content(model='gemini-2.0-flash', contents=desc_prompt)
        clean_text = desc_resp.text.strip()[:160].replace('"', "'")
    except Exception:
        clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ').replace('"', "'") + "..."
    
    # Resolver nombre legible de la categoría (FIX: config['name'] → NICHES lookup)
    niche_info = NICHES.get(category, {})
    niche_name = niche_info.get("name", category.capitalize())
    
    # Frontmatter YAML limpio y validado
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {date_str}
draft: false
description: "{clean_text}"
featured_image: "{imagen}"
tags: ["{niche_name}"]
categories: ["{category}"]
type: "{category}"
language: "{lang}"
translationKey: "{translation_key}"
---

![{meta['titulo'].replace('"', '')}]({imagen})

{contenido}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    print(f"✅ Guardado: {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True, help='Category or tools')
    args = parser.parse_args()
    cat = args.category.lower()
    
    # --- MODO TOOLS ---
    if cat == "tools":
        print("🚀 INICIANDO BLUEPRINT ENGINE")
        
        # SIEMPRE "IA" para herramientas técnicas como Make.com
        target_niche = "ia" 
        print(f"🎲 Nicho forzado para prueba: {target_niche}")
        
        # Buscamos "Make.com automation" explícitamente en esta prueba para garantizar calidad
        tutorial = tools_hunter.ToolsHunter.get_tutorial_content("Make.com automation")
        
        if not tutorial:
            print("💤 No tutorial found.")
            return
            
        # 1. GENERACIÓN DE IMAGEN MAESTRA (ÚNICA)
        print(f"🎨 Generando Imagen Maestra para: {tutorial['title']}...")
        master_slug = SlugManager.generate(tutorial['title'])
        # Usamos nicho 'tools' o 'ia' para el estilo visual
        master_image = get_image(tutorial['title'], master_slug, "tools")
            
        # 2. Generación Bilingüe
        for lang in ["en", "es"]:
            texto = escribir_blueprint(tutorial, lang)
            
            # Título Inteligente (IA)
            prompt_title = f"GENERATE A CLICKBAIT TITLE IN {lang.upper()} FOR: {tutorial['title']}. OUTPUT ONLY THE TITLE TEXT. NO 'Option 1'."
            resp_title = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_title)
            
            # Sanitización estricta (Python layer)
            raw_title = resp_title.text.strip().split('\n')[0]
            final_title = SlugManager.sanitize(raw_title)
            
            slug = SlugManager.generate(final_title)
            
            meta = {"titulo": final_title, "slug": slug}
            # INYECCIÓN DE IMAGEN MAESTRA
            guardar_post(meta, texto, lang, "tools", forced_image=master_image)
            
        return

    # --- MODO STANDARD ---
    if cat not in NICHES:
        print(f"❌ Categoría inválida.")
        return

    print(f"🚀 INICIANDO PENTAGON: {NICHES[cat]['name']}")
    tema = trend_hunter.TrendHunter.get_trend(cat)
    if not tema or not safety_check(tema): return
    
    # --- FENIX V3: BLOQUEO DE REDUNDANCIA ---
    if is_topic_redundant(tema, cat):
        print(f"🚫 TOPIC BLOCKED BY REDUNDANCY CHECK: '{tema}'. Skipping.")
        return
    
    print(f"🎯 TEMA: {tema}")
    res = researcher.Researcher()
    contexto = res.research_topic(f"{tema} {NICHES[cat]['search_context']}")
    
    # Generar Translation Key única para este par de artículos
    import uuid
    trans_key = str(uuid.uuid4())
    
    for lang in ["es", "en"]:
        meta = planificar_articulo(tema, contexto, lang, NICHES[cat])
        texto = escribir_articulo(meta, contexto, lang, NICHES[cat])
        guardar_post(meta, texto, lang, cat, translation_key=trans_key)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
