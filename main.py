import os
import requests
import json
import re
from google import genai
from google.genai import types
from datetime import datetime
import random
import urllib.parse
import time

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

client = genai.Client(api_key=GEMINI_KEY)

HUB_STATE_FILE = 'data/hub_state.json'
KEYWORDS_FILE = 'data/keywords.txt'

def obtener_keyword():
    if not os.path.exists(KEYWORDS_FILE): return None
    with open(KEYWORDS_FILE, 'r') as f:
        lines = f.readlines()
    if not lines: return None
    selected = lines[0].strip()
    with open(KEYWORDS_FILE, 'w') as f:
        f.writelines(lines[1:])
    return selected

def prepend_keywords(new_keywords):
    existing = []
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, 'r') as f:
            existing = f.readlines()
    
    with open(KEYWORDS_FILE, 'w') as f:
        for k in new_keywords:
            f.write(f"{k}\n")
        f.writelines(existing)

def gestionar_estado_hub(tema_actual):
    # Cargar estado
    state = {}
    if os.path.exists(HUB_STATE_FILE):
        with open(HUB_STATE_FILE, 'r') as f:
            try:
                state = json.load(f)
            except:
                state = {}

    is_hub = False
    hub_info = None

    if not state or state.get('spokes_left', 0) <= 0:
        # Nuevo HUB
        is_hub = True
        state = {
            'hub_keyword': tema_actual,
            'hub_slug': tema_actual.replace(" ", "-").lower(),
            'spokes_left': 5
        }
        print(f"👑 TEMA HUB DETECTADO: {tema_actual}")
    else:
        # Es un SPOKE
        is_hub = False
        state['spokes_left'] -= 1
        hub_info = {
            'keyword': state['hub_keyword'],
            'url': f"/posts/{state['hub_slug']}"
        }
        print(f"🛰️ TEMA SPOKE DETECTADO (Pertenece a {hub_info['keyword']})")

    # Guardar estado
    os.makedirs('data', exist_ok=True)
    with open(HUB_STATE_FILE, 'w') as f:
        json.dump(state, f)
    
    return is_hub, hub_info

def generar_imagen(titulo):
    print(f"🎨 Pintando imagen con Flux (Pollinations): {titulo}")
    try:
        prompt_arquitecto = f"Actúa como un Director de Arte experto. Escribe una descripción visual muy detallada, en INGLÉS, para una imagen fotorealista y cinemática sobre: '{titulo}'. Debe ser una sola frase larga. SIN comillas ni introducciones."
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt_arquitecto
        )
        descripcion_visual = response.text.strip().replace('"', '').replace("'", "")
        seed = random.randint(0, 1000000)
        prompt_encoded = urllib.parse.quote(descripcion_visual)
        imagen_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=flux&width=1280&height=720&seed={seed}&nologo=true"
        return imagen_url
    except Exception as e:
        print(f"⚠️ Error generando imagen: {e}")
        return None

# --- FASE A: EL ARQUITECTO (Escaleta) ---
def generar_indice(tema):
    print("🏗️ FASE A: Arquitecto diseñando la estructura...")
    prompt = f"""
    Actúa como un Arquitecto de Contenidos Senior.
    Tema: "{tema}".
    
    Tu tarea: Genera una lista JSON ESTRICTA de 6 a 8 encabezados (títulos H2) para un artículo masivo y experto.
    
    Reglas:
    1. Cubre aspectos técnicos, casos prácticos y futuro.
    2. NO incluyas Introducción ni Conclusión.
    3. Devuelve SOLO una lista de strings en formato JSON plano. Ejemplo: ["Qué es X", "Cómo funciona", "Ventajas", "Futuro"]
    """
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    try:
        # Limpiar bloques de código markdown
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        indice = json.loads(clean_json)
        return indice
    except:
        print("⚠️ Fallo parseando JSON del índice. Usando fallback.")
        return [f"Conceptos Clave de {tema}", f"Aplicaciones de {tema}", f"Análisis Técnico de {tema}", f"Futuro de {tema}"]

# --- FASE B: EL ESCRITOR (Bloques) ---
def escribir_bloque(encabezado, tema, hub_info):
    print(f"✍️ FASE B: Escribiendo bloque '{encabezado}'...")
    
    contexto_link = ""
    if hub_info:
        contexto_link = f"IMPORTANTE: Intenta mencionar el concepto '{hub_info['keyword']}' de forma natural e incluye este enlace Markdown: [{hub_info['keyword']}]({hub_info['url']}). Si no encaja, no lo fuerces."

    prompt = f"""
    Actúa como un Columnista Experto en Tecnología.
    Estás escribiendo una sección para el artículo: "{tema}".
    La sección es: "{encabezado}".

    INSTRUCCIONES DE ESCRITURA (MODULAR):
    1. Escribe 400 palabras profundas y técnicas sobre este subtema.
    2. ESTILO: Tono humano, cero saludos, cero IA. Usa analogías.
    3. GEO OPTIMIZATION (OBLIGATORIO):
       - Inmediatamente después del título de la sección, escribe un párrafo de 2 frases en negrita (**Resumen...**) que sintetice la idea clave.
       - Si comparas conceptos, genera una Tabla Markdown de 3 columnas automática.
    4. Cierre del bloque: Termina con un "Dato Técnico" o curiosidad relevante.
    5. {contexto_link}

    Empieza directamente con el contenido (sin repetir el título H2, eso lo pongo yo).
    """
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text

# --- FASE C: EL EDITOR (Ensamblaje y FAQ) ---
def generar_faq(contenido_total, tema):
    print("🧠 FASE C: Generando FAQ JSON-LD...")
    prompt = f"""
    Basándote en este texto sobre "{tema}":
    {contenido_total[:3000]}... (extracto)

    Genera 5 Preguntas Frecuentes (FAQ) relevantes.
    IMPORTANTE: Devuélvelas DIRECTAMENTE en formato de script JSON-LD (<script type="application/ld+json">...</script>) válido para insertar en HTML.
    """
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text

def extraer_subtemas(contenido_total):
    print("🌱 Generando Seeds (Subtemas) para futuros artículos...")
    prompt = f"""
    Lee este artículo y extrae 5 subtemas muy específicos o "long-tail keywords" que se mencionen pero que merezcan su propio artículo aparte.
    Devuelve SOLO la lista separada por comas.
    """
    response = client.models.generate_content(model='gemini-2.0-flash', contents=contenido_total[:4000])
    subtemas = [s.strip() for s in response.text.split(',')]
    return subtemas[:5]

def motor_de_contenidos(kw):
    is_hub, hub_info = gestionar_estado_hub(kw)
    
    # 1. Imagen
    imagen_url = generar_imagen(kw)
    
    # 2. Índice
    headers = generar_indice(kw)
    
    # 3. Escritura Modular
    contenido_completo = ""
    # Intro manual impactante
    intro_prompt = f"Escribe una introducción explosiva y viral (200 palabras) para un artículo sobre '{kw}'. Sin saludos. Directo a la yugular."
    intro_resp = client.models.generate_content(model='gemini-2.0-flash', contents=intro_prompt)
    contenido_completo += f"# {kw}\n\n{intro_resp.text}\n\n"
    
    for h in headers:
        bloque = escribir_bloque(h, kw, hub_info)
        contenido_completo += f"## {h}\n\n{bloque}\n\n"
        time.sleep(1) # Respetar rate limits
    
    # 4. FAQ
    faq_json = generar_faq(contenido_completo, kw)
    contenido_completo += f"\n\n## Preguntas Frecuentes\n{faq_json}"
    
    # 5. Generación de Spokes (Si es Hub)
    if is_hub:
        subtemas = extraer_subtemas(contenido_completo)
        print(f"🔗 Nuevos Spokes detectados: {subtemas}")
        prepend_keywords(subtemas)
    
    return contenido_completo, imagen_url

def guardar_localmente(titulo, contenido, imagen_url):
    slug = titulo.replace(" ", "-").lower()
    os.makedirs('content/posts', exist_ok=True)
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    image_fm = f"image: '{imagen_url}'" if imagen_url else ""
    front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\n{image_fm}\n---\n\n"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + contenido)
    print(f"✅ Artículo guardado: {filename}")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        try:
            texto, imagen_url = motor_de_contenidos(keyword)
            if texto:
                guardar_localmente(keyword, texto, imagen_url)
        except Exception as e:
            print(f"🔥 Error Crítico: {e}")
            exit(1)
    else:
        print("💤 Lista vacía.")
