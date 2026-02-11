import os
from novum_visual import get_image

IMAGES_DIR = "static/images"
MIN_SIZE_BYTES = 50000 # 50KB Threshold

def fix_broken_images():
    print("🧟‍♂️ INICIANDO CAZA DE ZOMBIES (Imágenes Rotas)...")
    
    files = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    count = 0
    fixed = 0
    
    for filename in files:
        filepath = os.path.join(IMAGES_DIR, filename)
        size = os.path.getsize(filepath)
        
        if size < MIN_SIZE_BYTES:
            print(f"   🚩 Detectada imagen rota: {filename} ({size} bytes)")
            
            # Deducir prompt del nombre del archivo (slug)
            slug = filename.replace('.jpg', '')
            prompt = slug.replace('-', ' ')
            
            # Regenerar (usará el nuevo motor con sleep y fallbacks)
            print(f"   ♻️ Regenerando...")
            result = get_image(prompt, slug, category="ia") # Asumimos IA por defecto o tendríamos que leer el post
            
            if result:
                fixed += 1
                print(f"   ✅ Arreglada.")
            else:
                print(f"   ❌ Fallo al arreglar.")
                
            count += 1
            
    print(f"\n✨ LIMPIEZA FINALIZADA: {fixed}/{count} imágenes reparadas.")

if __name__ == "__main__":
    fix_broken_images()
