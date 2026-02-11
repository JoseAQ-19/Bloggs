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
from utils import SlugManager 
from novum_visual import get_image 

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY.")
    client = None

# --- SYSTEM PROMPT GLOBAL (CLEAN FORMAT) ---
# Se inyecta la personalidad específica después, pero estas reglas son base.
SYSTEM_FORMAT_RULES = """
CRITICAL FORMATTING RULES:
1. NO TITLE REPETITION: Do NOT include the article title or H1 at the beginning. The website renders it automatically.
2. START IMMEDIATELY: Start with the TL;DR or the Hook paragraph directly.
3. HEADERS: Use H2 (##) for main sections. NEVER use H1 (#).
4. NO AI FLUFF: Do not use "In conclusion", "It is important to note".
"""

# --- CONFIGURACIÓN DE NICHOS ---
NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news",
        "prompt_es": """
            ROL: Desarrollador Senior y Analista de SaaS.
            TONO: Técnico pero accesible. Crítico con el hype.
            MISIÓN: Analizar herramientas, modelos de negocio y benchmarks de IA.
        """,
        "prompt_en": """
            ROLE: Senior Developer & SaaS Analyst.
            TONE: Technical yet accessible. Critical of hype.
            MISSION: Analyze AI tools, benchmarks, and micro-SaaS opportunities.
        """
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed study",
        "prompt_es": """
            ROL: Entrenador Basado en Evidencia y Biohacker.
            TONO: Motivador, científico y directo.
            MISIÓN: Desmentir bro-science. Citar estudios (PubMed/ScienceDirect).
        """,
        "prompt_en": """
            ROLE: Evidence-Based Coach & Biohacker.
            TONE: Motivational, scientific, direct.
            MISSION: Debunk bro-science. Cite studies (PubMed).
        """
    },
    "crypto": {
        "name": "Crypto & Web3",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency technical analysis DeFi blockchain finance news",
        "prompt_es": """
            ROL: Inversor de Wall Street experto en Blockchain.
            TONO: Analítico, urgente, financiero.
            MISIÓN: Análisis técnico, fundamental y de mercado. Detectar gemas y estafas.
        """,
        "prompt_en": """
            ROLE: Wall Street Investor & Blockchain Expert.
            TONE: Analytical, urgent, financial.
            MISSION: Technical and fundamental analysis. Spotting gems and scams.
        """
    },
    "youtube": {
        "name": "Creator Economy",
        "output_dir": "content/youtube",
        "search_context": "creator economy youtube algorithm twitch stats influencer business",
        "prompt_es": """
            ROL: Estratega Digital de la Creator Economy.
            TONO: Analítico, enfocado en el negocio y las métricas.
            MISIÓN: Deconstruir el éxito de YouTubers, cambios de algoritmo y monetización.
        """,
        "prompt_en": """
            ROLE: Digital Strategist & Creator Economy Analyst.
            TONE: Business-focused, metrics-driven.
            MISSION: Deconstruct YouTuber success, algo changes, and monetization.
        """
    },
    "viral": {
        "name": "Viral & Trends",
        "output_dir": "content/viral",
        "search_context": "viral internet trends reddit twitter drama pop culture",
        "prompt_es": """
            ROL: Redactor Senior de Revista Digital (Estilo Vice/BuzzFeed).
            TONO: Emocional, curioso, enganchante (Clicky).
            MISIÓN: Explicar el drama o la tendencia del momento.
        """,
        "prompt_en": """
            ROLE: Senior Digital Magazine Editor (Vice/BuzzFeed style).
            TONE: Emotional, curious, engaging (Clicky).
            MISSION: Explain the current drama or trend.
        """
    }
}

STRUCTURE_TEMPLATES = {
    'type_a': "PERIODISTIC: TL;DR -> Intro -> H2 Analysis -> H2 Impact -> Conclusion",
    'type_b': "STORYTELLING: Personal Hook -> The Problem -> The Deep Dive -> The Solution",
    'type_c': "LISTICLE: Rapid Intro -> 5 Key Points (Numbered) -> Final Verdict"
}

COMPLETED_FILE = 'data/completed.txt'

def safety_check(topic):
    """Filtro de seguridad AdSense."""
    print(f"👮‍♂️ Safety Check: {topic}...")
    try:
        prompt = f"""
        ACT AS: AdSense Moderator.
        TOPIC: "{topic}"
        TASK: Classify as SAFE or UNSAFE for advertising.
        CRITERIA: Hate speech, adult content, graphic violence, illegal drugs.
        OUTPUT: Only one word: SAFE or UNSAFE.
        """
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        verdict = resp.text.strip().upper()
        if "UNSAFE" in verdict:
            print(f"🚨 TEMA BLOQUEADO: {topic}")
            return False
        return True
    except:
        return True 

def planificar_articulo(tema, contexto, lang, category_config):
    print(f"🏗️ Planificando ({lang.upper()}) - Nicho: {category_config['name']}...")
    
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    
    prompt = f"""
    {prompt_persona}
    {SYSTEM_FORMAT_RULES}
    
    ACT LIKE AN EDITOR IN CHIEF.
    Topic: "{tema}"
    Context: "{contexto[:1500]}..."
    Language: {lang.upper()}
    
    TASK: Create metadata for a definitive article.
    STRICT JSON OUTPUT: {{ "titulo": "...", "slug_sugerido": "..." }}
    """
    
    try:
        resp = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        plan = json.loads(resp.text.replace('```json', '').replace('```', '').strip())
        suffix = "-en" if lang == "en" else ""
        plan['slug'] = SlugManager.generate(plan['slug_sugerido']) + suffix
        return plan
    except Exception as e:
        print(f"⚠️ Fallo planificación: {e}")
        return {"titulo": f"{tema} Analysis", "slug": SlugManager.generate(tema) + ("-en" if lang=="en" else "")}

def escribir_articulo(meta, contexto, lang, category_config):
    print(f"✍️ Escribiendo ({lang.upper()}): {meta['titulo']}...")
    
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    structure = random.choice(list(STRUCTURE_TEMPLATES.values()))
    
    prompt = f"""
    {prompt_persona}
    {SYSTEM_FORMAT_RULES}
    
    WRITE A COMPLETE ARTICLE ABOUT: "{meta['titulo']}".
    CONTEXT: {contexto}
    STRUCTURE TEMPLATE: {structure}
    LENGTH: 1200-1500 words.
    LANGUAGE: {lang.upper()}
    """
    
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return resp.text.strip()

def guardar_post(meta, contenido, lang, category):
    config = NICHES[category]
    output_dir = config['output_dir']
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
tags: ["{config['name']}", "Trends"]
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
    parser.add_argument('--category', type=str, required=True, help='Category: ia, fitness, crypto, youtube, viral')
    args = parser.parse_args()
    
    cat = args.category.lower()
    if cat not in NICHES:
        print(f"❌ Categoría '{cat}' no válida.")
        return

    print(f"🚀 INICIANDO NOVUM-PENTAGON: {NICHES[cat]['name']}")
    
    print(f"🏹 Cazando tendencia para: {cat}...")
    tema = trend_hunter.TrendHunter.get_trend(cat)
    
    if not tema:
        print("💤 No se encontró tendencia. Abortando.")
        return

    if not safety_check(tema):
        print("🛡️ Tema inseguro detectado. Activando protocolo de evasión (Backup).")
        return 

    print(f"🎯 TEMA VALIDADO: {tema}")
    
    search_query = f"{tema} {NICHES[cat]['search_context']}"
    res = researcher.Researcher()
    contexto = res.research_topic(search_query) 
    
    for lang in ["es", "en"]:
        meta = planificar_articulo(tema, contexto, lang, NICHES[cat])
        texto = escribir_articulo(meta, contexto, lang, NICHES[cat])
        guardar_post(meta, texto, lang, cat)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
