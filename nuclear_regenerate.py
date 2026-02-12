import os
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"

def nuclear_regenerate():
    print("☢️ INICIANDO OPERACIÓN CLEAN SLATE (REGENERACIÓN TOTAL)...")
    
    count = 0
    success_count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md"): continue
            if filename.startswith("_index"): continue 
            
            filepath = os.path.join(root, filename)
            count += 1
            
            try:
                post = frontmatter.load(filepath)
                title = post.get('title', 'Untitled')
                slug = filename.replace('.md', '')
                
                # Deducir categoría
                category = os.path.basename(root)
                if category in ['content', 'posts']: category = 'ia'
                
                print(f"🔄 [RENOVANDO] {filename} ({title[:30]}...)...")
                
                # Forzar regeneración borrando primero si existe (get_image comprueba existencia)
                img_filename = f"{slug}.jpg"
                phys_path = os.path.join(STATIC_IMAGES_ROOT, "images", img_filename)
                
                if os.path.exists(phys_path):
                    try: os.remove(phys_path)
                    except: pass
                
                # Generar nueva (Together AI / Flux)
                new_path = get_image(title, slug, category)
                
                if new_path:
                    # Actualizar frontmatter por si acaso la ruta cambia (aunque mantenemos slug)
                    post['featured_image'] = new_path
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    print(f"   ✅ OK")
                    success_count += 1
                else:
                    print(f"   ❌ FALLO")
                    
            except Exception as e:
                print(f"   ❌ ERROR CRÍTICO en {filename}: {e}")

    print(f"\n☢️ OPERACIÓN FINALIZADA.")
    print(f"   Total Archivos: {count}")
    print(f"   Regenerados:    {success_count}")

if __name__ == "__main__":
    nuclear_regenerate()
