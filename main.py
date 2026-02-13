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
import tools_hunter # NUEVO
from utils import SlugManager 
from novum_visual import get_image 

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY.")
    client = None

# --- SYSTEM PROMPTS ---
SYSTEM_FORMAT_RULES = """
CRITICAL FORMATTING RULES:
1. NO TITLE REPETITION: Do NOT include the article title or H1 at the beginning. The website renders it automatically.
2. START IMMEDIATELY: Start with the TL;DR or the Hook paragraph directly.
3. HEADERS: Use H2 (##) for main sections. NEVER use H1 (#).
4. NO AI FLUFF: Do not use "In conclusion", "It is important to note".
"""

PROMPT_BLUEPRINT = """
ACT COMO: Senior Technical Writer & DevOps Engineer.
TASK: Convert this raw YouTube transcript into a Professional 'Novum Blueprint' Tutorial.

SOURCE VIDEO: "{title}"
TRANSCRIPT RAW:
{transcript}

STRUCTURE (MANDATORY):
1. **The Problem:** Clear explanation of what we are solving.
2. **The Stack:** List of tools/software required.
3. **The Blueprint (Step-by-Step):** Detailed instructions. Use code blocks for scripts.
4. **Pro Tips:** Advanced optimization advice.

RULES:
- Clean up spoken language. Make it concise documentation.
- NO "In this video", "Subscribe", or "Smash the like button".
- Use Markdown headers (##).
- TONE: Professional, technical, zero fluff.
"""

# --- CONFIGURACIÓN DE NICHOS ---
NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news",
        "prompt_es": "ROL: Desarrollador Senior y Analista de SaaS. TONO: Técnico pero accesible.",
        "prompt_en": "ROLE: Senior Developer & SaaS Analyst. TONE: Technical yet accessible."
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed study",
        "prompt_es": "ROL: Entrenador Basado en Evidencia. TONO: Motivador, científico.",
        "prompt_en": "ROLE: Evidence-Based Coach. TONE: Motivational, scientific."
    },
    "crypto": {
        "name": "Crypto & Web3",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency technical analysis DeFi blockchain finance news",
        "prompt_es": "ROL: Inversor de Wall Street. TONO: Analítico, urgente.",
        "prompt_en": "ROLE: Wall Street Investor. TONE: Analytical, urgent."
    },
    "youtube": {
        "name": "Creator Economy",
        "output_dir": "content/youtube",
        "search_context": "creator economy youtube algorithm twitch stats influencer business",
        "prompt_es": "ROL: Estratega Digital. TONO: Analítico, enfocado en negocio.",
        "prompt_en": "ROLE: Digital Strategist. TONE: Business-focused."
    },
    "viral": {
        "name": "Viral & Trends",
        "output_dir": "content/viral",
        "search_context": "viral internet trends reddit twitter drama pop culture",
        "prompt_es": "ROL: Redactor Revista Digital. TONO: Emocional, curioso.",
        "prompt_en": "ROLE: Senior Digital Editor. TONE: Emotional, engaging."
    },
    "tools": {
        "name": "Novum Tools",
        "output_dir": "content/tools",
        "search_context": "tutorial guide"
    }
}

STRUCTURE_TEMPLATES = {
    'type_a': "PERIODISTIC: TL;DR -> Intro -> H2 Analysis -> H2 Impact -> Conclusion",
    'type_b': "STORYTELLING: Personal Hook -> The Problem -> The Deep Dive -> The Solution",
    'type_c': "LISTICLE: Rapid Intro -> 5 Key Points (Numbered) -> Final Verdict"
}

COMPLETED_FILE = 'data/completed.txt'

def safety_check(topic):
    print(f"👮‍♂️ Safety Check: {topic}...")
    try:
        prompt = f"ACT AS: AdSense Moderator. TOPIC: '{topic}'. OUTPUT: SAFE or UNSAFE."
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        if "UNSAFE" in resp.text.strip().upper():
            print(f"🚨 BLOQUEADO: {topic}")
            return False
        return True
    except:
        return True

def planificar_articulo(tema, contexto, lang, category_config):
    print(f"🏗️ Planificando ({lang}) - Nicho: {category_config['name']}...")
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    prompt = f"{prompt_persona}\n{SYSTEM_FORMAT_RULES}\nACT LIKE EDITOR. Topic: {tema}\nContext: {contexto[:1000]}\nSTRICT JSON: {{ \"titulo\": \"...\", \"slug_sugerido\": \"...\" }}"
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

def escribir_blueprint(tutorial_data):
    """
    Si el contenido ya viene de SurfSense (Markdown limpio), lo devuelve.
    Si fuera transcript sucio, lo procesaría con Gemini.
    """
    transcript = tutorial_data.get('transcript', '')
    
    # Detección simple: Si tiene estructura Markdown clara (H1, H2), asumimos que está listo
    if "# " in transcript and "## " in transcript:
        print("✅ Contenido de SurfSense detectado. Saltando reescritura Gemini (Ahorro de costes).")
        return transcript

    print(f"🛠️ Escribiendo Blueprint con Gemini: {tutorial_data['title']}...")
    prompt = PROMPT_BLUEPRINT.format(
        title=tutorial_data['title'],
        transcript=transcript[:25000]
    ) + f"\n{SYSTEM_FORMAT_RULES}"
    
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return resp.text.strip()

def guardar_post(meta, contenido, lang, category):
    config = NICHES.get(category, NICHES['ia']) # Fallback safe
    output_dir = config.get('output_dir', f'content/{category}')
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = f"{output_dir}/{meta['slug']}.md"
    imagen = get_image(meta['titulo'], meta['slug'], category)
    
    now = datetime.now()
    backdate = random.randint(15, 30) if lang == 'es' else random.randint(2, 10)
    date_str = (now - timedelta(minutes=backdate)).strftime("%Y-%m-%dT%H:%M:%S")
    clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ') + "..."
    
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {date_str}
draft: false
description: "{clean_text}"
featured_image: "{imagen}"
tags: ["{config['name']}", "Tutorials", "Blueprints"]
categories: ["{category}"]
type: "{category}"
language: "{lang}"
---

![{meta['titulo']}]({imagen})

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
        target_niche = random.choice(["ia", "crypto", "youtube", "fitness", "viral"])
        print(f"🎲 Nicho objetivo: {target_niche}")
        
        tutorial = tools_hunter.ToolsHunter.get_tutorial_content(target_niche)
        if not tutorial:
            print("💤 No tutorial found.")
            return
            
        texto = escribir_blueprint(tutorial)
        meta = {"titulo": f"Guide: {tutorial['title']}", "slug": SlugManager.generate(tutorial['title'])}
        guardar_post(meta, texto, "en", "tools")
        return

    # --- MODO STANDARD ---
    if cat not in NICHES:
        print(f"❌ Categoría inválida.")
        return

    print(f"🚀 INICIANDO PENTAGON: {NICHES[cat]['name']}")
    tema = trend_hunter.TrendHunter.get_trend(cat)
    if not tema or not safety_check(tema): return
    
    print(f"🎯 TEMA: {tema}")
    res = researcher.Researcher()
    contexto = res.research_topic(f"{tema} {NICHES[cat]['search_context']}")
    
    for lang in ["es", "en"]:
        meta = planificar_articulo(tema, contexto, lang, NICHES[cat])
        texto = escribir_articulo(meta, contexto, lang, NICHES[cat])
        guardar_post(meta, texto, lang, cat)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
