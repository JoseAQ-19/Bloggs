import os
import shutil
import frontmatter
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except:
    client = None

CONTENT_ROOT = "content"

def detect_language_score(text):
    text = text.lower()
    # Stopwords simples
    english_score = sum(1 for w in [" the ", " is ", " and ", " of ", " to ", " in "] if w in text)
    spanish_score = sum(1 for w in [" el ", " es ", " y ", " de ", " para ", " en "] if w in text)
    return "en" if english_score > spanish_score else "es"

def translate_title(title):
    if not client: return title
    try:
        prompt = f"Translate this blog title to Spanish. Make it viral. Output ONLY text. Title: {title}"
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return resp.text.strip().replace('"', '').replace("'", "")
    except:
        return title

def babel_fix():
    print("🌍 INICIANDO OPERACIÓN BABEL (LIMPIEZA IDIOMÁTICA)...")
    
    count_moved = 0
    count_spanglish = 0
    
    # Recorrer carpetas de idiomas
    for lang_folder in ["es", "en"]:
        base_path = os.path.join(CONTENT_ROOT, lang_folder)
        if not os.path.exists(base_path): continue
        
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                if not filename.endswith(".md") or filename.startswith("_index"): continue
                
                filepath = os.path.join(root, filename)
                
                try:
                    post = frontmatter.load(filepath)
                    content_text = post.content[:2000] # Muestra suficiente
                    title = post.get('title', '')
                    
                    # 1. DETECCIÓN DE IDIOMA REAL
                    real_lang = detect_language_score(content_text + " " + title)
                    
                    # CASO A: Archivo en carpeta incorrecta
                    if real_lang != lang_folder:
                        # Calcular nueva ruta (espejo)
                        # Reemplaza /es/ por /en/ o viceversa
                        new_root = root.replace(f"/{lang_folder}", f"/{real_lang}")
                        os.makedirs(new_root, exist_ok=True)
                        dest_path = os.path.join(new_root, filename)
                        
                        if os.path.exists(dest_path):
                            print(f"   🗑️ Borrando duplicado intruso: {filename} (Es {real_lang} en carpeta {lang_folder})")
                            os.remove(filepath)
                        else:
                            print(f"   📦 Moviendo {filename} de /{lang_folder}/ a /{real_lang}/")
                            # Actualizar frontmatter
                            post['language'] = real_lang
                            with open(filepath, 'wb') as f:
                                frontmatter.dump(post, f)
                            shutil.move(filepath, dest_path)
                            count_moved += 1
                        continue # Ya movido, siguiente
                        
                    # CASO B: Spanglish (Solo en ES)
                    if real_lang == "es":
                        # Si el título parece inglés (tiene palabras clave muy inglesas)
                        if " the " in title.lower() or " how to " in title.lower() or " guide " in title.lower():
                            print(f"   🇪🇸 Detectado Spanglish en Título: {title}")
                            new_title = translate_title(title)
                            print(f"      -> Traducido: {new_title}")
                            post['title'] = new_title
                            
                            # Guardar cambios
                            with open(filepath, 'wb') as f:
                                frontmatter.dump(post, f)
                            count_spanglish += 1
                            
                    # CASO C: Inyección TranslationKey
                    # Usamos el slug base (nombre archivo sin extensión y sin sufijo idioma si lo tuviera)
                    # Ejemplo: bitcoin-crash-en.md -> bitcoin-crash
                    base_key = filename.replace("-en.md", "").replace(".md", "")
                    
                    # Solo inyectar si no existe
                    if not post.get('translationKey'):
                        post['translationKey'] = base_key
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                        # print(f"   🔑 Key inyectada: {base_key}")

                except Exception as e:
                    print(f"❌ Error en {filename}: {e}")

    print(f"\n🌍 BABEL FINALIZADO.")
    print(f"   Archivos Movidos: {count_moved}")
    print(f"   Títulos Traducidos: {count_spanglish}")

if __name__ == "__main__":
    babel_fix()
