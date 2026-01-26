import os
from google import genai # <--- Importación moderna
from github import Github
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

# 1. INICIALIZACIÓN (Igual que en tu proyecto)
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
    print(f"🤖 Generando con librería moderna para: {kw}...")
    
    prompt = f"Actúa como redactor experto. Escribe un artículo SEO en Markdown sobre: '{kw}'. Usa H2, H3 y tablas."
    
    # 2. GENERACIÓN
    # Usamos 'generate_content' en lugar de 'chats' porque es un solo artículo, no una conversación.
    # Usamos 'gemini-1.5-flash' para GARANTIZAR que sea gratis y no falle la cuota.
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    return response.text

def guardar_post(titulo, contenido):
    slug = titulo.replace(" ", "-").lower()
    filename = f"content/posts/{slug}.md"
    fecha = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    front_matter = f"---\ntitle: '{titulo}'\ndate: {fecha}\ndraft: false\n---\n\n"
    
    g = Github(GH_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        repo.create_file(filename, f"Post: {titulo}", front_matter + contenido, branch="main")
        print(f"✅ PUBLICADO: {filename}")
    except Exception as e:
        print(f"⚠️ Error GitHub: {e}")

if __name__ == "__main__":
    keyword = obtener_keyword()
    if keyword:
        try:
            texto = generar_articulo(keyword)
            if texto:
                guardar_post(keyword, texto)
        except Exception as e:
            print(f"🔥 Error: {e}")
            exit(1)
    else:
        print("💤 Lista vacía.")
