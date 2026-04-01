import os
import frontmatter
from dotenv import load_dotenv
from google import genai
from novum_visual import get_image

# Config
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

TARGET_SUBSTRING = "alma-college"
CONTENT_ROOT = "content/fitness"
STATIC_ROOT = "static"

def fix_alma_college():
    print("🔧 REPARANDO CASO 'ALMA COLLEGE' (MODO OFFLINE)...")
    
    for filename in os.listdir(CONTENT_ROOT):
        if TARGET_SUBSTRING in filename:
            filepath = os.path.join(CONTENT_ROOT, filename)
            print(f"   Procesando: {filename}")
            
            try:
                post = frontmatter.load(filepath)
                
                # 1. Limpiar Descripción con Regex (No IA)
                old_desc = post.get('description', '')
                clean_desc = old_desc
                if "TL;DR" in old_desc or "Bro-Science" in old_desc:
                     # Quedarse con la primera frase lógica o truncar
                     # Simplemente quitamos la basura conocida
                     clean_desc = "Alma College's Kinesiology program bridges the gap between old-school dogma and evidence-based biohacking for hypertrophy and longevity."
                
                post['description'] = clean_desc
                print(f"      ✅ Desc Limpia: {clean_desc[:50]}...")
                
                # 2. Regenerar Imagen (Force FLUX)
                slug = filename.replace('.md', '')
                img_rel = post.get('featured_image', '').lstrip('/')
                img_phys = os.path.join(STATIC_ROOT, img_rel)
                
                if os.path.exists(img_phys):
                    os.remove(img_phys) # Borrar la caja negra
                
                # Usamos el título como prompt base
                new_img_path = get_image(post['title'], slug, category="fitness")
                if new_img_path:
                     post['featured_image'] = new_img_path
                     print(f"      ✅ Nueva Imagen FLUX: {new_img_path}")
                
                # Guardar
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    fix_alma_college()
