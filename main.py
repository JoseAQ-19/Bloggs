import os
import requests
import json
from google import genai
from datetime import datetime

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

def generar_articulo(kw):
    print(f"🤖 Generando con Gemini 2.0 Flash: {kw}")
    prompt = f"Actúa como experto SEO. Escribe un artículo de blog en Markdown sobre: '{kw}'. Incluye H2, H3 y una tabla."
    
    # Usamos el modelo 2.0 que ahora SÍ funciona gracias a tu facturación
    response = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt
    )
    return response.text

def guardar_localmente(titulo, contenido):
    slug = titulo.replace(" ", "-").lower()
    # Aseguramos que la carpeta exista
    os.makedirs('content/posts', exist_ok=True)
    
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\n---\n\n"
    
    # GUARDADO LOCAL (GitHub Actions lo subirá después)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(front_matter + contenido)
    print(f"✅ Archivo guardado localmente: {filename}")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        try:
            texto = generar_articulo(keyword)
            if texto:
                guardar_localmente(keyword, texto)
        except Exception as e:
            print(f"🔥 Error: {e}")
            exit(1)
    else:
        print("💤 Lista vacía.")
