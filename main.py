import os
import json
import re
import time
import random
import urllib.parse
from datetime import datetime
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
    if not os.path.exists(KEYWORDS_FILE): return None
    with open(KEYWORDS_FILE, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines: return None
    
    # Selección: Prioridad FIFO (Lo primero de la lista)
    tema = lines[0]
    
    # Rotación: Mover al final (o borrar si se prefiere, aquí lo borramos de la lista activa)
    with open(KEYWORDS_FILE, 'w') as f:
        for l in lines[1:]:
            f.write(f"{l}\n")
            
    return tema

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
    Fase de Arquitectura: Define 1 Pilar + 2 Spokes (Títulos y Slugs) ANTES de escribir.
    """
    print(f"🏗️ Planificando Cluster ({lang.upper()}) para: '{tema}'...")
    
    system_instr = SYSTEM_INSTRUCTION_ES if lang == "es" else SYSTEM_INSTRUCTION_EN
    role_desc = "ARQUITECTO SEO" if lang == "es" else "SEO ARCHITECT"
    
    prompt = f"""
    ACT LIKE AN {role_desc}.
    Topic: "{tema}"
    Context: "{contexto_investigacion[:2000]}..."
    Language: {lang.upper()} (Output titles in this language).
    
    TASK: Design a CONTENT CLUSTER (3 Articles).
    
    1. PILLAR ARTICLE (MAIN): Complete guide, overview. Epic title.
    2. SPOKE 1 (SUBTOPIC A): Specific, controversial angle.
    3. SPOKE 2 (SUBTOPIC B): Another angle (e.g., economic impact, future).
    
    STRICT JSON OUTPUT (No markdown):
    {{
      "pilar": {{ "titulo": "...", "slug_sugerido": "..." }},
      "spoke_1": {{ "titulo": "...", "slug_sugerido": "..." }},
      "spoke_2": {{ "titulo": "...", "slug_sugerido": "..." }}
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
        
        if "pilar" not in plan: raise ValueError("JSON incompleto")

        # Sanitizar slugs
        suffix = "-en" if lang == "en" else ""
        plan['pilar']['slug'] = SlugManager.generate(plan['pilar']['slug_sugerido']) + suffix
        plan['spoke_1']['slug'] = SlugManager.generate(plan['spoke_1']['slug_sugerido']) + suffix
        plan['spoke_2']['slug'] = SlugManager.generate(plan['spoke_2']['slug_sugerido']) + suffix
        
        return plan
    except Exception as e:
        print(f"⚠️ Error planificando cluster: {e}")
        base_slug = SlugManager.generate(tema)
        suffix = "-en" if lang == "en" else ""
        return {
            "pilar": {"titulo": f"Guide: {tema}", "slug": f"{base_slug}{suffix}"},
            "spoke_1": {"titulo": f"Analysis: {tema}", "slug": f"{base_slug}-analysis{suffix}"},
            "spoke_2": {"titulo": f"Future: {tema}", "slug": f"{base_slug}-future{suffix}"}
        }

def escribir_articulo(tipo, meta, plan_completo, contexto, lang="es"):
    """
    Escribe un artículo específico (Pilar o Spoke).
    """
    titulo = meta['titulo']
    print(f"✍️ Escribiendo {tipo.upper()} ({lang}): {titulo}...")
    
    system_instr = SYSTEM_INSTRUCTION_ES if lang == "es" else SYSTEM_INSTRUCTION_EN
    
    # Preparar Estrategia de Enlaces
    links_instruccion = ""
    if lang == "es":
        intro_link_text = f"> Este artículo es parte de nuestra [Guía Central: {plan_completo['pilar']['titulo']}](/posts/{plan_completo['pilar']['slug']})."
        body_link_text = "Debes mencionar y enlazar a los satélites..."
    else:
        intro_link_text = f"> This article is part of our [Central Guide: {plan_completo['pilar']['titulo']}](/posts/{plan_completo['pilar']['slug']})."
        body_link_text = "You MUST mention and link to the satellite articles..."

    if tipo == "pilar":
        links_instruccion = f"""
        SEO GOAL: This is the PILLAR ARTICLE.
        {body_link_text}
        - Mention "{plan_completo['spoke_1']['titulo']}" using relative link: /posts/{plan_completo['spoke_1']['slug']}
        - Mention "{plan_completo['spoke_2']['titulo']}" using relative link: /posts/{plan_completo['spoke_2']['slug']}
        """
    else:
        links_instruccion = f"""
        SEO GOAL: This is a SATELLITE ARTICLE (Spoke).
        MANDATORY: Start content (after TL;DR) with this exact line:
        {intro_link_text}
        """

    prompt = f"""
    WRITE A COMPLETE MARKDOWN ARTICLE ABOUT: "{titulo}".
    
    RESEARCH CONTEXT (USE THESE FACTS):
    {contexto}
    
    INTERLINKING INSTRUCTIONS (MANDATORY):
    {links_instruccion}
    
    MARKDOWN STRUCTURE:
    - No H1 at start (handled by front matter).
    - Start with **TL;DR (Key Takeaways):** (Bullet points).
    - Follow with a strong Introduction (Hook).
    - Use H2 for sections.
    - Use bold for key concepts.
    
    LENGTH: {'1500 words' if tipo == 'pilar' else '800 words'}.
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
    
    # Compartir imagen entre idiomas para ahorrar recursos (o generar nueva si se prefiere)
    # Por ahora generamos una por idioma para que el texto (si hubiera) o vibe encaje, 
    # pero el prompt de imagen es agnóstico.
    # Optimizacion: Usar la misma imagen si el slug base es igual? 
    # Simplificación: Generar nueva. Pollinations es gratis.
    imagen_local = generar_imagen_flux_local(meta['titulo'])
    
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ') + "..."
    
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {fecha}
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
    
    print(f"✅ Guardado ({lang}): {filepath}")

def main():
    print("🚀 INICIANDO SISTEMA DE CLUSTER GLOBAL (ES/EN)")
    
    # 1. Obtener Tema
    tema = obtener_keyword()
    if not tema:
        print("💤 No hay temas en cola (keywords.txt vacío).")
        return

    print(f"🎯 TEMA OBJETIVO: {tema}")
    
    # 2. Investigación (NotebookLLM / News)
    investigador = researcher.Researcher()
    try:
        contexto = investigador.research_topic(tema)
    except Exception as e:
        print(f"⚠️ Error en investigación: {e}. Usando contexto vacío.")
        contexto = "No research available."
    
    # 3. Bucle de Idiomas (High CPM Strategy)
    idiomas = ["es", "en"]
    
    for lang in idiomas:
        print(f"\n--- GENERANDO CLUSTER EN: {lang.upper()} ---")
        
        # Planificación
        plan = planificar_cluster(tema, contexto, lang)
        
        # Generación
        # Pilar
        contenido_pilar = escribir_articulo("pilar", plan['pilar'], plan, contexto, lang)
        guardar_post(plan['pilar'], contenido_pilar, lang)
        
        # Spoke 1
        contenido_s1 = escribir_articulo("spoke", plan['spoke_1'], plan, contexto, lang)
        guardar_post(plan['spoke_1'], contenido_s1, lang)
        
        # Spoke 2
        contenido_s2 = escribir_articulo("spoke", plan['spoke_2'], plan, contexto, lang)
        guardar_post(plan['spoke_2'], contenido_s2, lang)
    
    # 5. Registro Final
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{tema} (Global Cluster Completed)\n")

if __name__ == "__main__":
    main()
