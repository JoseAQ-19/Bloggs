import os
import time
import frontmatter
from novum_visual import get_image

# Directorio base de contenido y estáticos
CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static" # Porque la ruta en MD es relativa (/images/...)

# Umbral de corrupción (Pollinations error images are usually tiny)
CORRUPT_SIZE_THRESHOLD = 50000 # 50 KB

def fix_rate_limits():
    print("🧹 INICIANDO OPERACIÓN VISUAL PURGE...")
    
    corrupt_count = 0
    fixed_count = 0
    
    # Recorrer todas las carpetas de contenido
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md"): continue
            if filename.startswith("_index"): continue # Ignorar índices de sección
            
            md_path = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(md_path)
                image_rel_path = post.get('featured_image', '')
                
                if not image_rel_path:
                    continue # No tiene imagen, saltar
                
                # Detección de Placeholders Remotos (Deuda Técnica)
                if image_rel_path.startswith("http"):
                    print(f"🚩 URL REMOTA detectada: {filename}")
                    is_corrupt = True
                else:
                    # Construir ruta física
                    physical_path = os.path.join(STATIC_IMAGES_ROOT, image_rel_path.lstrip('/'))
                    if not os.path.exists(physical_path):
                        print(f"⚠️ Imagen perdida: {filename}")
                        # Si no existe, hay que regenerarla sí o sí
                        is_corrupt = True
                    else:
                        size = os.path.getsize(physical_path)
                        if size < CORRUPT_SIZE_THRESHOLD:
                            print(f"🚩 CORRUPTO detectado ({size/1024:.1f} KB): {filename}")
                            # Borrar archivo corrupto para forzar regeneración
                            os.remove(physical_path)
                            is_corrupt = True
                        else:
                            is_corrupt = False

                if is_corrupt:
                    # Datos para regenerar
                    title = post.get('title', 'Unknown Title')
                    slug = filename.replace('.md', '')
                    # Deducir categoría de la carpeta padre
                    category = os.path.basename(root)
                    
                    print(f"   🔄 Regenerando imagen para: {title[:40]}...")
                    
                    time.sleep(5) 
                    new_path = get_image(title, slug, category)
                    
                    if new_path:
                        # Actualizar Frontmatter con la nueva ruta local
                        post['featured_image'] = new_path
                        with open(md_path, 'wb') as f:
                            frontmatter.dump(post, f)
                        
                        print(f"   ✅ Reparado con éxito.")
                        fixed_count += 1
                        corrupt_count += 1
                    else:
                        print(f"   ❌ Fallo al reparar.")
                        
                else:
                    # Imagen OK
                    # print(f"✅ OK ({size/1024:.1f} KB): {filename}")
                    pass
                    
            except Exception as e:
                print(f"❌ Error procesando {filename}: {e}")

    print(f"\n✨ PURGA COMPLETADA: {fixed_count}/{corrupt_count} imágenes reparadas.")

if __name__ == "__main__":
    fix_rate_limits()
