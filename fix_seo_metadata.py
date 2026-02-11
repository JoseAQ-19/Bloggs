import os
import re
import frontmatter
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configuración
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except:
    print("❌ Error: No API Key found.")
    exit(1)

CONTENT_DIR = "content"

def generate_seo_description(content):
    """Genera una meta descripción SEO segura."""
    try:
        prompt = f"""
        ACT AS: SEO Expert.
        TASK: Write a meta description for this article.
        CONTENT: {content[:1000]}
        
        RULES:
        1. Length: Max 150 chars.
        2. Tone: Engaging, click-worthy.
        3. NO QUOTES: Do not use double quotes (") in the output.
        4. Output ONLY the text.
        """
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        desc = resp.text.strip().replace('"', "'").replace('\n', ' ')
        return desc[:160] # Safety clip
    except:
        return "Análisis profundo sobre tecnología y tendencias digitales en NovumWorld."

def fix_seo_metadata():
    print("🚑 INICIANDO PROTOCOLO OMEGA (REMEDIACIÓN SEO)...")
    
    deleted_count = 0
    desc_injected = 0
    h1_purged = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            if filename.startswith("_index"): continue # SAGRADO
            
            filepath = os.path.join(root, filename)
            
            try:
                # Cargar post
                post = frontmatter.load(filepath)
                content = post.content.strip()
                word_count = len(content.split())
                
                # REGLA 1: PODA THIN CONTENT
                if filename == "index.md" or word_count < 200:
                    print(f"✂️ BORRANDO THIN CONTENT ({word_count} palabras): {filename}")
                    os.remove(filepath)
                    deleted_count += 1
                    continue
                
                modified = False
                
                # REGLA 2: INYECCIÓN METADATOS
                if not post.get('description'):
                    print(f"   📝 Generando descripción para: {filename}")
                    new_desc = generate_seo_description(content)
                    post['description'] = new_desc
                    modified = True
                    desc_injected += 1
                
                # REGLA 3: PURGA H1
                lines = content.split('\n')
                if lines:
                    first_line = lines[0].strip()
                    title = post.get('title', '').strip()
                    
                    if first_line.startswith('# ') or first_line.lower() == title.lower():
                        print(f"   🧹 Eliminando H1 duplicado en: {filename}")
                        lines.pop(0)
                        # Limpiar líneas vacías iniciales tras borrado
                        while lines and not lines[0].strip():
                            lines.pop(0)
                        post.content = '\n'.join(lines)
                        modified = True
                        h1_purged += 1
                
                # GUARDADO FINAL
                if modified:
                    # Truco para evitar problemas de YAML: usar handler seguro
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                        
            except Exception as e:
                print(f"❌ Error procesando {filename}: {e}")

    print(f"\n📊 REPORTE FINAL OMEGA:")
    print(f"   [ {deleted_count} ] Archivos borrados por Thin Content")
    print(f"   [ {desc_injected} ] Descripciones inyectadas")
    print(f"   [ {h1_purged} ] H1 purgados")

if __name__ == "__main__":
    fix_seo_metadata()
