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
SYSTEM_INSTRUCTION = """
Eres el DIRECTOR DE CONTENIDOS de 'NOVUMWORLD'.
Tu misión es crear CLUSTERS DE INFORMACIÓN interconectados sobre tecnología y geopolítica.

ESTILO 'REALI-TEA':
1. NO ERES UNA WIKI. Eres un analista que opina.
2. DATOS REALES: Usa el contexto proporcionado (News/NotebookLM). Cita fuentes.
3. ESTRUCTURA:
   - H1: Título Viral (Clickbatero pero honesto).
   - TL;DR: 3 Puntos Clave al inicio (Bullet points).
   - Cuerpo: Párrafos cortos, negritas estratégicas.
   - Interlinking: Menciona explícitamente los otros artículos del cluster.

PROHIBIDO:
- Usar frases como "En conclusión", "Es importante destacar".
- Inventar datos si no están en el contexto (di "según analistas" o especula con lógica).
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

def planificar_cluster(tema, contexto_investigacion):
    """
    Fase de Arquitectura: Define 1 Pilar + 2 Spokes (Títulos y Slugs) ANTES de escribir.
    """
    print(f"🏗️ Planificando Cluster para: '{tema}'...")
    
    prompt = f"""
    ACTÚA COMO UN ARQUITECTO SEO.
    Tema Central: "{tema}"
    Contexto Disponible: "{contexto_investigacion[:2000]}..." (Extracto)
    
    TAREA: Diseña un CLUSTER DE CONTENIDOS (3 Artículos) interconectados.
    
    1. ARTÍCULO PILAR (MAIN): Guía completa, visión general. Título épico.
    2. SPOKE 1 (SUBTEMA A): Un ángulo específico muy polémico o técnico derivado del tema.
    3. SPOKE 2 (SUBTEMA B): Otro ángulo diferente (ej: impacto económico, futuro, historia).
    
    SALIDA JSON ESTRICTA (Sin markdown, solo el objeto raw):
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
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        # Limpieza defensiva por si Gemini mete markdown
        texto_json = resp.text.replace('```json', '').replace('```', '').strip()
        plan = json.loads(texto_json)
        
        # Validación de estructura mínima
        if "pilar" not in plan: raise ValueError("JSON incompleto")

        # Sanitizar slugs con nuestra herramienta robusta
        plan['pilar']['slug'] = SlugManager.generate(plan['pilar']['slug_sugerido'])
        plan['spoke_1']['slug'] = SlugManager.generate(plan['spoke_1']['slug_sugerido'])
        plan['spoke_2']['slug'] = SlugManager.generate(plan['spoke_2']['slug_sugerido'])
        
        return plan
    except Exception as e:
        print(f"⚠️ Error planificando cluster: {e}")
        # Fallback manual básico
        base_slug = SlugManager.generate(tema)
        return {
            "pilar": {"titulo": f"Guía Definitiva: {tema}", "slug": base_slug},
            "spoke_1": {"titulo": f"El Lado Oculto de {tema}", "slug": f"{base_slug}-analisis"},
            "spoke_2": {"titulo": f"Futuro de {tema}", "slug": f"{base_slug}-futuro"}
        }

def escribir_articulo(tipo, meta, plan_completo, contexto):
    """
    Escribe un artículo específico (Pilar o Spoke) inyectando los enlaces a los otros.
    """
    titulo = meta['titulo']
    slug = meta['slug']
    print(f"✍️ Escribiendo {tipo.upper()}: {titulo}...")
    
    # Preparar Estrategia de Enlaces
    links_instruccion = ""
    if tipo == "pilar":
        links_instruccion = f"""
        TU OBJETIVO SEO: Este es el ARTÍCULO PILAR.
        Debes mencionar y enlazar a los satélites en el cuerpo del texto:
        - Menciona "{plan_completo['spoke_1']['titulo']}" usando el enlace relativo: /posts/{plan_completo['spoke_1']['slug']}
        - Menciona "{plan_completo['spoke_2']['titulo']}" usando el enlace relativo: /posts/{plan_completo['spoke_2']['slug']}
        """
    else:
        links_instruccion = f"""
        TU OBJETIVO SEO: Este es un ARTÍCULO SATÉLITE (Spoke).
        OBLIGATORIO: Inicia el contenido (después del TL;DR) con esta línea exacta:
        > Este artículo es parte de nuestra [Guía Central: {plan_completo['pilar']['titulo']}](/posts/{plan_completo['pilar']['slug']}).
        """

    prompt = f"""
    ESCRIBE UN ARTÍCULO COMPLETO EN MARKDOWN SOBRE: "{titulo}".
    
    CONTEXTO DE INVESTIGACIÓN (USA ESTOS DATOS):
    {contexto}
    
    INSTRUCCIONES DE ENLAZADO INTERNO (OBLIGATORIO):
    {links_instruccion}
    
    ESTRUCTURA MARKDOWN:
    - No repitas el título H1 al principio (ya va en el front matter).
    - Empieza con:
      **TL;DR (Resumen Rápido):**
      * Punto 1
      * Punto 2
      * Punto 3
    - Sigue con una Introducción potente.
    - Usa H2 para secciones.
    - Usa negritas para conceptos clave.
    
    LONGITUD: {'1500 palabras' if tipo == 'pilar' else '800 palabras'}.
    """
    
    resp = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt
    )
    
    return resp.text.strip()

def guardar_post(meta, contenido):
    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = f"{POSTS_DIR}/{meta['slug']}.md"
    
    # --- CAMBIO CRÍTICO: Imagen Local ---
    imagen_local = generar_imagen_flux_local(meta['titulo'])
    # ------------------------------------
    
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Generar metadescription simple
    clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ') + "..."
    
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {fecha}
draft: false
description: "{clean_text}"
featured_image: "{imagen_local}"
tags: ["Tecnología", "Análisis", "Geopolítica"]
categories: ["Deep Dive"]
---

![{meta['titulo']}]({imagen_local})

{contenido}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    
    print(f"✅ Guardado: {filepath}")

def main():
    print("🚀 INICIANDO SISTEMA DE CLUSTER INSTANTÁNEO (FIX SEO)")
    
    # 1. Obtener Tema
    tema = obtener_keyword()
    if not tema:
        print("💤 No hay temas en cola (keywords.txt vacío).")
        return

    print(f"🎯 TEMA OBJETIVO: {tema}")
    
    # 2. Investigación (NotebookLLM / News)
    # Instanciamos el Researcher de nuestro nuevo módulo
    investigador = researcher.Researcher()
    try:
        contexto = investigador.research_topic(tema)
    except Exception as e:
        print(f"⚠️ Error en investigación: {e}. Usando contexto vacío.")
        contexto = "No se pudo obtener investigación profunda. Usa conocimiento general."
    
    # 3. Planificación (Cluster)
    plan = planificar_cluster(tema, contexto)
    
    # 4. Generación y Guardado (Paralelo conceptual)
    # Pilar
    contenido_pilar = escribir_articulo("pilar", plan['pilar'], plan, contexto)
    guardar_post(plan['pilar'], contenido_pilar)
    
    # Spoke 1
    contenido_s1 = escribir_articulo("spoke", plan['spoke_1'], plan, contexto)
    guardar_post(plan['spoke_1'], contenido_s1)
    
    # Spoke 2
    contenido_s2 = escribir_articulo("spoke", plan['spoke_2'], plan, contexto)
    guardar_post(plan['spoke_2'], contenido_s2)
    
    # 5. Registro
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{tema} (Cluster Completo)\n")

if __name__ == "__main__":
    main()
