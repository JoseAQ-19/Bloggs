import os
import requests
import random
import time
import base64
import urllib.parse
from together import Together
from openai import OpenAI

class NovumVisualEngine:
    """
    Motor Gráfico Híbrido V3 (Together + Nebius + Lexica).
    Arquitectura: Rey y Heredero (Prioridad de Coste/Calidad).
    """
    
    STATIC_DIR = "static/images"
    DEFAULT_DIR = "static/images/defaults"
    
    # ADN Visual
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
        
        # Clients
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if self.together_key else None
        
        self.nebius_key = os.getenv("NEBIUS_API_KEY")
        # Nebius usa OpenAI SDK client
        self.nebius_client = OpenAI(base_url="https://api.studio.nebius.ai/v1/", api_key=self.nebius_key) if self.nebius_key else None

    def generate_and_save(self, prompt, slug, category="ia"):
        print(f"🎨 [VisualEngine] Procesando: {slug}")
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # Enriquecer Prompt
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        enhanced_prompt = f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9"

        # 1. EL REY: TOGETHER AI
        if self.together_client:
            if self._generate_together(enhanced_prompt, filepath):
                return f"/images/{filename}"
        
        # 2. EL HEREDERO: NEBIUS AI
        if self.nebius_client:
            if self._generate_nebius(enhanced_prompt, filepath):
                return f"/images/{filename}"

        # 3. RED DE SEGURIDAD: LEXICA
        if self._search_lexica(prompt, filepath):
            return f"/images/{filename}"

        # 4. FALLBACK FINAL
        return self._get_fallback_image(category)

    def _save_bytes(self, content, filepath):
        try:
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"   ✅ Guardado: {os.path.basename(filepath)} ({len(content)/1024:.1f} KB)")
            return True
        except Exception as e:
            print(f"   ❌ Error IO: {e}")
            return False

    def _generate_together(self, prompt, filepath):
        print("   👑 [1] Together AI (FLUX)...")
        try:
            response = self.together_client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell",
                width=1280, height=720, steps=4, n=1,
                response_format="b64_json"
            )
            image_bytes = base64.b64decode(response.data[0].b64_json)
            return self._save_bytes(image_bytes, filepath)
        except Exception as e:
            print(f"   ⚠️ Together falló: {e}")
            return False

    def _generate_nebius(self, prompt, filepath):
        print("   ⚔️ [2] Nebius AI (FLUX)...")
        try:
            # Nebius devuelve URL, no base64 directo usualmente con OpenAI sdk standard para imagenes
            response = self.nebius_client.images.generate(
                model="black-forest-labs/FLUX.1-schnell",
                prompt=prompt,
                size="1024x1024", # Ajustar si soportan landscape
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            
            # Descargar la URL
            img_resp = requests.get(image_url, timeout=30)
            if img_resp.status_code == 200:
                return self._save_bytes(img_resp.content, filepath)
            return False
        except Exception as e:
            print(f"   ⚠️ Nebius falló: {e}")
            return False

    def _search_lexica(self, simple_prompt, filepath):
        print("   🔍 [3] Lexica Search...")
        try:
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(simple_prompt)}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("images"):
                    img_url = data["images"][0]["src"]
                    img_resp = requests.get(img_url, timeout=15)
                    if img_resp.status_code == 200:
                        return self._save_bytes(img_resp.content, filepath)
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
