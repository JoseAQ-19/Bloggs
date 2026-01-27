import os
import requests
import json
from google import genai
from google.genai import types
from datetime import datetime
import random
import urllib.parse

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

client = genai.Client(api_key=GEMINI_KEY)

def obtener_keyword():
    path = 'data/keywords.txt'
    if not os.path.exists(path): return None
    with open(path, 'r') as f:
        lines = f.readlines()
    if not lines: return None
    selected = lines[0].strip()
    with open(path, 'w') as f:
        f.writelines(lines[1:])
    return selected

def generar_imagen(titulo):
    print(f"🎨 Pintando imagen con Flux (Pollinations): {titulo}")
    try:
        # PASO A: El Arquitecto (Gemini crea el prompt visual)
        prompt_arquitecto = f"Actúa como un Director de Arte experto. Escribe una descripción visual muy detallada, en INGLÉS, para una imagen fotorealista y cinemática sobre: '{titulo}'. Debe ser una sola frase larga. SIN comillas ni introducciones."
        
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt_arquitecto
        )
        
        # PASO B: Limpieza
        descripcion_visual = response.text.strip().replace('"', '').replace("'", "")
        print(f"👁️ Prompt Visual: {descripcion_visual}")
        
        # PASO C: Semilla Mágica
        seed = random.randint(0, 1000000)
        
        # PASO D: Construcción de la URL (Flux)
        # Usamos urllib.parse.quote para asegurar que la URL sea válida
        prompt_encoded = urllib.parse.quote(descripcion_visual)
        imagen_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=flux&width=1280&height=720&seed={seed}&nologo=true"
        
        # PASO E: Retorno
        print(f"🔗 URL Generada: {imagen_url}")
        return imagen_url

    except Exception as e:
        print(f"⚠️ Error generando imagen: {e}")
        return None

def generar_articulo(kw):
    print(f"🤖 Generando con Gemini 2.0 Flash: {kw}")
    tema = kw
    # PROMPT DE INGENIERÍA: MODO COLUMNISTA DE OPINIÓN SENIOR (HUMANO)
    prompt = f"""
    Actúa como un columnista experto y crítico para 'NovumWorld'. No seas neutral. Tienes opiniones fuertes. Usa un tono conversacional, irónico a veces, y directo.
    
    Vas a escribir sobre: "{tema}".

    REGLAS DE ORO (INSTRUCCIONES MAESTRAS):
    1. PROHIBIDO SALUDAR: Empieza el artículo directamente con una frase impactante o una pregunta retórica. No digas "¡Claro!", ni "Aquí tienes el artículo", ni "En este post vamos a ver...".
    2. ESTRUCTURA HUMANA: Evita el exceso de listas. Prioriza los párrafos narrativos. Usa metáforas y ejemplos de la vida real. No uses frases cliché como "En el mundo digital de hoy..." o "Es importante destacar...".
    3. ESTRUCTURA MARKDOWN: Usa H1 para el título y H2 para subtítulos, pero intégralos orgánicamente.
    4. CIERRE SIN MARKETING: El final debe ser una reflexión abierta o una conclusión tajante. PROHIBIDO pedir que se suscriban, que dejen comentarios o que compartan en redes sociales. Termina con un punto final y ya.
    5. IDIOMA: Español Neutro natural.

    Escribe la columna completa ahora:
    """
    
    
    # Usamos el modelo 2.0 que ahora SÍ funciona gracias a tu facturación
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt
    )
    
    # Generar imagen
    imagen_url = generar_imagen(kw)
    
    return response.text, imagen_url

def guardar_localmente(titulo, contenido, imagen_url):
    slug = titulo.replace(" ", "-").lower()
    # Aseguramos que la carpeta exista
    os.makedirs('content/posts', exist_ok=True)
    
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Frontmatter con imagen si existe
    if imagen_url:
        front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\nimage: '{imagen_url}'\n---\n\n"
    else:
        front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\n---\n\n"
    
    # GUARDADO LOCAL (GitHub Actions lo subirá después)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + contenido)
    print(f"✅ Archivo guardado localmente: {filename}")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        try:
            texto, imagen_url = generar_articulo(keyword)
            if texto:
                guardar_localmente(keyword, texto, imagen_url)
        except Exception as e:
            print(f"🔥 Error: {e}")
            exit(1)
    else:
        print("💤 Lista vacía.")
