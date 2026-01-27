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

# 1. FORZAR MODO MÁQUINA (Instrucción de Sistema)
SYSTEM_INSTRUCTION = """
ERES UN REDACTOR DE CONTENIDO INVISIBLE DE ALTA GAMA.
TU PRODUCCIÓN VA DIRECTA A PUBLICACIÓN EDITORIAL.
PROHIBIDO TERMINANTEMENTE:
- Saludos, meta-comentarios ("Aquí tienes el texto", "He redactado...").
- Etiquetas de sección administrativas visibles como "TÍTULO:", "INTRODUCCIÓN:", "SECCIÓN:", "CONTENIDO:".
- Repetir el título de la sección al inicio del párrafo.
- Feedback humano.

TU OBJETIVO ES GENERAR TEXTO FINAL IMPECABLE QUE NO REQUIERA EDICIÓN HUMANA.
SI EL INPUT PIDE "INTRODUCCIÓN", ESCRIBE DIRECTAMENTE EL PÁRRAFO DE INTRODUCCIÓN, SIN PONER EL TÍTULO "INTRODUCCIÓN".
"""

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

# --- HERRAMIENTAS DE LIMPIEZA FINAL ---
def limpiar_contenido_final(texto):
    if not texto: return ""
    
    # 1. Sanitización de Etiquetas Prohibidas
    prohibidas = ["TÍTULO:", "TITLE:", "INTRODUCCIÓN:", "INTRO:", "META-DESCRIPCIÓN:", "CONTENIDO:", "SECCIÓN:", "CONCLUSIÓN:"]
    for p in prohibidas:
        texto = re.sub(f"^{p}\s*", "", texto, flags=re.IGNORECASE | re.MULTILINE)
    
    # 2. Reparar Newlines literales
    texto = texto.replace('\\n', '\n')
    
    # 3. Aire Visual para Tablas
    texto = re.sub(r'(\n\|.*\|)', r'\n\n\1', texto) 
    
    return texto.strip()

def limpiar_eco_encabezado(texto, encabezado):
    """
    Elimina el encabezado si aparece repetido al inicio del texto.
    """
    texto = texto.strip()
    # Normalize for comparison (ignore case/punctuation)
    norm_texto = re.sub(r'[^\w\s]', '', texto.lower())
    norm_header = re.sub(r'[^\w\s]', '', encabezado.lower())
    
    if norm_texto.startswith(norm_header):
        # Remove header from raw text (case insensitive)
        texto = re.sub(f"^{re.escape(encabezado)}\s*[:\.]?\s*", "", texto, flags=re.IGNORECASE).strip()
    
    # Also clean common "link phrases"
    frases_eco = [
        f"Todo sobre {encabezado}",
        f"En este apartado hablaremos de {encabezado}",
        f"Como vemos en {encabezado}",
        "A continuación analizaremos"
    ]
    for frase in frases_eco:
         texto = re.sub(f"^{re.escape(frase)}\s*[:\.]?\s*", "", texto, flags=re.IGNORECASE).strip()
         
    return texto

def limpiar_titulo(texto):
    texto = texto.strip()
    
    patron_basura = r'^(y |o |además |¡|!|continuando|profundizando|analizando|siguiendo|como vemos|en este artículo|hoy vamos a ver)\s*'
    texto = re.sub(patron_basura, '', texto, flags=re.IGNORECASE)
    
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
    if not lineas: return "Sin Título"
    titulo = lineas[0]
    
    titulo = re.sub(r'^(TITULO:|Title:|Here is|Aquí tienes|Claro|El título es)\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'^[\d\.\-\s\*]+', '', titulo) 
    titulo = titulo.replace('*', '').replace('#', '').replace('"', '').replace('`', '')
    titulo = re.sub(r':\s*$', '', titulo)
    
    words = titulo.split()
    if len(words) > 15:
        titulo = " ".join(words[:12]) + "..."
    
    if titulo and titulo[0].islower():
        titulo = titulo[0].upper() + titulo[1:]
    
    return titulo.strip()

# --- FASE A: EL ARQUITECTO (Headers Cortos) ---
def generar_estructura(tema):
    print("🏗️ FASE A: Arquitecto diseñando la estructura...")
    prompt = f"""
    Tema: "{tema}".
    TAREA:
    1. Genera un Título Viral y SEO-Optimizado.
    2. Genera una lista JSON ESTRICTA de 6 a 8 encabezados (H2).
    
    REGLA CLAVE PARA ENCABEZADOS (H2):
    - Deben ser CONCEPTOS CORTOS y ELEGANTES (Máximo 4 palabras).
    - PROHIBIDO frases largas o preguntas.
    - Ejemplo BIEN: "Impacto Económico", "Evolución Técnica".
    - Ejemplo MAL: "Cómo esto afectará a la economía mundial en el futuro".

    FORMATO OBLIGATORIO:
    [TITULO]Escribe aquí el título[/TITULO]
    [ESCALETA]Escribe aquí el JSON[/ESCALETA]
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    texto = limpiar_contenido_final(response.text)
    
    titulo_match = re.search(r'\[TITULO\](.*?)\[/TITULO\]', texto, re.DOTALL)
    escaleta_match = re.search(r'\[ESCALETA\](.*?)\[/ESCALETA\]', texto, re.DOTALL)
    
    titulo_final = tema 
    headers = [f"Análisis de {tema}", "Perspectivas Futuras", "Conclusión"]

    if titulo_match:
        titulo_final = limpiar_titulo(titulo_match.group(1))
    
    if escaleta_match:
        try:
            headers = json.loads(escaleta_match.group(1))
        except:
            pass
                
    return titulo_final, headers

# --- FASE B: EL ESCRITOR (Anti-Echo) ---
def escribir_bloque(encabezado, titulo_articulo, hub_info):
    print(f"✍️ FASE B: Escribiendo bloque '{encabezado}'...")
    
    contexto_link = ""
    if hub_info:
        contexto_link = f"Contexto opcional: '{hub_info['keyword']}' ([Enlace]({hub_info['url']}))."

    prompt = f"""
    ACTÚA COMO UN ANALISTA SENIOR DE UN FORO ECONÓMICO GLOBAL.
    REDACTA LA SECCIÓN: "{encabezado}" PARA EL ARTÍCULO: "{titulo_articulo}".

    --- REGLAS DE ORO DE ESCRITURA ---
    1. ANTI-ECHO (CRÍTICO): PROHIBIDO EMPEZAR EL PÁRRAFO REPITIENDO EL TÍTULO DE LA SECCIÓN.
    2. PROHIBIDO: Frases como "En esta sección...", "Como dice el título...".
    3. INICIO POTENTE: Empieza DIRECTAMENTE con un análisis fuerte o un dato.

    --- REGLAS DE ORO DE DISEÑO ---
    1. JERARQUÍA PLANA: No uses subtítulos (#, ##, ###) dentro de este bloque.
    2. NEGRITAS QUIRÚRGICAS: Úsalas SOLO para resaltar 1 concepto técnico clave (máximo 2 palabras).
    3. AIRE VISUAL: Cada 3 párrafos, intenta usar una LISTA de viñetas (-) o una TABLA compacta.
    4. TABLAS: DEBES dejar DOS saltos de línea (\\n\\n) antes y después de ella.
    
    {contexto_link}

    SALIDA: Solo el texto Markdown final. Cero etiquetas.
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    raw_text = limpiar_contenido_final(response.text)
    # Limpieza programática de ECO (Seguridad extra)
    return limpiar_eco_encabezado(raw_text, encabezado)

# --- FASE C: ESTRATEGA DE SEO ---
def generar_relacionados(tema):
    print("🧠 FASE C: Generando Estrategia de Enlazado...")
    prompt = f"""
    ACTÚA COMO UN ESTRATEGA DE SEO.
    Genera "## Temas Relacionados" para: "{tema}".
    
    FORMATO (Lista Markdown):
    * [Tema 1](/posts/slug-1)
    * [Tema 2](/posts/slug-2)
    * [Tema 3](/posts/slug-3)

    REGLAS:
    1. PROHIBIDO hablar. Solo la lista.
    2. Slugs limpios.
    3. Sin etiquetas extrañas.
    """
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return limpiar_contenido_final(response.text)

def extraer_subtemas(contenido_total):
    print("🌱 Generando Seeds...")
    prompt = """
    ACTÚA COMO UN ESTRATEGA DE DATOS.
    Genera 5 palabras clave (Seeds) para futuros artículos. 
    Formato: Solo palabras separadas por comas.
    PROHIBIDO HABLAR. SOLO DATOS.
    """
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=contenido_total[:3000],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    texto = limpiar_contenido_final(response.text)
    return [s.strip() for s in texto.split(',')][:5]

def motor_de_contenidos(kw):
    print(f"\n🚀 INICIANDO MOTOR PARA: {kw}")
    
    is_hub, hub_info = gestionar_estado_hub(kw)
    
    titulo, headers = generar_estructura(kw)
    print(f"📌 Título Generado: {titulo}")
    
    imagen_url = generar_imagen(titulo)
    
    intro_prompt = f"Escribe una intro profesional (200 palabras) para '{titulo}'. Estilo analista global. Directo al grano."
    intro_resp = client.models.generate_content(
        model='gemini-2.0-flash', contents=intro_prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    intro_texto = limpiar_contenido_final(intro_resp.text)
    contenido_completo = f"{intro_texto}\n\n"
    
    for h in headers:
        bloque = escribir_bloque(h, titulo, hub_info)
        contenido_completo += f"## {h}\n\n{bloque}\n\n"
        time.sleep(1)
    
    bloque_relacionados = generar_relacionados(titulo)
    contenido_completo += f"\n\n{bloque_relacionados}\n\n"
    
    if is_hub:
        try:
            subtemas = extraer_subtemas(contenido_completo)
            prepend_keywords(subtemas)
            print(f"🔗 Spokes añadidos: {subtemas}")
        except:
            pass
    
    return titulo, contenido_completo, imagen_url

def guardar_localmente(titulo, contenido, imagen_url):
    slug = titulo.replace(" ", "-").lower()
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = slug[:50]
    
    os.makedirs('content/posts', exist_ok=True)
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    image_fm = f"image: '{imagen_url}'" if imagen_url else ""
    front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\n{image_fm}\n---\n\n"
    
    contenido = limpiar_contenido_final(contenido)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + contenido)
    print(f"✅ Artículo guardado: {filename}")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        try:
            titulo, texto, imagen_url = motor_de_contenidos(keyword)
            if texto:
                guardar_localmente(titulo, texto, imagen_url)
        except Exception as e:
            print(f"🔥 Error Crítico: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    else:
        print("💤 Lista vacía.")
