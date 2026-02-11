import os
import requests
import random
import time
import base64
import urllib.parse
from together import Together

class NovumVisualEngine:
    """
    Motor Gráfico Híbrido V2 (Together AI + Pollinations + Lexica).
    Arquitectura: Cascada de Fallos (Waterfall) con decodificación Base64 local.
    """
    
    STATIC_DIR = "static/images"
    DEFAULT_DIR = "static/images/defaults"
    
    # ADN Visual (Estilos)
    AESTHETICS = {
        "ia": "cyberpunk style, neon blue and purple lighting, futuristic laboratory, detailed circuit boards, cinematic 8k, unreal engine 5 render, high contrast",
        "crypto": "matrix code rain style, golden bitcoin physical coin, stock market charts background, dark green theme, financial district night, ultra realistic, bloomberg terminal vibe",
        "fitness": "gym atmosphere, crossfit athlete silhouette, dramatic lighting, sweat details, orange and black theme, motivational poster style, sharp focus",
        "youtube": "youtube play button 3d render, red glowing neon, streaming studio setup, microphone and camera shallow depth of field, vibrant colors, 4k",
        "viral": "pop art style, vibrant colors, shocked emoji 3d render, chaotic internet collage, trending topic visualization, glossy finish, high saturation",
        "tools": "isometric 3d technical diagram, blueprint style, neon blue lines, engineering drafting table, clean minimalist tech"
    }

    def __init__(self):
        # Asegurar estructura de carpetas
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.DEFAULT_DIR, exist_ok=True)
        
        # Together Auth
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if self.together_key else None

    def generate_and_save(self, prompt, slug, category="ia"):
        """
        Método Maestro: Genera imagen y guarda en disco.
        Retorna: Ruta relativa ("/images/slug.jpg") o Fallback.
        """
        print(f"🎨 [VisualEngine] Iniciando generación para: {slug}")
        
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # 1. Enriquecer Prompt
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        enhanced_prompt = f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9"

        # 2. Cascada de Ejecución (Waterfall)
        
        # NIVEL 1: TOGETHER AI (FLUX.1-schnell)
        if self.together_client:
            if self._level_1_together(enhanced_prompt, filepath):
                return f"/images/{filename}"
        else:
            print("   ℹ️ Together API Key no encontrada. Saltando Nivel 1.")

        # NIVEL 2: POLLINATIONS (Flux Hack)
        if self._level_2_pollinations(enhanced_prompt, filepath):
            return f"/images/{filename}"

        # NIVEL 3: LEXICA (Search)
        if self._level_3_lexica(prompt, filepath): # Prompt simple para búsqueda
            return f"/images/{filename}"

        # FALLBACK FINAL
        print("   ⚠️ Fallo total de motores. Usando Imagen Default.")
        return self._get_fallback_image(category)

    def _save_bytes(self, content, filepath):
        """Helper para escritura física."""
        try:
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"   ✅ Imagen guardada: {os.path.basename(filepath)} ({len(content)/1024:.1f} KB)")
            return True
        except Exception as e:
            print(f"   ❌ Error escribiendo archivo: {e}")
            return False

    def _level_1_together(self, prompt, filepath):
        print("   🚀 Intentando Nivel 1: Together AI (FLUX.1-schnell)...")
        try:
            response = self.together_client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell",
                width=1280, # Landscape
                height=720,
                steps=4,
                n=1,
                response_format="base64"
            )
            
            # Extraer Base64 y decodificar
            b64_data = response.data[0].b64_json
            image_bytes = base64.b64decode(b64_data)
            
            return self._save_bytes(image_bytes, filepath)
            
        except Exception as e:
            print(f"   ⚠️ Together AI falló: {e}")
            return False

    def _level_2_pollinations(self, prompt, filepath):
        print("   🌺 Intentando Nivel 2: Pollinations (Flux)...")
        try:
            time.sleep(2) # Throttling ligero
            seed = random.randint(0, 999999)
            encoded = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true&safe=true&seed={seed}"
            
            response = requests.get(url, timeout=45)
            
            if response.status_code == 200:
                content = response.content
                # Filtro Anti-Spam (Rate Limit images are small)
                if len(content) > 100000: # > 100KB
                    return self._save_bytes(content, filepath)
                else:
                    print(f"   🚩 Imagen corrupta/limitada detectada ({len(content)} bytes). Descartando.")
                    return False
            
            print(f"   ⚠️ Pollinations falló (Status: {response.status_code})")
            return False
        except Exception as e:
            print(f"   ⚠️ Pollinations Exception: {e}")
            return False

    def _level_3_lexica(self, simple_prompt, filepath):
        print("   🔍 Intentando Nivel 3: Lexica (Search)...")
        try:
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(simple_prompt)}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])
                if images:
                    img_url = images[0]["src"]
                    img_resp = requests.get(img_url, timeout=15)
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
        
        if not os.path.exists(local_path):
            # Remote placeholder last resort
            return f"https://placehold.co/1280x720/000000/FFFFFF/png?text={category.upper()}+News"
            
        return f"/images/defaults/{filename}"

# Interfaz pública
def get_image(prompt, slug, category="ia"):
    engine = NovumVisualEngine()
    return engine.generate_and_save(prompt, slug, category)
