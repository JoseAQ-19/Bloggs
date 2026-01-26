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
    # Lista de modelos a probar en orden de preferencia (Modernos -> Estables -> Legacy)
    candidates = ["gemini-1.5-flash", "gemini-1.5-flash-001", "gemini-1.5-pro"]
    
    last_error = None
    for model_name in candidates:
        try:
            print(f"🤖 Intentando usar modelo: {model_name}...")
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            print(f"✅ ¡Éxito con {model_name}!")
            return response.text
        except Exception as e:
            print(f"❌ Falló {model_name}: {e}")
            last_error = e
            # Si es error de cuota (429), fallamos inmediatamente, no sirve de nada cambiar de modelo
            if "429" in str(e) or "quota" in str(e).lower():
                print("⚠️ LÍMITE DE CUOTA ALCANZADO. Deteniendo intentos.")
                raise e
            continue

    print("💀 Ningún modelo funcionó.")
    raise last_error

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
