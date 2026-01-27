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
- Etiquetas de sección administrativas como "TÍTULO:", "INTRODUCCIÓN:", "CONTENIDO:", "META-DESCRIPCIÓN:", "SECCIÓN:". 
- Escribe DIRECTAMENTE el texto final que leerá el usuario.

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
def limpiar_tags(texto):
    # Eliminar etiquetas administrativas
    # Pattern: Line starts with one of these keywords followed by colon and optional space
    patron = r'^(TÍTULO|TITLE|META-DESCRIPCIÓN|INTRODUCCIÓN|CONTENIDO|SECCIÓN|INTRO):?\s*'
    texto = re.sub(patron, '', texto, flags=re.IGNORECASE | re.MULTILINE)
    return texto.strip()

def limpiar_titulo(texto):
    texto = texto.strip()
    
    # Lista Negra extendida: Conectores y Gerundios
    patron_basura = r'^(y |o |además |¡|!|continuando|profundizando|analizando|siguiendo|como vemos|en este artículo|hoy vamos a ver)\s*'
    texto = re.sub(patron_basura, '', texto, flags=re.IGNORECASE)
    
    # Filtro de Dos Pasos: Quedarse solo con la primera línea
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
    if not lineas: return "Sin Título"
    titulo = lineas[0]
    
    # Eliminar prefijos de IA y NÚMEROS/SIMBOLOS AGRESIVOS
    titulo = re.sub(r'^(TITULO:|Title:|Here is|Aquí tienes|Claro|El título es)\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'^[\d\.\-\s\*]+', '', titulo) # Elimina "1. ", "2-", "** " al inicio
    
    # Limpieza estricta de markdown en el título
    titulo = titulo.replace('*', '').replace('#', '').replace('"', '').replace('`', '')
    
    # Eliminar dos puntos al final
    titulo = re.sub(r':\s*$', '', titulo)
    
    # Validación de longitud
    words = titulo.split()
    if len(words) > 15:
        titulo = " ".join(words[:12]) + "..."
    
    # Capitalización tipo Título (Title Case)
    return titulo.strip().title()

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
    - El TÍTULO debe ser un nombre propio o una declaración directa (sin numeros ni gerundios).
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    texto = limpiar_tags(response.text)
    
    # Parsing manual con etiquetas
    titulo_match = re.search(r'\[TITULO\](.*?)\[/TITULO\]', texto, re.DOTALL)
    escaleta_match = re.search(r'\[ESCALETA\](.*?)\[/ESCALETA\]', texto, re.DOTALL)
    
    titulo_final = tema # Fallback
    headers = [f"Todo sobre {tema}", f"Análisis de {tema}", "Conclusión"] # Fallback

    if titulo_match:
        raw_title = titulo_match.group(1).strip()
        titulo_final = limpiar_titulo(raw_title)
    
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

# --- FASE B: EL ESCRITOR (Bloques - Estilo WEF) ---
def escribir_bloque(encabezado, titulo_articulo, hub_info):
    print(f"✍️ FASE B: Escribiendo bloque '{encabezado}'...")
    
    contexto_link = ""
    if hub_info:
        contexto_link = f"IMPORTANTE: Intenta mencionar el concepto '{hub_info['keyword']}' de forma natural e incluye este enlace Markdown: [{hub_info['keyword']}]({hub_info['url']}). Si no encaja, no lo fuerces."

    # PROMPT "GLOBAL AUTHORITY (WEF)" REFINADO
    prompt = f"""
    ACTÚA COMO UN ANALISTA SENIOR DE UN FORO ECONÓMICO GLOBAL.
    TU OBJETIVO ES REDACTAR LA SECCIÓN: "{encabezado}" 
    PARA EL ARTÍCULO TITULADO: "{titulo_articulo}".

    --- REGLAS DE ORO DE FORMATO (ESTRICTO) ---
    1. PROHIBIDO: Escribir títulos (# o ##) dentro de este bloque. El script ya los pone.
    2. PROHIBIDO: Usar etiquetas administrativas como "CONTENIDO:", "SECCIÓN:" o "INTRODUCCIÓN:".
    3. PROHIBIDO: Saludos, meta-comentarios o feedback hacia el usuario.
    4. ESTILO: Redacción técnica, profesional y neutral. Evita el tono sensacionalista.
    5. PÁRRAFOS: Máximo de 4 a 6 líneas por párrafo para garantizar legibilidad.
    6. NEGRILLAS: Úsalas exclusivamente para resaltar 1 o 2 conceptos clave por sección. No resaltes frases enteras.
    7. ESPACIADO: Separa cada párrafo con exactamente dos saltos de línea (\\n\\n).

    --- ESTRUCTURA TÉCNICA ---
    - Comienza directamente con el texto analítico.
    - Si presentas datos comparativos, usa una tabla Markdown limpia sin bordes innecesarios.
    - Si incluyes una lista, usa viñetas sencillas (-) con una breve explicación.
    - {contexto_link}

    SALIDA: Solo el texto Markdown final. Si incluyes etiquetas de IA, el sistema descartará tu respuesta.
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return limpiar_tags(response.text)

# --- FASE C: EL EDITOR (Ensamblaje y FAQ) ---
def generar_faq(contenido_total, tema):
    print("🧠 FASE C: Generando FAQ Dual (Visual + JSON-LD)...")
    prompt = f"""
    Basado en: "{tema}".
    Genera 5 Preguntas Frecuentes.
    
    FORMATO DE SALIDA OBLIGATORIO (Usa estas etiquetas):
    
    [VISUAL]
    ### ¿Pregunta 1?
    Respuesta breve.
    ### ¿Pregunta 2?
    Respuesta breve.
    ...
    [/VISUAL]
    
    [SCRIPT]
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      ...
    }}
    </script>
    [/SCRIPT]
    
    REGLA: En [SCRIPT], NO uses bloques de código Markdown (```). Solo el raw script.
    """
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    # Parsing
    visual = ""
    script = ""
    
    v_match = re.search(r'\[VISUAL\](.*?)\[/VISUAL\]', response.text, re.DOTALL)
    s_match = re.search(r'\[SCRIPT\](.*?)\[/SCRIPT\]', response.text, re.DOTALL)
    
    if v_match: visual = v_match.group(1).strip()
    if s_match: script = s_match.group(1).strip().replace('```html', '').replace('```json', '').replace('```', '')
    
    # Limpieza extra de etiquetas en visual
    visual = limpiar_tags(visual)
    
    return visual, script

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
    texto_raw = limpiar_tags(response.text)
    return [s.strip() for s in texto_raw.split(',')][:5]

def motor_de_contenidos(kw):
    print(f"\n🚀 INICIANDO MOTOR PARA: {kw}")
    
    is_hub, hub_info = gestionar_estado_hub(kw)
    
    # 1. Fase A: Estructura y Título
    titulo, headers = generar_estructura(kw)
    print(f"📌 Título Generado: {titulo}")
    
    # 2. Imagen
    imagen_url = generar_imagen(titulo)
    
    # 3. Intro
    intro_prompt = f"Escribe una intro profesional (200 palabras) para '{titulo}'. Estilo analista global. Directo al grano."
    intro_resp = client.models.generate_content(
        model='gemini-2.0-flash', contents=intro_prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    # 5. Sincronización Fase C (Ensamblaje sin duplicar título)
    # ELIMINADO EL # {titulo} AQUÍ PARA EVITAR DUPLICADOS EN HUGO
    contenido_completo = f"{limpiar_tags(intro_resp.text)}\n\n"
    
    for h in headers:
        bloque = escribir_bloque(h, titulo, hub_info)
        # Separación explícita
        contenido_completo += f"## {h}\n\n{bloque}\n\n"
        time.sleep(1)
    
    # 4. FAQ Dual
    faq_visual, faq_script = generar_faq(contenido_completo, kw)
    
    contenido_completo += f"\n\n## Preguntas Frecuentes\n{faq_visual}\n\n"
    contenido_completo += f"{faq_script}"
    
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
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = slug[:60]
    
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
