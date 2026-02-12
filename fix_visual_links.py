import os
import frontmatter
from utils import SlugManager
from novum_visual import get_image

# Configuración
CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"
VALID_THRESHOLD = 50000 # 50 KB

def fix_visual_links():
    print("🔗 INICIANDO OPERACIÓN LINKER (SINCRONIZACIÓN)...")
    
    count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                # 1. Leer Post
                post = frontmatter.load(filepath)
                title = post.get('title', '')
                if not title: continue # Skip sin título
                
                # 2. Generar Slug/Filename esperado
                # IMPORTANTE: Usamos el mismo SlugManager que main.py para consistencia
                # O si preferimos basarnos en el nombre del archivo MD para ser más robustos con lo que ya existe:
                # slug = filename.replace('.md', '') 
                # Pero la instrucción dice "basado en el título". Vamos a usar el slug del archivo que es más fiable como ID único.
                slug = filename.replace('.md', '')
                
                expected_img_name = f"{slug}.jpg"
                phys_path = os.path.join(STATIC_IMAGES_ROOT, "images", expected_img_name)
                
                # 3. Verificación / Generación
                image_ready = False
                
                if os.path.exists(phys_path) and os.path.getsize(phys_path) > VALID_THRESHOLD:
                    image_ready = True
                else:
                    print(f"   ⚠️ Imagen ausente/pequeña para: {slug}. Generando...")
                    # Deducir categoría
                    category = os.path.basename(root)
                    if category == 'content': category = 'ia'
                    
                    # Generar (get_image guarda en static/images/{slug}.jpg)
                    new_path = get_image(title, slug, category)
                    if new_path:
                        image_ready = True
                
                # 4. Cirugía de Frontmatter
                if image_ready:
                    # Ruta relativa absoluta para Hugo
                    final_path = f"/images/{expected_img_name}"
                    
                    if post.get('featured_image') != final_path:
                        post['featured_image'] = final_path
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                        print(f"   ✅ [ENLAZADO] {title[:30]}... -> {final_path}")
                        count += 1
                    else:
                        # print(f"   🆗 Ya enlazado: {slug}")
                        pass
                        
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n✨ OPERACIÓN COMPLETADA: {count} archivos re-enlazados.")

if __name__ == "__main__":
    fix_visual_links()
