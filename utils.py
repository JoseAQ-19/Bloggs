import os
import requests
import re
import unicodedata
import time
from urllib.parse import urlparse

class SlugManager:
    @staticmethod
    def generate(text):
        """Genera un slug SEO-friendly determinista."""
        if not text: return f"post-{int(time.time())}"
        
        # Normalización Unicode (tildes, ñ, etc)
        slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        slug = slug.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug) # Solo letras, números y guiones
        slug = re.sub(r'[\s-]+', '-', slug) # Espacios a guiones
        slug = slug.strip('-')
        
        return slug or f"post-{int(time.time())}"

class ImageManager:
    STATIC_DIR = "static/images/uploads"

    @staticmethod
    def download_image(url, filename_base):
        """
        Descarga una imagen de una URL y la guarda localmente con un nombre SEO.
        Retorna la ruta relativa para usar en Hugo (ej: /images/uploads/mi-post.jpg).
        """
        if not url: return ""

        try:
            # Crear directorio si no existe
            os.makedirs(ImageManager.STATIC_DIR, exist_ok=True)
            
            # Limpiar nombre de archivo
            safe_name = SlugManager.generate(filename_base)
            filename = f"{safe_name}.jpg" # Forzamos jpg por simplicidad con Pollinations
            local_path = os.path.join(ImageManager.STATIC_DIR, filename)
            
            print(f"⬇️ Descargando imagen: {url} -> {local_path}")
            
            # AUMENTO CRÍTICO DE TIMEOUT PARA MODELO FLUX (Puede tardar 30s+)
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return f"/images/uploads/{filename}"
            else:
                print(f"⚠️ Error descarga imagen ({response.status_code})")
                return ""
                
        except Exception as e:
            print(f"❌ Error guardando imagen local: {e}")
            return ""
