import os
import requests
import random
import time
import urllib.parse
from pathlib import Path

class NovumVisualEngine:
    """
    Motor Gráfico Híbrido V1 para Hugo SSG.
    Arquitectura: Local Storage + Cascada de APIs (Cloudflare -> Pollinations -> Lexica -> Fallback).
    """
    
    STATIC_DIR = "static/images"
    DEFAULT_DIR = "static/images/defaults"
    
    # ADN Visual de Novum (Estética por Vertical)
    AESTHETICS = {
        "ia": "cyberpunk style, neon blue and purple lighting, futuristic laboratory, detailed circuit boards, cinematic 8k, unreal engine 5 render, high contrast",
        "crypto": "matrix code rain style, golden bitcoin physical coin, stock market charts background, dark green theme, financial district night, ultra realistic, bloomberg terminal vibe",
        "fitness": "gym atmosphere, crossfit athlete silhouette, dramatic lighting, sweat details, orange and black theme, motivational poster style, sharp focus",
        "youtube": "youtube play button 3d render, red glowing neon, streaming studio setup, microphone and camera shallow depth of field, vibrant colors, 4k",
        "viral": "pop art style, vibrant colors, shocked emoji 3d render, chaotic internet collage, trending topic visualization, glossy finish, high saturation"
    }

    def __init__(self):
        # Asegurar estructura de carpetas
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.DEFAULT_DIR, exist_ok=True)
        
        # Cloudflare Auth
        self.cf_id = os.getenv("CF_ACCOUNT_ID")
        self.cf_token = os.getenv("CF_API_TOKEN")

    def generate_and_save(self, prompt, slug, category="ia"):
        """
        Método Maestro: Genera, Descarga y Guarda la imagen.
        Retorna: Ruta relativa para Hugo (ej: "/images/mi-slug.jpg")
        """
        print(f"🎨 [VisualEngine] Iniciando generación para: {slug}")
        
        # 1. Enriquecer Prompt
        enhanced_prompt = self._apply_aesthetic_modifiers(prompt, category)
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # Si ya existe (cache), devolver
        if os.path.exists(filepath):
            print(f"   ♻️ Imagen cacheada encontrada: {filename}")
            return f"/images/{filename}"

        # 2. Cascada de Ejecución
        success = False
        
        # Nivel 0: Cloudflare Workers AI (Flux)
        if self.cf_id and self.cf_token:
            success = self._try_cloudflare(enhanced_prompt, filepath)
            
        # Nivel 1: Pollinations (Flux Hack)
        if not success:
            success = self._try_pollinations(enhanced_prompt, filepath)
            
        # Nivel 2: Lexica (Search)
        if not success:
            success = self._try_lexica(prompt, filepath) # Usamos prompt simple para búsqueda
            
        # Nivel 3: Fallback Local
        if not success:
            print("   ⚠️ Fallo total de APIs. Usando Fallback Local.")
            return self._get_fallback_image(category)
            
        print(f"   ✅ Imagen guardada en: {filepath}")
        return f"/images/{filename}"

    def _apply_aesthetic_modifiers(self, prompt, category):
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        return f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9 --v 6.0"

    def _save_bytes(self, content, filepath):
        """Helper para escritura física."""
        try:
            with open(filepath, "wb") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"   ❌ Error escribiendo archivo: {e}")
            return False

    def _try_cloudflare(self, prompt, filepath):
        print("   ☁️ Intentando Nivel 0: Cloudflare AI...")
        try:
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
            headers = {"Authorization": f"Bearer {self.cf_token}"}
            payload = {"prompt": prompt}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                import base64
                # Cloudflare suele devolver JSON con base64
                result = response.json()
                if "result" in result and "image" in result["result"]:
                    image_data = base64.b64decode(result["result"]["image"])
                    return self._save_bytes(image_data, filepath)
                # O devuelve bytes directos dependiendo del endpoint, asumimos JSON standard
            print(f"   ⚠️ Cloudflare falló (Status: {response.status_code})")
            return False
        except Exception as e:
            print(f"   ⚠️ Cloudflare Exception: {e}")
            return False

    def _try_pollinations(self, prompt, filepath):
        print("   🌺 Intentando Nivel 1: Pollinations (Flux)...")
        try:
            seed = random.randint(0, 999999)
            encoded = urllib.parse.quote(prompt)
            # URL optimizada según investigación
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true&safe=true&seed={seed}"
            
            response = requests.get(url, timeout=45) # Flux es lento
            
            if response.status_code == 200 and len(response.content) > 5000:
                return self._save_bytes(response.content, filepath)
                
            print(f"   ⚠️ Pollinations falló (Size: {len(response.content)})")
            return False
        except Exception as e:
            print(f"   ⚠️ Pollinations Exception: {e}")
            return False

    def _try_lexica(self, simple_prompt, filepath):
        print("   🔍 Intentando Nivel 2: Lexica (Search)...")
        try:
            # Buscamos imágenes ya existentes
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(simple_prompt)}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])
                if images:
                    # Coger la primera
                    image_url = images[0]["src"]
                    # Descargarla
                    img_resp = requests.get(image_url, timeout=15)
                    if img_resp.status_code == 200:
                        return self._save_bytes(img_resp.content, filepath)
            
            print("   ⚠️ Lexica sin resultados.")
            return False
        except Exception as e:
            print(f"   ⚠️ Lexica Exception: {e}")
            return False

    def _get_fallback_image(self, category):
        """Retorna ruta al placeholder local."""
        filename = f"default-{category}.jpg"
        local_path = os.path.join(self.DEFAULT_DIR, filename)
        
        # Si no existe la default física, usamos un placeholder remoto seguro para no romper
        if not os.path.exists(local_path):
            return f"https://placehold.co/1280x720/000000/FFFFFF/png?text={category.upper()}+News"
            
        return f"/images/defaults/{filename}"

# Interfaz simplificada para uso en main.py
def get_image(prompt, slug, category="ia"):
    engine = NovumVisualEngine()
    return engine.generate_and_save(prompt, slug, category)
