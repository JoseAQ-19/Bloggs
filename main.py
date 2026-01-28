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
import unicodedata

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

client = genai.Client(api_key=GEMINI_KEY)

# 1. FORZAR MODO MÁQUINA (Instrucción de Sistema)
SYSTEM_INSTRUCTION = """
Eres un ANALISTA SENIOR EXPERTO en Geopolítica, Tecnología y Economía.
Escribes para NOVUMWORLD, un medio de élite.

TU PERSONALIDAD ("REALI-TEA"):
1. OPINIÓN FUERTE: No eres neutral. Usas la 1ª persona ("En mi análisis...", "Sostengo que...").
2. CRÍTICO: Señalas sin piedad los fallos del mercado, las mentiras corporativas y las contradicciones.
3. DATA-DRIVEN: Tus argumentos se basan en los HECHOS REALES suministrados. No inventas cifras.

PROHIBIDO TERMINANTEMENTE:
- GENERAR TABLAS. (Usa listas de puntos para datos).
- Ser "tibio" o "enciclopédico".
- Usar frases de IA como "En conclusión" o "Es importante destacar".
- Repetir el título de la sección al inicio.
- Saludos o meta-comentarios.

TU OBJETIVO: Escribir el mejor análisis en español de 2026.
"""

HUB_STATE_FILE = 'data/hub_state.json'
KEYWORDS_FILE = 'data/keywords.txt'
DB_FILE = 'data/articulos_data.json'
COMPLETED_FILE = 'data/completed.txt'

# Cargar BD en memoria
MASTER_DB = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        try:
            MASTER_DB = json.load(f)
        except:
            MASTER_DB = {}

def generar_slug(texto):
    slug = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    slug = slug.replace(" ", "-").lower()
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = slug[:50].strip('-') # Evitar guiones al final tras el recorte
    
    # Fallback si el título solo contenía símbolos/emojis
    if not slug:
        slug = f"post-{int(time.time())}"
        
    return slug

def recargar_keywords_si_vacio():
    """
    Si keywords.txt está vacío, lo rellena con las claves de MASTER_DB
    que NO estén en data/completed.txt
    """
    if not MASTER_DB: 
        return []
    
    print("🔄 Lista vacía. Verificando historial de completados...")
    
    completed = set()
    if os.path.exists(COMPLETED_FILE):
        with open(COMPLETED_FILE, 'r') as f:
            # Normalizamos al cargar el historial
            completed = {line.strip().lower() for line in f if line.strip()}
    
    nuevos_temas = []
    print(f"📊 Analizando {len(MASTER_DB)} temas de la BD frente a {len(completed)} ya completados...")

    for tema in MASTER_DB.keys():
        if tema.strip().lower() not in completed:
            nuevos_temas.append(tema)
        else:
            print(f"  ⏭️ Saltando (Ya completado): {tema[:30]}...")
    
    if nuevos_temas:
        with open(KEYWORDS_FILE, 'w') as f:
            for k in nuevos_temas:
                f.write(f"{k}\n")
        print(f"✅ RECARGA EXITOSA: {len(nuevos_temas)} temas añadidos a la cola.")
        return nuevos_temas
    else:
        print("⚠️ No quedan temas pendientes en la BD (todos marcados como completados).")
        return []

def registrar_completado(tema):
    try:
        os.makedirs('data', exist_ok=True)
        with open(COMPLETED_FILE, 'a') as f:
            f.write(f"{tema.strip().lower()}\n")
        
        # --- LIMPIEZA DE BASE DE DATOS MAESTRA ---
        # Buscamos la clave real (case-insensitive) para borrarla
        db_lookup = {k.strip().lower(): k for k in MASTER_DB.keys()}
        real_key = db_lookup.get(tema.strip().lower())
        
        if real_key:
            del MASTER_DB[real_key]
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(MASTER_DB, f, ensure_ascii=False, indent=2)
            print(f"🗑️ Tema eliminado de la base de datos maestra: {real_key[:30]}...")
            
        print(f"🏁 Tema registrado como completado: {tema[:30]}...")
    except Exception as e:
        print(f"⚠️ Error registrando completado/limpiando BD: {e}")

def obtener_keyword():
    lines = []
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, 'r') as f:
            lines = [l for l in f.readlines() if l.strip()]
    
    # Si no hay líneas válidas, intentamos recargar
    if not lines:
        nuevos = recargar_keywords_si_vacio()
        if nuevos:
            lines = [f"{t}\n" for t in nuevos]
        else:
            return None, None
    
    # --- FILTRO BLINDADO ANTI-GIT ---
    topic_limpio = None
    idx_found = -1
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("<<<<") or line.startswith("====") or line.startswith(">>>>"):
            continue
        
        possible_topic = re.sub(r'^[<>=]{7}.*?:\s*', '', line).strip()
        
        if possible_topic and not topic_limpio:
            topic_limpio = possible_topic
            idx_found = i
            break
            
    if not topic_limpio:
        return None, None
        
    lineas_restantes = lines[:idx_found] + lines[idx_found+1:]
    
    # --------------------------------
    
    # Buscar en la BD Maestra (Case-Insensitive Lookup)
    db_lookup = {k.strip().lower(): k for k in MASTER_DB.keys()}
    real_key = db_lookup.get(topic_limpio.strip().lower())
    
    dossier = MASTER_DB.get(real_key, {}) if real_key else {}
    
    if dossier:
        context_data = json.dumps(dossier, ensure_ascii=False, indent=2)
    else:
        context_data = "No hay datos específicos. Usa tu conocimiento general pero SÉ CRÍTICO."

    with open(KEYWORDS_FILE, 'w') as f:
        for l in lineas_restantes:
             if not l.endswith('\n'): l += '\n'
             f.write(l)
             
    return topic_limpio, context_data

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

    # --- VERIFICACIÓN DE EXISTENCIA FÍSICA (Auto-Reparación) ---
    if state and 'hub_slug' in state:
        expected_file = f"content/posts/{state['hub_slug']}.md"
        if not os.path.exists(expected_file):
            print(f"🚨 ALERTA: El Hub '{state['hub_slug']}' ha desaparecido físicamente. Reseteando memoria.")
            state = {} # Borrado de emergencia por inconsistencia

    is_hub = False
    hub_info = None

    if not state or state.get('spokes_left', 0) <= 0:
        # Nuevo HUB
        is_hub = True
        state = {
            'hub_keyword': tema_actual,
            'hub_slug': tema_actual.replace(" ", "-").lower(), # Placeholder, se actualizará al guardar
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
    
    # IMPORTANTE: Si es Hub, el slug real se guardará después de generar el título. 
    # Devolvemos el estado parcial, y luego `motor_de_contenidos` actualizará el slug correcto tras generar el título.
    
    return is_hub, hub_info, state

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

# --- HERRAMIENTAS DE LIMPIEZA FINAL (GLASS CLEANER) ---
def limpiar_contenido_final(texto):
    if not texto: return ""
    
    # 1. Backslash Hunter (Mata líneas que solo son \)
    texto = re.sub(r'^\s*\\\s*$', '', texto, flags=re.MULTILINE)
    
    # 2. Sanitización de Etiquetas Prohibidas
    prohibidas = ["TÍTULO:", "TITLE:", "INTRODUCCIÓN:", "INTRO:", "META-DESCRIPCIÓN:", "CONTENIDO:", "SECCIÓN:", "CONCLUSIÓN:"]
    for p in prohibidas:
        texto = re.sub(f"^{p}\s*", "", texto, flags=re.IGNORECASE | re.MULTILINE)
    
    # 3. Reparar Newlines literales
    texto = texto.replace('\\n', '\n')
    
    # 4. Island Logic (Aire para tablas)
    # Lógica línea por línea para asegurar \n\n alrededor del bloque de tabla
    lines = texto.splitlines()
    processed_lines = []
    in_table = False
    
    for i, line in enumerate(lines):
        clean_line = line.strip()
        is_table_row = clean_line.startswith('|')
        
        # Ignorar líneas vacías en la detección de estado, pero conservarla sueltas
        if not clean_line:
            processed_lines.append(line)
            continue
            
        if is_table_row:
            if not in_table:
                # START OF TABLE
                in_table = True
                # Ensure spacing before: Add empty line if prev line wasn't empty
                if processed_lines and processed_lines[-1].strip():
                     processed_lines.append("")
        else:
             if in_table:
                 # END OF TABLE
                 in_table = False
                 # Ensure spacing after: Add empty line
                 processed_lines.append("")
        
        processed_lines.append(line)
        
    texto = "\n".join(processed_lines)
    
    return texto.strip()

def limpiar_eco_encabezado(texto, encabezado):
    """
    Elimina el encabezado si aparece repetido al inicio del texto (Line-by-Line Inspection).
    """
    lines = texto.strip().splitlines()
    cleaned_lines = []
    header_found = False
    
    # Analyze first 3 non-empty lines for echoes
    scan_limit = 3
    scanned_count = 0
    
    norm_header = re.sub(r'[^\w\s]', '', encabezado.lower())

    for i, line in enumerate(lines):
        clean_line = line.strip()
        
        # If we passed the safety zone, just add the rest
        if scanned_count >= scan_limit:
            cleaned_lines.append(line)
            continue
            
        if not clean_line:
            # Keep empty lines but don't count them towards scan limit if we haven't started content
            if cleaned_lines: 
                cleaned_lines.append(line)
            continue

        scanned_count += 1
        
        # CHECK 1: Starts with Markdown Header (#) 
        if clean_line.startswith('#'):
            continue # Drop this line
            
        # CHECK 2: Fuzzy Match with Header
        norm_line = re.sub(r'[^\w\s]', '', clean_line.lower())
        
        # Check if line IS the header (or very close)
        if norm_line == norm_header or norm_line.startswith(norm_header):
            continue # Drop this line
            
        # CHECK 3: Common Intro Phrases
        if any(clean_line.lower().startswith(p.lower()) for p in [
            f"Todo sobre {encabezado}",
            f"En este apartado",
            f"Como vemos en",
            "A continuación",
            "En esta sección"
        ]):
            continue # Drop
            
        # If it survived, it's real content
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines).strip()

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
def generar_estructura(tema, context_data, is_hub):
    print("🏗️ FASE A: Arquitecto diseñando la estructura...")
    
    num_headers = 10 if is_hub else 7
    tipo_articulo = "GUIDE (Gran Formato)" if is_hub else "Artículo Standard"
    
    prompt = f"""
    Tema: "{tema}".
    Datos Reales: "{context_data}"
    Tipo: {tipo_articulo}
    
    TAREA:
    1. Genera un Título Viral y Provocador (Estilo Bloomberg/Vice).
    2. Genera una lista JSON ESTRICTA de {num_headers} encabezados (H2).
    
    REGLA CLAVE PARA ENCABEZADOS (H2):
    - Conceptos cortantes ("La Gran Mentira", "El Colapso"). Máximo 4 palabras.
    - Sácale jugo a los Datos Reales.

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

# --- FASE B: EL ESCRITOR (Anti-Echo + Glass Cleaner + Strict Tables) ---
def escribir_bloque(encabezado, titulo_articulo, hub_info, context_data):
    print(f"✍️ FASE B: Escribiendo bloque '{encabezado}'...")
    
    instruccion_spoke = ""
    if hub_info:
        instruccion_spoke = f"""
        IMPORTANTE (SPOKE): Este artículo es satélite de la Guía Principal sobre '{hub_info['keyword']}'.
        DEBES mencionar brevemente la 'Guía Principal' y enlazarla así: [Ver Guía Principal]({hub_info['url']}).
        Hazlo de forma natural en el texto.
        """

    prompt = f"""
    ACTÚA COMO UN ANALISTA SENIOR (ESTILO 'REALI-TEA').
    Tienes este DOSSIER TÉCNICO EXCLUSIVO (JSON):
    ```json
    {context_data}
    ```
    
    MANDATO DE VERACIDAD:
    - Esta es tu ÚNICA fuente de verdad. Tienes prohibido contradecir estas cifras.
    - Úsalas como base de tus argumentos.
    - Si el dossier contiene datos negativos o pérdidas, ACTIVA EL MODO "HONESTIDAD BRUTAL". No suavices la realidad. Explícala.
    
    REDACTA LA SECCIÓN: "{encabezado}" PARA EL ARTÍCULO: "{titulo_articulo}".
    
    --- REGLAS DE ORO DE ESCRITURA ---
    1. PROHIBIDO USAR CONTRABARRA '\\' PARA ESCAPAR TEXTO.
    2. ANTI-ECHO (CRÍTICO): PROHIBIDO EMPEZAR EL PÁRRAFO REPITIENDO EL TÍTULO DE LA SECCIÓN.
    3. SÍNTESIS NARRATIVA (SIN TABLAS): Usa listas de viñetas (*) para datos.
    4. TONO: Usa la 1ª persona ("Mi lectura es...", "Observo que..."). Sé crítico. Cita los HECHOS REALES para validar tu tesis.
    
    {instruccion_spoke}

    --- REGLAS DE ORO DE DISEÑO ---
    1. JERARQUÍA PLANA: No uses subtítulos (#, ##, ###) dentro de este bloque.
    2. NEGRITAS QUIRÚRGICAS: Úsalas SOLO para resaltar 1 concepto técnico clave (máximo 2 palabras).
    

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

# --- FASE C: ESTRATEGA DE SEO (Con Catálogo Real) ---
def obtener_catalogo_real():
    posts = []
    if not os.path.exists('content/posts'):
        return []
        
    for f in os.listdir('content/posts'):
        if f.endswith('.md'):
            path = os.path.join('content/posts', f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.readlines()
                    # Buscamos title: en las primeras líneas
                    for line in content[:10]:
                        match = re.search(r'title:\s*[\'"](.*?)[\'"]', line)
                        if match:
                            title = match.group(1)
                            slug = f.replace('.md', '')
                            posts.append(f"- [{title}](/posts/{slug})")
                            break
            except:
                pass
    return posts

def generar_relacionados(tema):
    catalog = obtener_catalogo_real()
    
    # Regla del Desierto: Si hay pocos posts, mejor no poner nada
    if len(catalog) < 3:
        print("📭 Catálogo insuficiente para interlinking (<3). Omitiendo sección.")
        return ""

    print(f"🧠 FASE C: Generando Estrategia de Enlazado (Basada en {len(catalog)} artículos reales)...")
    
    # Seleccionamos aleatoriamente unos cuantos para no saturar el prompt si hay muchos
    sample_catalog = "\n".join(random.sample(catalog, min(len(catalog), 30)))
    
    prompt = f"""
    ACTÚA COMO UN ESTRATEGA DE SEO.
    Tienes este CATÁLOGO REAL de artículos existentes en el blog:
    
    {sample_catalog}
    
    TAREA: Selecciona 3 artículos de esa lista que se relacionen mejor con: "{tema}".
    
    REGLA DE ORO:
    - SOLO puedes elegir enlaces de la lista de arriba.
    - PROHIBIDO inventar o alucinar títulos. Si no está en la lista, no existe.
    - Si ninguno encaja perfecto, elige los más recientes.
    
    FORMATO (Lista Markdown):
    * [Título Real](/posts/slug-real)
    * [Título Real](/posts/slug-real)
    * [Título Real](/posts/slug-real)
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

def motor_de_contenidos(kw, context_data):
    print(f"\n🚀 INICIANDO MOTOR PARA: {kw}")
    
    is_hub, hub_info, state_obj = gestionar_estado_hub(kw)
    
    titulo, headers = generar_estructura(kw, context_data, is_hub)
    print(f"📌 Título Generado: {titulo}")
    
    # --- Actualización Crítica del State si es Hub ---
    # Necesitamos el slug REAL generado a partir del título, no el teórico
    if is_hub:
        real_slug = generar_slug(titulo)
        state_obj['hub_slug'] = real_slug
        # Guardamos ahora que tenemos el slug definitivo
        os.makedirs('data', exist_ok=True)
        with open(HUB_STATE_FILE, 'w') as f:
            json.dump(state_obj, f)
    elif state_obj:
        # Si es Spoke, solo guardamos el decremento del contador
        os.makedirs('data', exist_ok=True)
        with open(HUB_STATE_FILE, 'w') as f:
            json.dump(state_obj, f)
    # -----------------------------------------------
    
    imagen_url = generar_imagen(titulo)
    
    intro_prompt = f"""
    Escribe una INTRODUCCIÓN DURA Y DIRECTA (200 palabras) para '{titulo}'.
    Usa este DOSSIER: 
    ```json
    {context_data}
    ```
    Empieza con una frase corta y demoledora.
    Estilo: Analista Senior (1ª persona). Si hay datos alarmantes, empieza por ahí.
    """
    intro_resp = client.models.generate_content(
        model='gemini-2.0-flash', contents=intro_prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    
    intro_texto = limpiar_contenido_final(intro_resp.text)
    contenido_completo = f"{intro_texto}\n\n"
    
    for h in headers:
        bloque = escribir_bloque(h, titulo, hub_info, context_data)
        contenido_completo += f"## {h}\n\n{bloque}\n\n"
        time.sleep(1)
    
    bloque_relacionados = generar_relacionados(titulo)
    contenido_completo += f"\n\n{bloque_relacionados}\n\n"
    
    if is_hub:
        try:
            subtemas = extraer_subtemas(contenido_completo)
            prepend_keywords(subtemas) # Hub spokes don't have context data yet, simple strings
            print(f"🔗 Spokes añadidos: {subtemas}")
        except:
            pass
    
    return titulo, contenido_completo, imagen_url

def guardar_localmente(titulo, contenido, imagen_url):
    # Uso de la función helper factorizada
    slug = generar_slug(titulo)
    
    os.makedirs('content/posts', exist_ok=True)
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # SANITIZACIÓN DE TÍTULO PARA FRONT MATTER
    # Eliminar comillas simples y dobles internas para evitar rotura de YAML
    titulo_limpio = titulo.replace("'", "").replace('"', "")
    
    image_fm = f"featured_image: '{imagen_url}'" if imagen_url else ""
    front_matter = f"---\ntitle: '{titulo_limpio}'\ndate: {fecha}\ndraft: false\n{image_fm}\n---\n\n"
    
    contenido = limpiar_contenido_final(contenido)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + contenido)
    print(f"✅ Artículo guardado: {filename}")

if __name__ == "__main__":
    keyword, context_data = obtener_keyword()
    if keyword:
        try:
            # We assume context_data is valid string even if empty
            titulo, texto, imagen_url = motor_de_contenidos(keyword, context_data)
            if texto:
                guardar_localmente(titulo, texto, imagen_url)
                registrar_completado(keyword)
        except Exception as e:
            print(f"🔥 Error Crítico: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    else:
        print("💤 Lista vacía.")
