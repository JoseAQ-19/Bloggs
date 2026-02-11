import os
from novum_visual import get_image

IMAGES_DIR = "static/images"
# Umbral estricto: Todo lo < 100KB es sospechoso de ser Pollinations Error o baja calidad
CORRUPT_THRESHOLD = 100000 

def upgrade_to_flux():
    print("💎 INICIANDO LAVADO DE CARA PLATINUM (TOGETHER AI)...")
    
    count = 0
    fixed = 0
    
    if not os.path.exists(IMAGES_DIR): return

    for root, dirs, files in os.walk(IMAGES_DIR):
        for filename in files:
            if not filename.endswith(".jpg"): continue
            if filename.startswith("logo") or "default" in filename: continue
            
            filepath = os.path.join(root, filename)
            size = os.path.getsize(filepath)
            
            if size < CORRUPT_THRESHOLD:
                print(f"\n🚩 DETECTADA CALIDAD BAJA ({size/1024:.1f} KB): {filename}")
                
                # Deducción de datos para regenerar
                slug = filename.replace('.jpg', '')
                prompt = slug.replace('-', ' ')
                
                # Intentar adivinar categoría por el nombre del archivo (limitado pero funcional)
                category = "ia"
                if "bitcoin" in slug or "crypto" in slug: category = "crypto"
                elif "gym" in slug or "fitness" in slug: category = "fitness"
                elif "youtube" in slug: category = "youtube"
                
                # Regenerar con Motor Platinum
                # get_image guardará sobre el mismo archivo
                print(f"   ✨ Regenerando con FLUX SOTA...")
                
                # Borrar para asegurar clean write
                try: os.remove(filepath)
                except: pass
                
                new_path = get_image(prompt, slug, category)
                
                if new_path:
                    print(f"   ✅ Upgrade completado.")
                    fixed += 1
                else:
                    print("   ❌ Fallo en upgrade.")
                
                count += 1

    print(f"\n💎 UPGRADE FINALIZADO: {fixed}/{count} imágenes elevadas a nivel Platinum.")

if __name__ == "__main__":
    upgrade_to_flux()
