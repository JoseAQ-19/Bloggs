import os
import json
import re
import time
import random
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
from researcher import TrendDetector
from utils import SlugManager, ImageManager

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY. El cliente de Gemini no funcionará a menos que se inyecte manualmente.")
    client = None

# Sistema de Archivos
KEYWORDS_FILE = 'data/keywords.txt'
COMPLETED_FILE = 'data/completed.txt'
POSTS_DIR = 'content/posts'

# 1. PERSONA DEL AGENTE (Director de Contenidos)
SYSTEM_INSTRUCTION_ES = """
ROL: Eres un EXPERTO TECH CÍNICO Y REAL (Anti-AI Persona).
Tu misión es escribir análisis crudos, directos y con opinión fuerte sobre tecnología y geopolítica.

ESTILO 'RADICAL HUMAN' (ESPAÑOL):
1. 🚫 PROHIBIDO SER NEUTRAL:
   - No digas "Existen varias opiniones". Di "La mayoría se equivoca. La realidad es...".
   - Toma partido. Sé valiente. Si algo es basura, dilo.

2. 🗣️ LENGUAJE CONVERSACIONAL (Jerga Tech):
   - Frases cortas y punchy.
   - Preguntas retóricas: "¿Crees que lo hicieron por caridad? Ja."
   - Analogías reales: "Correr esto en CPU es como llenar una piscina con una cuchara".

3. 📉 ESTRUCTURA IMPERFECTA (Humana):
   - Empieza con una anécdota o declaración fuerte (Hooks), nunca con definiciones de diccionario.
   - Rompe la cuarta pared: Habla al lector ("Tú").

4. 🛑 LISTA NEGRA (Detectores de IA):
   - SI USAS ESTAS FRASES, EL SISTEMA TE BORRARÁ:
     "En conclusión", "En resumen", "Es importante destacar", "Un tapiz de...",
     "En el panorama actual", "Cabe señalar", "Es crucial", "Sumérgete en".
   - Bórralas y reescribe con lenguaje natural.

TU META: Que el lector dude si esto lo escribió una IA o un ingeniero cabreado de Silicon Valley.
"""

SYSTEM_INSTRUCTION_EN = """
ROLE: You are a TECH INSIDER and AGGRESSIVE WALL STREET ANALYST.
Your mission is to write raw, direct, and opinionated deep dives on tech and geopolitics for the US Market.

STYLE 'TECH INSIDER' (ENGLISH):
1. 🚫 NO NEUTRALITY:
   - Don't say "There are various opinions". Say "Most people are wrong. The reality is...".
   - Pick a side. Be bold. If something is trash, call it trash.

2. 🗣️ CONVERSATIONAL & SHARP:
   - Short, punchy sentences.
   - Rhetorical questions: "Do you really think they did that for charity? Ha."
   - Real-world analogies.
   - Use US currency ($) and Silicon Valley references.

3. 📉 IMPERFECT STRUCTURE (Human):
   - Start with a strong hook or anecdote, never a dictionary definition.
   - Break the fourth wall: Talk to the reader ("You").

4. 🛑 BLACKLIST (AI Detectors):
   - NEVER USE: "In conclusion", "In summary", "It is important to note", "A tapestry of...",
     "In the current landscape", "It is worth noting", "Delve into".
   - Delete them and rewrite naturally.

GOAL: Make the reader wonder if this was written by an AI or a pissed-off Senior Engineer at Google.
"""

def obtener_keyword():
    """Obtiene keyword de la cola FIFO. Si está vacía, detecta tendencia automáticamente."""
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        if lines:
            # Selección FIFO
            tema = lines[0]
            with open(KEYWORDS_FILE, 'w') as f:
                for l in lines[1:]:
                    f.write(f"{l}\n")
            print(f"📋 Keyword de cola: '{tema}'")
            return tema

    # FALLBACK: Auto-detección de tendencias del nicho
    print("🔥 Cola vacía → Activando DETECCIÓN AUTOMÁTICA de tendencias...")
    for category in ["tech", "crypto", "geopolitics"]:
        trends = TrendDetector.get_niche_trends(category, max_trends=3)
        if trends:
            # Tomar la tendencia más fresca
            selected = trends[0]
            tema = selected['title']
            print(f"🎯 Tendencia auto-detectada [{category}]: {tema[:60]}...")
            return tema

    print("💤 No se encontraron tendencias ni keywords.")
    return None

def generar_imagen_flux_local(titulo):
    """
    Genera imagen con Pollinations, la DESCARGA localmente y retorna ruta local.
    """
    print(f"🎨 Generando y Descargando imagen para: {titulo}")
    try:
        # 1. Construir URL de Pollinations
        prompt = f"Editorial photography, cinematic lighting, ultra-realistic, 8k. Theme: {titulo}. Minimalist tech style, dark background with neon accents."
        encoded = urllib.parse.quote(prompt)
        seed = random.randint(0, 99999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1280&height=720&seed={seed}&nologo=true"
        
        # 2. Descargar localmente
        local_path = ImageManager.download_image(image_url, titulo)
        if local_path:
            return local_path
        else:
            return "" # Fallback a nada o imagen default
    except Exception as e:
        print(f"⚠️ Error imagen: {e}")
        return ""

def planificar_cluster(tema, contexto_investigacion, lang="es"):
    """
    Fase de Arquitectura: Define 1 Artículo Único (SNIPER MODE).
    """
    print(f"🏗️ Planificando Artículo Sniper ({lang.upper()}) para: '{tema}'...")
    
    system_instr = SYSTEM_INSTRUCTION_ES if lang == "es" else SYSTEM_INSTRUCTION_EN
    
    prompt = f"""
    ACT LIKE AN EDITOR IN CHIEF.
    Topic: "{tema}"
    Context: "{contexto_investigacion[:2000]}..."
    Language: {lang.upper()} (Output titles in this language).
    
    TASK: Create the metadata for ONE definitive article.
    
    STRICT JSON OUTPUT (No markdown):
    {{
      "titulo": "...", 
      "slug_sugerido": "..." 
    }}
    """
    
    try:
        resp = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", system_instruction=system_instr)
        )
        texto_json = resp.text.replace('```json', '').replace('```', '').strip()
        plan = json.loads(texto_json)
        
        # Sanitizar slug
        suffix = "-en" if lang == "en" else ""
        plan['slug'] = SlugManager.generate(plan['slug_sugerido']) + suffix
        
        return plan
    except Exception as e:
        print(f"⚠️ Error planificando: {e}")
        base_slug = SlugManager.generate(tema)
        suffix = "-en" if lang == "en" else ""
        return {"titulo": f"Deep Dive: {tema}", "slug": f"{base_slug}{suffix}"}

def escribir_articulo(meta, contexto, lang="es"):
    """
    Escribe el artículo único.
    """
    titulo = meta['titulo']
    print(f"✍️ Escribiendo ARTÍCULO SNIPER ({lang}): {titulo}...")
    
    system_instr = SYSTEM_INSTRUCTION_ES if lang == "es" else SYSTEM_INSTRUCTION_EN
    
    prompt = f"""
    WRITE A COMPLETE MARKDOWN ARTICLE ABOUT: "{titulo}".
    
    RESEARCH CONTEXT (USE THESE FACTS):
    {contexto}
    
    MARKDOWN STRUCTURE:
    - Start with **TL;DR (Key Takeaways):** (Bullet points).
    - Follow with a strong Introduction (Hook).
    - Use H2 for sections.
    - Use bold for key concepts.
    - NO internal linking to non-existent articles. Focus on depth.
    
    LENGTH: 1500 words.
    LANGUAGE: {lang.upper()}
    """
    
    resp = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system_instr)
    )
    
    return resp.text.strip()

def guardar_post(meta, contenido, lang="es"):
    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = f"{POSTS_DIR}/{meta['slug']}.md"
    
    # Check if exists (Anti-Repetition handled before, but safe check)
    if os.path.exists(filepath):
        print(f"⚠️ Archivo ya existe, sobrescribiendo: {filepath}")

    imagen_local = generar_imagen_flux_local(meta['titulo'])
    
    # --- LOGICA DE RETARDO HUMANO (ANTI-BOT) ---
    now = datetime.now()
    if lang == "es":
        # Simula publicación hace 15-20 mins
        backdate_mins = random.randint(15, 25)
    else:
        # Simula publicación "Breaking News" hace 2-5 mins
        backdate_mins = random.randint(2, 5)
        
    fecha_simulada = now - timedelta(minutes=backdate_mins)
    fecha_str = fecha_simulada.strftime("%Y-%m-%dT%H:%M:%S")
    # -------------------------------------------
    
    clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ') + "..."
    
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {fecha_str}
draft: false
description: "{clean_text}"
featured_image: "{imagen_local}"
tags: ["Technology", "Analysis", "Geopolitics"]
categories: ["Deep Dive"]
language: "{lang}"
---

![{meta['titulo']}]({imagen_local})

{contenido}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"✅ Guardado ({lang}) - Fecha Simulada: {fecha_str}")

def main():
    print("🚀 INICIANDO SISTEMA SNIPER GLOBAL v2 (Trend Detection + NotebookLM)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. Obtener Tema (Cola FIFO → Fallback: Auto-Tendencia)
    tema = obtener_keyword()
    if not tema:
        print("💤 No hay temas disponibles (cola vacía + sin tendencias).")
        return

    print(f"\n🎯 TEMA OBJETIVO: {tema}")
    
    # 2. Investigación Profunda (NotebookLM MCP → Fallback: Scraping)
    investigador = researcher.Researcher()
    try:
        contexto = investigador.research_topic(tema)
    except Exception as e:
        print(f"⚠️ Error en investigación: {e}. Usando contexto mínimo.")
        contexto = f"No deep research available. Topic: {tema}. Write based on general knowledge."
    
    # 3. Bucle de Idiomas (High CPM Strategy)
    idiomas = ["es", "en"]
    
    for lang in idiomas:
        print(f"\n--- GENERANDO POST EN: {lang.upper()} ---")
        
        # Planificación (Single Article)
        meta = planificar_cluster(tema, contexto, lang)
        
        # Generación (Sin Spokes)
        contenido = escribir_articulo(meta, contexto, lang)
        guardar_post(meta, contenido, lang)
    
    # 5. Registro Final
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{tema} (Global Sniper Completed)\n")

if __name__ == "__main__":
    main()
