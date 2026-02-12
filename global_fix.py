import os
import frontmatter
from novum_visual import get_image

# Configuración
CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static"
# Umbral estricto para detectar "Pollinations Error" o baja calidad
CORRUPT_THRESHOLD = 120000 # 120 KB (Las de Together/Flux suelen ser 200KB+)

def global_fix():
    print("☣️ INICIANDO PROTOCOLO DE DESCONTAMINACIÓN GLOBAL...")
    
    total_scanned = 0
    fixed_count = 0
    
    # Recorrido Recursivo Profundo (os.walk baja por todas las subcarpetas: ia, crypto, en, es...)
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md"): continue
            if filename.startswith("_index"): continue # No tocar índices de sección
            
            filepath = os.path.join(root, filename)
            total_scanned += 1
            
            try:
                post = frontmatter.load(filepath)
                
                # Datos del post
                title = post.get('title', 'Untitled')
                image_rel_path = post.get('featured_image', '')
                
                # Deducir categoría por carpeta padre
                category = os.path.basename(root)
                # Si está en raíz o 'posts', asignar default
                if category in ['content', 'posts']: category = 'ia' 
                
                needs_fix = False
                fix_reason = ""
                
                # CASO 1: No tiene imagen asignada
                if not image_rel_path:
                    needs_fix = True
                    fix_reason = "Missing Frontmatter"
                
                # CASO 2: Tiene imagen pero hay que verificarla físicamente
                else:
                    # Normalizar ruta (quitar / inicial)
                    clean_rel_path = image_rel_path.lstrip('/')
                    physical_path = os.path.join(STATIC_IMAGES_ROOT, clean_rel_path)
                    
                    if not os.path.exists(physical_path):
                        needs_fix = True
                        fix_reason = "File Not Found"
                    else:
                        size = os.path.getsize(physical_path)
                        if size < CORRUPT_THRESHOLD:
                            needs_fix = True
                            fix_reason = f"Low Quality/Error ({size/1024:.1f} KB)"
                
                if needs_fix:
                    print(f"🔧 FIXING [{category.upper()}]: {title[:40]}... -> {fix_reason}")
                    
                    # Generar Slug si no lo tenemos fácil (usamos filename)
                    slug = filename.replace('.md', '')
                    
                    # Borrar archivo corrupto si existe
                    if image_rel_path:
                        clean_rel_path = image_rel_path.lstrip('/')
                        physical_path = os.path.join(STATIC_IMAGES_ROOT, clean_rel_path)
                        if os.path.exists(physical_path):
                            try: os.remove(physical_path)
                            except: pass
                    
                    # Generar Nueva Imagen (Together AI Platinum)
                    # get_image ya maneja la lógica de guardar y devolver ruta
                    # Usamos el título como prompt base
                    new_image_path = get_image(title, slug, category)
                    
                    if new_image_path:
                        post['featured_image'] = new_image_path
                        
                        # Guardar cambios en el .md
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                            
                        print(f"   ✅ Reparado: {new_image_path}")
                        fixed_count += 1
                    else:
                        print(f"   ❌ Fallo al generar imagen.")
                
            except Exception as e:
                print(f"   ❌ Error leyendo {filename}: {e}")

    print(f"\n🚀 PROTOCOLO FINALIZADO.")
    print(f"   Escaneados: {total_scanned}")
    print(f"   Reparados:  {fixed_count}")

if __name__ == "__main__":
    global_fix()
