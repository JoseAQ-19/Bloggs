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
from utils import SlugManager, ImageManager

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY. El cliente de Gemini no funcionará a menos que se inyecte manualmente.")
    client = None

# --- CONFIGURACIÓN DE NICHOS (EL PENTÁGONO) ---
NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "keywords_file": "data/keywords_ia.txt",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news",
        "prompt_es": """
            ROL: Desarrollador Senior y Analista de SaaS.
            TONO: Técnico pero accesible. Crítico con el hype, centrado en la utilidad real y el código.
            MISIÓN: Analizar herramientas, modelos de negocio y benchmarks de IA.
            ESTILO: Usa jerga dev (API, deploy, latency) pero explícala.
        """,
        "prompt_en": """
            ROLE: Senior Developer & SaaS Analyst.
            TONE: Technical yet accessible. Critical of hype, focused on real utility and business models.
            MISSION: Analyze AI tools, benchmarks, and micro-SaaS opportunities.
            STYLE: Use dev jargon (API, deploy, latency) appropriately.
        """
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "keywords_file": "data/keywords_fitness.txt",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed study",
        "prompt_es": """
            ROL: Entrenador Basado en Evidencia y Biohacker.
            TONO: Motivador, científico y directo.
            MISIÓN: Desmentir bro-science. Citar estudios (PubMed/ScienceDirect).
            ESTILO: Datos duros, protocolos claros, enfoque en longevidad y rendimiento.
        """,
        "prompt_en": """
            ROLE: Evidence-Based Coach & Biohacker.
            TONE: Motivational, scientific, direct.
            MISSION: Debunk bro-science. Cite studies (PubMed).
            STYLE: Hard data, clear protocols, focus on longevity and performance.
        """
    },
    "crypto": {
        "name": "Crypto & Web3",
        "keywords_file": "data/keywords_crypto.txt",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency technical analysis DeFi blockchain finance news",
        "prompt_es": """
            ROL: Inversor de Wall Street experto en Blockchain.
            TONO: Analítico, urgente, financiero.
            MISIÓN: Análisis técnico, fundamental y de mercado. Detectar gemas y estafas.
            ESTILO: Habla de liquidez, market cap, velas y ciclos de mercado.
        """,
        "prompt_en": """
            ROLE: Wall Street Investor & Blockchain Expert.
            TONE: Analytical, urgent, financial.
            MISSION: Technical and fundamental analysis. Spotting gems and scams.
            STYLE: Discuss liquidity, market cap, candles, and market cycles.
        """
    },
    "youtube": {
        "name": "Creator Economy",
        "keywords_file": "data/keywords_youtube.txt",
        "output_dir": "content/youtube",
        "search_context": "creator economy youtube algorithm twitch stats influencer business",
        "prompt_es": """
            ROL: Estratega Digital de la Creator Economy.
            TONO: Analítico, enfocado en el negocio y las métricas.
            MISIÓN: Deconstruir el éxito de YouTubers, cambios de algoritmo y monetización.
            ESTILO: Habla de RPM, CTR, retención y viralidad.
        """,
        "prompt_en": """
            ROLE: Digital Strategist & Creator Economy Analyst.
            TONE: Business-focused, metrics-driven.
            MISSION: Deconstruct YouTuber success, algo changes, and monetization.
            STYLE: Focus on RPM, CTR, retention, and virality.
        """
    },
    "viral": {
        "name": "Viral & Trends",
        "keywords_file": "data/keywords_viral.txt",
        "output_dir": "content/viral",
        "search_context": "viral internet trends reddit twitter drama pop culture",
        "prompt_es": """
            ROL: Redactor Senior de Revista Digital (Estilo Vice/BuzzFeed).
            TONO: Emocional, curioso, enganchante (Clicky).
            MISIÓN: Explicar el drama o la tendencia del momento.
            ESTILO: Seguro para anunciantes (sin odio), pero con salseo.
        """,
        "prompt_en": """
            ROLE: Senior Digital Magazine Editor (Vice/BuzzFeed style).
            TONE: Emotional, curious, engaging (Clicky).
            MISSION: Explain the current drama or trend.
            STYLE: Brand-safe (no hate), but spicy.
        """
    }
}

COMPLETED_FILE = 'data/completed.txt'

def obtener_keyword(category):
    """Obtiene una keyword específica para la categoría."""
    config = NICHES.get(category)
    if not config: return None
    
    filepath = config['keywords_file']
    if not os.path.exists(filepath):
        # Crear archivo dummy si no existe para evitar crash
        os.makedirs('data', exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(f"Trend 1 for {category}\n")
        return f"Trend 1 for {category}"

    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    
    if not lines: return None
    
    # Selección FIFO
    tema = lines[0]
    
    # Rotación
    with open(filepath, 'w') as f:
        for l in lines[1:]:
            f.write(f"{l}\n")
            
    return tema

def planificar_articulo(tema, contexto, lang, category_config):
    """Planifica el artículo (Título/Slug) según la personalidad del nicho."""
    print(f"🏗️ Planificando ({lang.upper()}) - Nicho: {category_config['name']}...")
    
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    
    prompt = f"""
    {prompt_persona}
    
    ACT LIKE AN EDITOR IN CHIEF.
    Topic: "{tema}"
    Context: "{contexto[:1500]}..."
    Language: {lang.upper()}
    
    TASK: Create metadata for a definitive article.
    
    STRICT JSON OUTPUT:
    {{ "titulo": "...", "slug_sugerido": "..." }}
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
    
    prompt = f"""
    {prompt_persona}
    
    WRITE A COMPLETE ARTICLE ABOUT: "{meta['titulo']}".
    CONTEXT: {contexto}
    
    STRUCTURE:
    - **TL;DR** (Bullets).
    - **Introduction** (Hook).
    - **Deep Dive** (H2 sections).
    - **Conclusion/Takeaway**.
    
    LENGTH: 1200-1500 words.
    LANGUAGE: {lang.upper()}
    """
    
    resp = client.models.generate_content(
        model='gemini-2.0-flash', contents=prompt
    )
    return resp.text.strip()

def guardar_post(meta, contenido, lang, category):
    config = NICHES[category]
    output_dir = config['output_dir']
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = f"{output_dir}/{meta['slug']}.md"
    
    # Imagen local
    imagen = ImageManager.download_image(
        f"https://image.pollinations.ai/prompt/{urllib.parse.quote(meta['titulo'])}?model=flux&width=1280&height=720&nologo=true", 
        meta['titulo']
    )
    
    # Backdating
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
    
    tema = obtener_keyword(cat)
    if not tema:
        print("💤 No hay keywords.")
        return
        
    print(f"🎯 TEMA: {tema}")
    
    # Investigación con Contexto Específico
    # Concatenamos la keyword con el contexto del nicho para mejorar la búsqueda
    search_query = f"{tema} {NICHES[cat]['search_context']}"
    
    res = researcher.Researcher()
    contexto = res.research_topic(search_query) # Researcher V3 maneja esto
    
    # Generación Dual
    for lang in ["es", "en"]:
        meta = planificar_articulo(tema, contexto, lang, NICHES[cat])
        texto = escribir_articulo(meta, contexto, lang, NICHES[cat])
        guardar_post(meta, texto, lang, cat)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
