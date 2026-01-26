import os
import google.generativeai as genai
from github import Github
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp') # Versión experimental rápida y astuta

def obtener_keyword():
    if not os.path.exists('data/keywords.txt'): return None
    with open('data/keywords.txt', 'r') as f:
        lines = f.readlines()
    if not lines: return None
    
    selected = lines[0].strip()
    # Guardamos el resto de keywords
    with open('data/keywords.txt', 'w') as f:
        f.writelines(lines[1:])
    return selected

def generar_articulo(kw):
    prompt = f"Escribe un artículo SEO optimizado en Markdown sobre: {kw}. Incluye H2, H3, tablas y FAQ."
    response = model.generate_content(prompt)
    return response.text

def guardar_archivo(titulo, contenido):
    # Formato para SSG (Hugo/Next.js)
    slug = titulo.replace(" ", "-").lower()
    path = f"content/posts/{slug}.md"
    header = f"---\ntitle: '{titulo}'\ndate: {datetime.now().isoformat()}\ndraft: false\n---\n\n"
    
    os.makedirs('content/posts', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header + contenido)
    print(f"✅ Archivo {path} creado localmente.")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        print(f"🚀 Procesando: {keyword}")
        texto = generar_articulo(keyword)
        guardar_archivo(keyword, texto)
    else:
        print("⚠️ No hay más palabras clave en la lista.")
