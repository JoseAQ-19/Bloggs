import os
import requests
import re
import unicodedata
import time
import random
import urllib.parse
from pathlib import Path

class SlugManager:
    @staticmethod
    def generate(text):
        """Genera un slug SEO-friendly determinista."""
        if not text: return f"post-{int(time.time())}"
        slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        slug = slug.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        slug = slug.strip('-')
        return slug or f"post-{int(time.time())}"

class ImageManager:
    STATIC_DIR = "static/images/uploads"
    DEFAULT_DIR = "static/images/defaults"

    @staticmethod
    def get_image(prompt, filename_base, category="ia"):
        """
        Orquesta la obtención de imagen:
        1. Intenta Pollinations con FLUX.
        2. Si falla, usa imagen por defecto de la categoría.
        """
        # Asegurar directorios
        os.makedirs(ImageManager.STATIC_DIR, exist_ok=True)
        os.makedirs(ImageManager.DEFAULT_DIR, exist_ok=True)

        # 1. Intentar Generación AI (FLUX)
        image_path = ImageManager._generate_flux(prompt, filename_base)
        if image_path:
            return image_path
            
        # 2. Fallback: Imagen Default Local
        print(f"⚠️ Usando imagen de respaldo para: {category}")
        return ImageManager._get_default_image(category)

    @staticmethod
    def _generate_flux(prompt, filename_base):
        """Genera con Pollinations usando parámetros FLUX."""
        try:
            safe_name = SlugManager.generate(filename_base)
            filename = f"{safe_name}.jpg"
            local_path = os.path.join(ImageManager.STATIC_DIR, filename)
            
            # Si ya existe (cache), devolverlo
            if os.path.exists(local_path):
                return f"/images/uploads/{filename}"

            # Construir URL FLUX optimizada
            # seed aleatoria para variedad
            seed = random.randint(0, 1000000)
            encoded_prompt = urllib.parse.quote(prompt)
            
            # URL Mágica
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1280&height=720&seed={seed}&nologo=true&enhance=true"
            
            print(f"🎨 Generando FLUX: {prompt[:40]}...")
            
            # Timeout alto porque FLUX tarda
            response = requests.get(url, timeout=45)
            
            if response.status_code == 200 and len(response.content) > 5000:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Imagen FLUX guardada: {filename}")
                return f"/images/uploads/{filename}"
            else:
                print(f"   ❌ Error FLUX: Status {response.status_code} o contenido vacío.")
                return None
                
        except Exception as e:
            print(f"   ❌ Excepción FLUX: {e}")
            return None

    @staticmethod
    def _get_default_image(category):
        """Retorna la ruta de la imagen default para la categoría."""
        # Asumimos que existen (deberíamos crearlas si no)
        filename = f"default-{category}.jpg"
        local_path = os.path.join(ImageManager.DEFAULT_DIR, filename)
        
        # Si no existe física, devolvemos una url placeholder remota segura como último recurso
        if not os.path.exists(local_path):
            return f"https://placehold.co/1280x720/000000/FFFFFF/png?text={category.upper()}+News"
            
        return f"/images/defaults/{filename}"
