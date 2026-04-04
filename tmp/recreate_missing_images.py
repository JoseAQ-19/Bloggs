import os
import sys

# Ensure scripts directory is in path to import novum_visual
script_dir = os.path.join(os.getcwd(), 'scripts')
sys.path.append(script_dir)

import frontmatter
from novum_visual import get_image

base_dir = "content"
img_base_dir = "static"

print("🚀 Iniciando reemplazo de defaults (Fases 2 y 3)...")
total_checked = 0
total_fixed = 0

for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(".md"):
            filepath = os.path.join(root, filename)
            total_checked += 1
            
            try:
                post = frontmatter.load(filepath)
                if filename == "_index.md":
                    continue
                
                img_path = post.get('featured_image', post.get('image', ''))
                
                is_default = False
                if img_path and '/images/defaults/' in img_path:
                    is_default = True
                
                if is_default:
                    print(f"⚠️ Imagen Default Detectada en: {filepath}")
                    title = post.get('title', 'Unknown Topic')
                    content = post.content
                    slug = post.get('slug', os.path.splitext(filename)[0])
                    
                    parts = filepath.replace('\\', '/').split('/')
                    category = "ia"
                    if "content" in parts:
                        idx = parts.index("content")
                        if len(parts) > idx + 2:
                            category = parts[idx+1] if parts[idx+1] not in ["en", "es"] else (parts[idx+2] if len(parts) > idx + 2 else "ia")
                    
                    print(f"   Contexto -> {title}")
                    # Llamar al motor de imagenes que genera basado en contexto
                    new_img_path = get_image(title, content, slug, category)
                    
                    if new_img_path and '/images/defaults/' not in new_img_path:
                        post['featured_image'] = new_img_path
                        post['image'] = new_img_path
                        
                        # Fix inline occurrences if any
                        updated_content = content.replace(img_path, new_img_path)
                        post.content = updated_content
                        
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                            
                        print(f"   ✅ Reemplazado por -> {new_img_path}\n")
                        total_fixed += 1
                    else:
                        print(f"   ❌ Fallo en generación, mantuvo default.\n")
            except Exception as e:
                print(f"❌ Error crítico procesando {filepath}: {e}")

print(f"🏁 Finalizado. Total archivos revisados: {total_checked}. Archivos reparados: {total_fixed}.")
