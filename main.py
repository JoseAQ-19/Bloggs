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
ERES UN OPERADOR INDUSTRIAL DE PROCESAMIENTO DE DATOS.
TU SALIDA ES EXCLUSIVAMENTE CÓDIGO Y TEXTO PARA PROCESAMIENTO AUTOMATIZADO.
PROHIBIDO TERMINANTEMENTE:
- Saludos, cortesía o validación ("¡Excelente!", "Hola", "Aquí tienes").
- Introducciones o meta-comentarios ("El título es...", "He generado...").
- Feedback humano.

TU RESPUESTA DEBE EMPEZAR DIRECTAMENTE CON EL CONTENIDO SOLICITADO.
CUALQUIER TEXTO FUERA DE LO SOLICITADO HARÁ QUE EL SISTEMA FALLE.
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

# --- HERRAMIENTAS DE LIMPIEZA ---
def limpiar_titulo(texto):
    # 4. Refinar la Lógica de "Limpieza de Títulos"
    texto = texto.strip()
    # Eliminar prefijos de "IA habladora"
    texto = re.sub(r'^(y |o |además |¡|!)\s*', '', texto, flags=re.IGNORECASE)
    
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
    if not lineas: return "Sin Título"
    
    titulo = lineas[0]
    # Eliminar prefijos comunes de IA
    titulo = re.sub(r'^(TITULO:|Title:|Aquí tienes|Claro|El título es)\s*', '', titulo, flags=re.IGNORECASE).strip()
    titulo = titulo.replace('"', '').replace('*', '').replace('#', '')
    
    # Validación de longitud (Si es > 15 palabras, cortar)
    words = titulo.split()
    if len(words) > 15:
        return " ".join(words[:12]) + "..."
    
    return titulo

# --- FASE A: EL ARQUITECTO (Escaleta + Título) ---
def generar_estructura(tema):
    print("🏗️ FASE A: Arquitecto diseñando la estructura...")
    prompt = f"""
    Tema: "{tema}".
    
    TAREA:
    1. Genera un Título Viral y SEO-Optimizado.
    2. Genera una lista JSON ESTRICTA de 6 a 8 encabezados (H2).
    
    FORMATO DE SALIDA OBLIGATORIO (Usa estas etiquetas exactas):
    [TITULO]Escribe aquí el título[/TITULO]
    [ESCALETA]Escribe aquí el JSON[/ESCALETA]
    
    Reglas:
    - NO escribas nada fuera de estas etiquetas.
    - El JSON debe ser válido (lista de strings).
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    texto = response.text
    
    # Parsing manual con etiquetas
    titulo_match = re.search(r'\[TITULO\](.*?)\[/TITULO\]', texto, re.DOTALL)
    escaleta_match = re.search(r'\[ESCALETA\](.*?)\[/ESCALETA\]', texto, re.DOTALL)
    
    titulo_final = tema # Fallback
    headers = [f"Todo sobre {tema}", f"Análisis de {tema}", "Conclusión"] # Fallback

    if titulo_match:
        titulo_final = limpiar_titulo(titulo_match.group(1))
    
    if escaleta_match:
        try:
            headers = json.loads(escaleta_match.group(1))
        except:
            print("⚠️ Error JSON. Intentando limpiar markdown...")
            try:
                clean_json = escaleta_match.group(1).replace('```json', '').replace('```', '').strip()
                headers = json.loads(clean_json)
            except:
                pass
                
    return titulo_final, headers

# --- FASE B: EL ESCRITOR (Bloques) ---
def escribir_bloque(encabezado, titulo_articulo, hub_info):
    print(f"✍️ FASE B: Escribiendo bloque '{encabezado}'...")
    
    contexto_link = ""
    if hub_info:
        contexto_link = f"IMPORTANTE: Intenta mencionar el concepto '{hub_info['keyword']}' de forma natural e incluye este enlace Markdown: [{hub_info['keyword']}]({hub_info['url']}). Si no encaja, no lo fuerces."

    prompt = f"""
    Artículo: "{titulo_articulo}".
    Sección: "{encabezado}".

    INSTRUCCIONES:
    1. Escribe 400 palabras profundas y técnicas.
    2. ESTILO: Tono humano, cero saludos, cero IA.
    3. GEO OPTIMIZATION:
       - Empieza con párrafo **Resumen** (Bold).
       - Si comparas, usa Tabla Markdown.
    4. {contexto_link}

    SALIDA: Solo el contenido Markdown de la sección.
    """
    
    # Amnesia Selectiva: Cada llamada es stateless por defecto en generate_content
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return response.text

# --- FASE C: EL EDITOR (Ensamblaje y FAQ) ---
def generar_faq(contenido_total, tema):
    print("🧠 FASE C: Generando FAQ JSON-LD...")
    prompt = f"""
    Basado en: "{tema}".
    Genera 5 FAQ en formato JSON-LD (<script type="application/ld+json">).
    SOLO EL SCRIPT.
    """
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return response.text

def extraer_subtemas(contenido_total):
    print("🌱 Generando Seeds...")
    prompt = """
    ERES UN EXTRACTOR DE DATOS.
    Genera 5 temas cortos de 3 palabras máximo, separados por comas.
    PROHIBIDO dar feedback, felicitar al usuario o escribir párrafos.
    Si fallas, el sistema se detendrá.
    """
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=contenido_total[:3000],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return [s.strip() for s in response.text.split(',')][:5]

def motor_de_contenidos(kw):
    # Amnesia: kw es nuevo, reiniciamos todo el flujo
    print(f"\n🚀 INICIANDO MOTOR PARA: {kw}")
    
    is_hub, hub_info = gestionar_estado_hub(kw)
    
    # 1. Fase A: Estructura y Título
    titulo, headers = generar_estructura(kw)
    print(f"📌 Título Generado: {titulo}")
    
    # 2. Imagen
    imagen_url = generar_imagen(titulo)
    
    # 3. Intro
    intro_prompt = f"Escribe una intro viral (200 palabras) para '{titulo}'. Directo al grano."
    intro_resp = client.models.generate_content(
        model='gemini-2.0-flash', contents=intro_prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    # 5. Sincronización Fase C (Ensamblaje con espaciado explícito)
    contenido_completo = f"# {titulo}\n\n{intro_resp.text}\n\n"
    
    for h in headers:
        bloque = escribir_bloque(h, titulo, hub_info)
        # Separación explícita (Doble salto de línea para evitar pegado)
        contenido_completo += f"## {h}\n\n{bloque}\n\n"
        time.sleep(1)
    
    # 4. FAQ
    faq_json = generar_faq(contenido_completo, kw)
    contenido_completo += f"\n\n## Preguntas Frecuentes\n{faq_json}"
    
    # 5. Spokes
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
    # Limpiar slug de caracteres raros
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Recorte de seguridad (50 caracteres)
    slug = slug[:50]
    
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
