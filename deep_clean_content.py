import os
import re
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"
MIN_SIZE_BYTES = 80000 # 80 KB

def deep_clean_content():
    print("🧼 INICIANDO LAVADO A PRESIÓN...")
    
    cleaned_body_count = 0
    regenerated_cover_count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                # Cargar post
                post = frontmatter.load(filepath)
                content_original = post.content
                
                modified = False
                
                # --- PASO 1: CIRUGÍA DEL CONTENIDO (Body) ---
                # Regex para eliminar imágenes Markdown: ![alt](url)
                content_clean = re.sub(r'!\[.*?\]\(.*?\)', '', content_original)
                
                # Eliminar saltos de línea extra que queden
                content_clean = re.sub(r'\n{3,}', '\n\n', content_clean).strip()
                
                if content_clean != content_original:
                    post.content = content_clean
                    modified = True
                    print(f"   ✂️ [LIMPIO] Cuerpo de texto saneado: {filename}")
                    cleaned_body_count += 1
                
                # --- PASO 2: DETECCIÓN DE PORTADA TÓXICA (Frontmatter) ---
                image_ref = post.get('featured_image', '')
                needs_regen = False
                
                if not image_ref:
                    needs_regen = True # Sin imagen
                elif "pollinations" in image_ref.lower():
                    needs_regen = True # URL antigua
                elif image_ref.startswith("http"):
                    needs_regen = True # URL externa cualquiera
                else:
                    # Check físico local
                    clean_ref = image_ref.lstrip('/')
                    phys_path = os.path.join(STATIC_IMAGES_ROOT, clean_ref)
                    
                    if not os.path.exists(phys_path):
                        needs_regen = True
                    elif os.path.getsize(phys_path) < MIN_SIZE_BYTES:
                        needs_regen = True # Imagen de error pequeña
                        try: os.remove(phys_path) # Borrar la mala
                        except: pass
                
                if needs_regen:
                    print(f"   🔄 [REGENERANDO] Portada para: {filename}...")
                    title = post.get('title', 'Untitled')
                    slug = filename.replace('.md', '')
                    category = os.path.basename(root)
                    if category == 'content': category = 'ia'
                    
                    new_img = get_image(title, slug, category)
                    
                    if new_img:
                        post['featured_image'] = new_img
                        modified = True
                        regenerated_cover_count += 1
                        print(f"      ✅ Nueva imagen: {new_img}")
                    else:
                        print(f"      ❌ Fallo al generar.")
                
                # GUARDAR CAMBIOS
                if modified:
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                        
            except Exception as e:
                print(f"❌ Error crítico en {filename}: {e}")

    print(f"\n🧼 OPERACIÓN FINALIZADA.")
    print(f"   Textos Limpiados: {cleaned_body_count}")
    print(f"   Portadas Regeneradas: {regenerated_cover_count}")

if __name__ == "__main__":
    deep_clean_content()
