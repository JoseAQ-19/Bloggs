import os
import requests
import random
import time
import base64
import urllib.parse
from together import Together
from dotenv import load_dotenv

# Cargar entorno (Seguridad para scripts externos)
load_dotenv()

# Ruta base del proyecto (para rutas absolutas robustas)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class NovumVisualEngine:
    """
    Motor Gráfico V4 (Together AI + Lexica Fallback).
    Arquitectura simplificada: Together → Lexica → Default Local.
    NUNCA devuelve URLs externas. Siempre rutas locales /images/...
    """
    
    STATIC_DIR = os.path.join(BASE_DIR, "static/images")
    DEFAULT_DIR = os.path.join(BASE_DIR, "static/images/defaults")
    
    # ADN Visual
    AESTHETICS = {
        "ia": "cyberpunk style, neon blue and purple lighting, futuristic laboratory, detailed circuit boards, cinematic 8k, unreal engine 5 render, high contrast",
        "crypto": "matrix code rain style, golden bitcoin physical coin, stock market charts background, dark green theme, financial district night, ultra realistic, bloomberg terminal vibe",
        "fitness": "gym atmosphere, crossfit athlete silhouette, dramatic lighting, sweat details, orange and black theme, motivational poster style, sharp focus",
        "youtube": "youtube play button 3d render, red glowing neon, streaming studio setup, microphone and camera shallow depth of field, vibrant colors, 4k",
        "viral": "editorial photography, neon purple and yellow lighting, high fashion, trending topic visualization, cinematic 8k, sharp focus, no cartoons, serious journalism style",
        "tools": "isometric 3d technical diagram, blueprint style, neon blue lines, engineering drafting table, clean minimalist tech"
    }

    def __init__(self):
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.DEFAULT_DIR, exist_ok=True)
        
        # Client único: Together AI
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if self.together_key else None

    def generate_and_save(self, prompt, slug, category="ia"):
        print(f"🎨 [VisualEngine] Procesando: {slug}")
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # Enriquecer Prompt
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        enhanced_prompt = f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9"

        # 1. TOGETHER AI (Principal)
        if self.together_client:
            if self._generate_together(enhanced_prompt, filepath):
                return f"/images/{filename}"
            print("   ⚠️ Together falló. Intentando Lexica...")
        else:
            print("   ⚠️ TOGETHER_API_KEY no configurada. Saltando generación AI.")

        # 2. RED DE SEGURIDAD: LEXICA
        if self._search_lexica(prompt, filepath):
            return f"/images/{filename}"

        # 3. FALLBACK LOCAL (NUNCA URLs externas)
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
        """Fallback determinista: SIEMPRE devuelve ruta local, NUNCA URL externa."""
        filename = f"default-{category}.jpg"
        local_path = os.path.join(self.DEFAULT_DIR, filename)
        if os.path.exists(local_path):
            print(f"   🛡️ Usando default local: {filename}")
            return f"/images/defaults/{filename}"
        
        # Si no existe el específico, buscar default genérico (ia)
        generic = os.path.join(self.DEFAULT_DIR, "default-ia.jpg")
        if os.path.exists(generic):
            print(f"   🛡️ Usando default genérico: default-ia.jpg")
            return "/images/defaults/default-ia.jpg"
        
        # Último recurso: ruta local que al menos no rompe el HTML
        print(f"   🚨 CRÍTICO: Sin imagen fallback para '{category}'.")
        return f"/images/defaults/default-{category}.jpg"

def get_image(prompt, slug, category="ia"):
    engine = NovumVisualEngine()
    return engine.generate_and_save(prompt, slug, category)
