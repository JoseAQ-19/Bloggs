import os
import requests
import random
import time
import base64
import urllib.parse
from together import Together

class NovumVisualEngine:
    """
    Motor Gráfico Platinum (Together AI FLUX + Lexica Fallback).
    Prioridad: Calidad SOTA y Velocidad.
    """
    
    STATIC_DIR = "static/images"
    DEFAULT_DIR = "static/images/defaults"
    
    AESTHETICS = {
        "ia": "cyberpunk style, neon blue and purple lighting, futuristic laboratory, detailed circuit boards, cinematic 8k, unreal engine 5 render, high contrast",
        "crypto": "matrix code rain style, golden bitcoin physical coin, stock market charts background, dark green theme, financial district night, ultra realistic, bloomberg terminal vibe",
        "fitness": "gym atmosphere, crossfit athlete silhouette, dramatic lighting, sweat details, orange and black theme, motivational poster style, sharp focus",
        "youtube": "youtube play button 3d render, red glowing neon, streaming studio setup, microphone and camera shallow depth of field, vibrant colors, 4k",
        "viral": "pop art style, vibrant colors, shocked emoji 3d render, chaotic internet collage, trending topic visualization, glossy finish, high saturation",
        "tools": "isometric 3d technical diagram, blueprint style, neon blue lines, engineering drafting table, clean minimalist tech"
    }

    def __init__(self):
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.DEFAULT_DIR, exist_ok=True)
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if self.together_key else None

    def generate_and_save(self, prompt, slug, category="ia"):
        print(f"💎 [VisualEngine Platinum] Procesando: {slug}")
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # 1. Enriquecer Prompt
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        enhanced_prompt = f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9"

        # 2. MOTOR 1: TOGETHER AI (FLUX)
        if self.together_client:
            if self._generate_together(enhanced_prompt, filepath):
                return f"/images/{filename}"
        else:
            print("   ⚠️ No Together API Key found.")

        # 3. MOTOR 2: LEXICA (Fallback Seguro)
        if self._search_lexica(prompt, filepath):
            return f"/images/{filename}"

        # 4. FALLBACK FINAL
        return self._get_fallback_image(category)

    def _generate_together(self, prompt, filepath):
        print("   🚀 Generando con Together AI (FLUX.1-schnell)...")
        try:
            response = self.together_client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell",
                width=1280,
                height=720,
                steps=4,
                n=1,
                response_format="b64_json"
            )
            
            b64_data = response.data[0].b64_json
            image_bytes = base64.b64decode(b64_data)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            print(f"   ✅ Imagen FLUX generada ({len(image_bytes)/1024:.1f} KB)")
            return True
            
        except Exception as e:
            print(f"   ❌ Error Together AI: {e}")
            return False

    def _search_lexica(self, simple_prompt, filepath):
        print("   🔍 Buscando respaldo en Lexica...")
        try:
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(simple_prompt)}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("images"):
                    img_url = data["images"][0]["src"]
                    img_resp = requests.get(img_url, timeout=15)
                    if img_resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        return True
            return False
        except:
            return False

    def _get_fallback_image(self, category):
        filename = f"default-{category}.jpg"
        local_path = os.path.join(self.DEFAULT_DIR, filename)
        if not os.path.exists(local_path):
            return f"https://placehold.co/1280x720/000000/FFFFFF/png?text={category.upper()}"
        return f"/images/defaults/{filename}"

def get_image(prompt, slug, category="ia"):
    engine = NovumVisualEngine()
    return engine.generate_and_save(prompt, slug, category)
