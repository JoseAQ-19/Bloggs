import os
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"
CORRUPT_THRESHOLD = 120000 # 120 KB

def create_static_pages():
    print("📄 Verificando páginas estáticas...")
    pages = {
        "about.md": "Sobre Nosotros",
        "contact.md": "Contacto",
        "privacy.md": "Política de Privacidad"
    }
    for filename, title in pages.items():
        path = os.path.join(CONTENT_ROOT, filename)
        if not os.path.exists(path):
            print(f"   ➕ Creando {filename}...")
            with open(path, "w") as f:
                f.write(f"---\ntitle: \"{title}\"\nlayout: \"single\"\nurl: \"/{filename.replace('.md','')}/\"\n---\n\nContenido pendiente.")

def deep_clean():
    print("☢️ INICIANDO LIMPIEZA PROFUNDA (Together/Nebius)...")
    create_static_pages()
    
    fixed_count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            try:
                post = frontmatter.load(filepath)
                image_rel = post.get('featured_image', '')
                
                needs_fix = False
                
                # Check 1: No imagen
                if not image_rel:
                    needs_fix = True
                else:
                    # Check 2: Tamaño físico
                    phys_path = os.path.join(STATIC_IMAGES_ROOT, image_rel.lstrip('/'))
                    if not os.path.exists(phys_path) or os.path.getsize(phys_path) < CORRUPT_THRESHOLD:
                        needs_fix = True
                        if os.path.exists(phys_path):
                            try: os.remove(phys_path)
                            except: pass
                
                if needs_fix:
                    print(f"🔧 Reparando: {filename}...")
                    title = post.get('title', 'Untitled')
                    slug = filename.replace('.md', '')
                    category = os.path.basename(root)
                    if category == 'content': category = 'ia'
                    
                    new_img = get_image(title, slug, category)
                    
                    if new_img:
                        post['featured_image'] = new_img
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                        fixed_count += 1
                        
            except Exception as e:
                print(f"❌ Error en {filename}: {e}")

    print(f"✅ FINALIZADO. Reparados: {fixed_count}")

if __name__ == "__main__":
    deep_clean()
