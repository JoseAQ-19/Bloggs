import os
import re
import frontmatter
import time
from dotenv import load_dotenv

# Importar motor visual (asumiendo que novum_visual está en la raíz)
# Necesitamos añadir el root al path en manage.py, pero aquí usamos import relativo o absoluto
# Como manage.py añade el root al sys.path, podemos importar desde root
try:
    from novum_visual import get_image
except ImportError:
    # Fallback si se ejecuta directo
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from novum_visual import get_image

load_dotenv()
CONTENT_DIR = "content"
STATIC_IMAGES = "static"
CORRUPT_THRESHOLD = 100000

def run_text_clean():
    print("🧹 [CLI] LIMPIANDO TEXTOS (TL;DR)...")
    patterns = [r'\*\*?TL;?DR.*?\*\*?:?', r'^Key Takeaways', r'^En resumen']
    count = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            filepath = os.path.join(root, filename)
            try:
                post = frontmatter.load(filepath)
                orig = post.content
                for p in patterns:
                    post.content = re.sub(p, '', post.content, flags=re.I|re.M).lstrip()
                if post.content != orig:
                    with open(filepath, 'wb') as f: frontmatter.dump(post, f)
                    count += 1
            except: pass
    print(f"✨ {count} archivos saneados.")

def run_image_clean():
    print("🎨 [CLI] LIMPIANDO IMÁGENES ROTAS (<100KB)...")
    fixed = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            filepath = os.path.join(root, filename)
            try:
                post = frontmatter.load(filepath)
                img_rel = post.get('featured_image', '').lstrip('/')
                if not img_rel: continue
                
                phys_path = os.path.join(STATIC_IMAGES, img_rel)
                needs_fix = False
                
                if not os.path.exists(phys_path): needs_fix = True
                elif os.path.getsize(phys_path) < CORRUPT_THRESHOLD: 
                    try: os.remove(phys_path)
                    except: pass
                    needs_fix = True
                
                if needs_fix:
                    print(f"   🔄 Regenerando: {filename}")
                    title = post.get('title')
                    slug = filename.replace('.md', '')
                    cat = os.path.basename(root)
                    new_img = get_image(title, slug, cat)
                    if new_img:
                        post['featured_image'] = new_img
                        with open(filepath, 'wb') as f: frontmatter.dump(post, f)
                        fixed += 1
            except Exception as e:
                print(f"❌ Error: {e}")
    print(f"✨ {fixed} imágenes reparadas.")
