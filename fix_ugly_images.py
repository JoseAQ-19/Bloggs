import os
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"
# Subimos el listón: Imágenes < 150KB son sospechosas de baja calidad para FLUX
QUALITY_THRESHOLD = 150000 

def fix_ugly_images():
    print("🎨 INICIANDO REPARACIÓN VISUAL SELECTIVA (<150KB)...")
    
    repaired = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            try:
                post = frontmatter.load(filepath)
                title = post.get('title', 'Untitled')
                image_rel = post.get('featured_image', '')
                slug = filename.replace('.md', '')
                category = os.path.basename(root) # Categoría corregida por el script anterior
                
                if not image_rel: continue
                
                # Check físico
                phys_path = os.path.join(STATIC_IMAGES_ROOT, image_rel.lstrip('/'))
                
                needs_repair = False
                
                if not os.path.exists(phys_path):
                    print(f"⚠️ Imagen perdida: {filename}")
                    needs_repair = True
                elif os.path.getsize(phys_path) < QUALITY_THRESHOLD:
                    print(f"📉 Baja Calidad ({os.path.getsize(phys_path)/1024:.1f} KB): {filename}")
                    needs_repair = True
                    
                if needs_repair:
                    print(f"   🔄 Regenerando para [{category.upper()}]: {title[:30]}...")
                    
                    # Borrar vieja
                    if os.path.exists(phys_path):
                        try: os.remove(phys_path)
                        except: pass
                        
                    # Generar nueva (El motor ya aplica estética por categoría)
                    new_path = get_image(title, slug, category)
                    
                    if new_path:
                        post['featured_image'] = new_path
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                        repaired += 1
                        print(f"   ✅ Reparada.")
                    else:
                        print(f"   ❌ Fallo al regenerar.")
                        
            except Exception as e:
                print(f"❌ Error: {e}")

    print(f"\n✨ REPARACIÓN FINALIZADA. {repaired} imágenes mejoradas.")

if __name__ == "__main__":
    fix_ugly_images()
