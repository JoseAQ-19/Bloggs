import os
import frontmatter
from novum_visual import NovumVisualEngine

# Configuración
CONTENT_DIR = "content/viral"

def audit_viral():
    print("🕵️‍♂️ AUTOPSIA DE LA SECCIÓN VIRAL...")
    
    # 1. INVESTIGACIÓN DE IMÁGENES (Prompts)
    print("\n[1] ANÁLISIS DE LÓGICA VISUAL:")
    prompt_template = NovumVisualEngine.AESTHETICS.get('viral')
    print(f"   - Estilo configurado para 'viral': \"{prompt_template}\"")
    print("   -> CAUSA PROBABLE: El estilo pide 'pop art', 'shocked emoji 3d', 'chaotic internet collage'. Esto genera contenido infantil.")

    # 2. INVESTIGACIÓN DEL DISEÑO (Archivos)
    print("\n[2] ANÁLISIS DE ESTRUCTURA Y DISEÑO:")
    
    # Check Frontmatter
    if os.path.exists(CONTENT_DIR):
        files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md') and not f.startswith('_')]
        if files:
            sample = os.path.join(CONTENT_DIR, files[0])
            post = frontmatter.load(sample)
            print(f"   - Muestra Frontmatter ({files[0]}):")
            print(f"     type: {post.get('type')}")
            print(f"     layout: {post.get('layout')}")
            print(f"     categories: {post.get('categories')}")
    
    # Check Layouts
    viral_layouts = []
    for root, dirs, files in os.walk("layouts"):
        if "viral" in root:
            viral_layouts.append(root)
    
    if viral_layouts:
        print(f"   - Carpetas de layout 'viral' encontradas: {viral_layouts}")
        print("   -> CAUSA PROBABLE: Si existe layouts/viral, Hugo la usa. Si está vacía o mal hecha, rompe el estilo.")
    else:
        print("   - No existen layouts específicos para 'viral' en root.")

    # Check CSS
    print("\n[3] ANÁLISIS CSS (custom.css):")
    # Simulación de lectura de custom.css (ya sé lo que escribí antes)
    print("   - Buscando regla '.theme-viral'...")
    # Voy a leer el archivo real para confirmar
    with open("static/css/custom.css", "r") as f:
        css = f.read()
        if ".theme-viral" in css:
            import re
            match = re.search(r'\.theme-viral\s*{([^}]*)}', css)
            if match:
                print(f"   - Regla encontrada: {match.group(1)}")
                if "background-color: #ffffff" in match.group(1):
                     print("   -> ¡CULPABLE ENCONTRADO! El CSS fuerza background blanco explícitamente.")

if __name__ == "__main__":
    audit_viral()
