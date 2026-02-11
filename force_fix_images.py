import os
import requests
import time
import urllib.parse

IMAGES_DIR = "static/images"
# Umbral Agresivo: Las de Pollinations error pesan ~30-60KB.
# Las buenas de Flux HD pesan > 100KB.
CORRUPT_THRESHOLD = 100000 

def download_from_lexica(prompt, filepath):
    """Descarga EXCLUSIVA desde Lexica (Safe Haven)."""
    print(f"   🔍 Buscando en Lexica: {prompt[:40]}...")
    try:
        url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(prompt)}"
        resp = requests.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            images = data.get("images", [])
            if images:
                # Filtrar por apaisada si es posible, si no la primera
                # Lexica devuelve grid, la primera suele ser la más relevante
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

def force_fix_images():
    print("☣️ INICIANDO PURGA AGRESIVA (Threshold > 100KB)...")
    
    count = 0
    fixed = 0
    
    if not os.path.exists(IMAGES_DIR):
        print("❌ Directorio static/images no existe.")
        return

    # Escanear archivos en raíz de static/images y subcarpetas si las hubiera
    for root, dirs, files in os.walk(IMAGES_DIR):
        for filename in files:
            if not filename.endswith(".jpg") and not filename.endswith(".png"): continue
            if filename.startswith("logo"): continue # No tocar logo
            if "default" in filename: continue # No tocar defaults
            
            filepath = os.path.join(root, filename)
            size = os.path.getsize(filepath)
            
            if size < CORRUPT_THRESHOLD:
                print(f"\n🚩 DETECTADO CORRUPTO ({size/1024:.1f} KB): {filename}")
                
                # Prompt simple basado en nombre del archivo
                slug_clean = filename.replace('.jpg', '').replace('.png', '').replace('-', ' ')
                prompt = f"{slug_clean} cyberpunk tech realistic"
                
                # Sobrescribir con Lexica
                if download_from_lexica(prompt, filepath):
                    print(f"   ✅ SANEADO con Lexica (Size ahora: {os.path.getsize(filepath)/1024:.1f} KB)")
                    fixed += 1
                else:
                    print("   ❌ Fallo al sanear. Se mantiene corrupto.")
                
                time.sleep(1.5) # Rate limit friendly
                count += 1
            else:
                # print(f"✅ OK ({size/1024:.1f} KB): {filename}")
                pass

    print(f"\n✨ PURGA FINALIZADA: {fixed}/{count} imágenes sospechosas reemplazadas.")

if __name__ == "__main__":
    force_fix_images()
