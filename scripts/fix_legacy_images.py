import os
import frontmatter
from novum_visual import get_image

base_dir = "content"
img_base_dir = "static"

print("🚀 Iniciando Fixer Masivo de Imágenes...")
total_checked = 0
total_fixed = 0

for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(".md"):
            filepath = os.path.join(root, filename)
            total_checked += 1
            
            try:
                post = frontmatter.load(filepath)
                # Omitir paginas _index.md
                if filename == "_index.md":
                    continue
                
                img_path = post.get('featured_image', post.get('image', ''))
                
                missing = False
                if img_path:
                    if img_path.startswith('/'):
                        actual_path = os.path.join(img_base_dir, img_path.lstrip('/'))
                    else:
                        # Si no empieza con /, asumimos que ya está limpio o es relativo
                        actual_path = os.path.join(img_base_dir, "images", img_path)
                    
                    if not os.path.exists(actual_path):
                        missing = True
                else:
                    missing = True
                
                if missing:
                    print(f"⚠️ Imagen Rota Detectada en: {filepath}")
                    title = post.get('title', 'Unknown Topic')
                    content = post.content
                    slug = post.get('slug', os.path.splitext(filename)[0])
                    
                    # Extraer categoria
                    parts = filepath.replace('\\', '/').split('/')
                    category = "ia"
                    if "content" in parts:
                        idx = parts.index("content")
                        if len(parts) > idx + 2:
                            category = parts[idx+2]
                    
                    # Llamar al motor de imagenes que regenera o da fallback
                    new_img_path = get_image(title, content, slug, category)
                    
                    post['featured_image'] = new_img_path
                    post['image'] = new_img_path
                    
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                        
                    print(f"✅ Arreglado -> {new_img_path}\n")
                    total_fixed += 1
            except Exception as e:
                print(f"❌ Error crítico procesando {filepath}: {e}")

print(f"🏁 Finalizado. Total archivos revisados: {total_checked}. Archivos reparados: {total_fixed}.")
