import os
from google import genai
from github import Github
from datetime import datetime

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")

# Nuevo cliente de la librería moderna
client = genai.Client(api_key=GEMINI_KEY)

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
    try:
        # Revertimos a 1.5 Flash y añadimos control de errores
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO DE GEMINI:\n{e}\n")
        # Si es error de cuota (429), lo avisamos claro
        if "429" in str(e) or "quota" in str(e).lower():
            print("⚠️ HAS ALCANZADO EL LÍMITE DE USO GRATUITO. ESPERA UNOS MINUTOS.")
        # Si es error de modelo (404), listamos los disponibles
        elif "404" in str(e):
             print("⚠️ MODELO NO ENCONTRADO. Intentando listar modelos disponibles...")
             try:
                 for m in client.models.list(config={"page_size": 10}):
                     print(f" - {m.name}")
             except:
                 pass
        raise e

def guardar_archivo(titulo, contenido):
    # Formato para SSG (Hugo/Next.js)
    slug = titulo.replace(" ", "-").lower()
    path = f"content/posts/{slug}.md"
    # Formato de fecha simplificado como solicitado
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"---\ntitle: '{titulo}'\ndate: {date_str}\ndraft: false\n---\n\n"
    
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
