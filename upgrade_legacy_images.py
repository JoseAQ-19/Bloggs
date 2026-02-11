import os
import frontmatter
from novum_visual import get_image

CONTENT_DIRS = [
    'content/ia', 'content/crypto', 'content/fitness', 'content/youtube', 'content/viral'
]

def upgrade_legacy_images():
    print("🎨 INICIANDO REMASTERIZACIÓN VISUAL (HD UPGRADE)...")
    
    count = 0
    
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        
        category = os.path.basename(folder)
        print(f"\n📂 Escaneando carpeta: {category}...")
        
        files = [f for f in os.listdir(folder) if f.endswith('.md') and not f.startswith('_index')]
        
        for filename in files:
            filepath = os.path.join(folder, filename)
            
            try:
                post = frontmatter.load(filepath)
                title = post.get('title')
                slug = filename.replace('.md', '')
                
                # Check si ya tiene imagen HD (opcional, o forzar siempre)
                # Forzamos update para asegurar calidad Flux
                
                print(f"   🔄 Actualizando: {title[:40]}...")
                
                # Generar nueva imagen con NovumVisualEngine
                new_image_path = get_image(title, slug, category)
                
                if new_image_path:
                    # Actualizar Frontmatter
                    post['featured_image'] = new_image_path
                    
                    # Guardar con cuidado
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    
                    count += 1
                
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n✨ PROCESO COMPLETADO: {count} imágenes remasterizadas a HD.")

if __name__ == "__main__":
    upgrade_legacy_images()
