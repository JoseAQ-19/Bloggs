import os
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"

def rescue_visuals():
    print("🚑 INICIANDO RESCATE VISUAL MASIVO (TOGETHER AI / FLUX)...")
    
    count = 0
    fixed_count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            count += 1
            
            try:
                post = frontmatter.load(filepath)
                title = post.get('title', 'Untitled')
                current_img = post.get('featured_image', '')
                
                needs_fix = False
                reason = ""
                
                # Criterio 1: Placeholder remoto
                if "placehold.co" in current_img:
                    needs_fix = True
                    reason = "Placeholder Remoto"
                
                # Criterio 2: Archivo fantasma
                elif current_img.startswith("/images/"):
                    phys_path = os.path.join(STATIC_IMAGES_ROOT, current_img.lstrip('/'))
                    if not os.path.exists(phys_path):
                        needs_fix = True
                        reason = "Archivo Fantasma"
                    # Opcional: Check tamaño
                    elif os.path.getsize(phys_path) < 50000:
                        needs_fix = True
                        reason = "Archivo Corrupto (<50KB)"
                
                # Criterio 3: Sin imagen
                elif not current_img:
                    needs_fix = True
                    reason = "Sin Imagen"

                if needs_fix:
                    print(f"🔧 [RESCATE] {title[:40]}... ({reason})")
                    
                    slug = filename.replace('.md', '')
                    category = os.path.basename(root)
                    if category in ['content', 'posts']: category = 'ia'
                    
                    # Generar nueva imagen (FLUX via Together AI)
                    new_path = get_image(title, slug, category)
                    
                    if new_path and "placehold.co" not in new_path:
                        post['featured_image'] = new_path
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                        print(f"   ✅ FIXED: {new_path}")
                        fixed_count += 1
                    else:
                        print(f"   ❌ ERROR: No se pudo generar imagen válida.")
                        
            except Exception as e:
                print(f"   ❌ Excepción crítica en {filename}: {e}")

    print(f"\n🚑 RESCATE FINALIZADO. Procesados: {count}. Arreglados: {fixed_count}.")

if __name__ == "__main__":
    rescue_visuals()
