import os
import requests
import time
import urllib.parse

IMAGES_DIR = "static/images"
UPLOADS_DIR = "static/images/uploads"
MIN_SIZE_BYTES = 50000 # 50KB

def download_from_lexica(prompt, filepath):
    print(f"   🔍 Buscando en Lexica: {prompt}...")
    try:
        url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(prompt)}"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            images = data.get("images", [])
            if images:
                # Usar la primera
                img_url = images[0]["src"]
                print(f"   📥 Descargando: {img_url[:50]}...")
                img_resp = requests.get(img_url, timeout=20)
                if img_resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)
                    return True
        print("   ⚠️ Lexica falló o no encontró nada.")
        return False
    except Exception as e:
        print(f"   ❌ Error Lexica: {e}")
        return False

def purge_images():
    print("🧹 INICIANDO PURGA DE IMÁGENES ROTAS (RATE LIMIT)...")
    
    # Escanear tanto static/images como uploads
    targets = [IMAGES_DIR, UPLOADS_DIR]
    count = 0
    fixed = 0
    
    for directory in targets:
        if not os.path.exists(directory): continue
        
        files = [f for f in os.listdir(directory) if f.endswith('.jpg')]
        
        for filename in files:
            filepath = os.path.join(directory, filename)
            size = os.path.getsize(filepath)
            
            if size < MIN_SIZE_BYTES:
                print(f"\n🚩 IMAGEN ROTA DETECTADA: {filename} ({size} bytes)")
                
                # Prompt simple basado en nombre
                prompt = filename.replace('.jpg', '').replace('-', ' ')
                
                # Reemplazar con Lexica (Force)
                if download_from_lexica(prompt, filepath):
                    print("   ✅ REEMPLAZADA CON ÉXITO.")
                    fixed += 1
                else:
                    print("   ❌ NO SE PUDO REPARAR.")
                
                time.sleep(1) # Respetar a Lexica
                count += 1
    
    print(f"\n✨ PURGA FINALIZADA: {fixed}/{count} imágenes saneadas.")

if __name__ == "__main__":
    purge_images()
