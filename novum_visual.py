import os
import requests
import time
import base64
import urllib.parse
from together import Together
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Archivo de estado persistente para intercalado entre ejecuciones
PENDULUM_STATE_FILE = os.path.join(BASE_DIR, "data", ".last_image_api.txt")


class NovumVisualEngine:
    """
    Motor Gráfico V5 — Sistema Péndulo (Together/HF Intercalado Estricto).
    
    Arquitectura:
    - Turno A (par):  Together AI (FLUX.1-schnell)
    - Turno B (impar): Hugging Face Serverless (FLUX.1-schnell)
    - Fallback cruzado: si falla el turno asignado, usa la otra API
    - Red de seguridad: Lexica → Default local
    - NUNCA devuelve URLs externas. Siempre rutas locales /images/...
    """
    
    STATIC_DIR = os.path.join(BASE_DIR, "static/images")
    DEFAULT_DIR = os.path.join(BASE_DIR, "static/images/defaults")
    
    # ADN Visual (prompts estéticos por categoría)
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
        
        # Together AI client
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if self.together_key else None
        
        # Hugging Face API key
        self.hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_API_KEY")
        
        # Pendulum state — tracks which API to use next within a single run
        self._call_index = 0

    # =========================================================
    # FASE 1: SISTEMA PÉNDULO (TICK-TOCK)
    # =========================================================

    def _read_pendulum_state(self):
        """Lee el último proveedor usado del archivo de estado persistente."""
        try:
            if os.path.exists(PENDULUM_STATE_FILE):
                with open(PENDULUM_STATE_FILE, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "hf"  # Default: last was HF → first call will use Together

    def _write_pendulum_state(self, provider):
        """Escribe qué proveedor acaba de ser usado."""
        try:
            os.makedirs(os.path.dirname(PENDULUM_STATE_FILE), exist_ok=True)
            with open(PENDULUM_STATE_FILE, 'w') as f:
                f.write(provider)
        except Exception as e:
            print(f"   ⚠️ No se pudo guardar estado péndulo: {e}")

    def _get_next_provider(self):
        """
        Determina qué API usar siguiendo el patrón A/B/A/B estricto.
        
        - Dentro de la misma ejecución: usa el índice de llamada (_call_index)
        - Entre ejecuciones: lee el archivo de estado para continuar la alternancia
        """
        last_used = self._read_pendulum_state()
        
        # El offset base depende de qué se usó por última vez entre ejecuciones.
        # Si la última ejecución terminó con "together", empezamos con "hf" y viceversa.
        if last_used == "together":
            base_offset = 1  # impar = HF primero
        else:
            base_offset = 0  # par = Together primero
        
        effective_index = base_offset + self._call_index
        self._call_index += 1
        
        if effective_index % 2 == 0:
            return "together"
        else:
            return "hf"

    # =========================================================
    # ENTRADA PRINCIPAL
    # =========================================================

    def generate_and_save(self, prompt, slug, category="ia"):
        print(f"🎨 [VisualEngine V5] Procesando: {slug}")
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)
        
        # Enriquecer Prompt con ADN visual
        style = self.AESTHETICS.get(category, self.AESTHETICS["ia"])
        enhanced_prompt = f"{prompt}, {style}, editorial photography, wide angle, --ar 16:9"

        # Determinar turno del péndulo
        provider = self._get_next_provider()
        print(f"   🔄 Péndulo → Turno: {provider.upper()}")

        # Ejecutar con fallback cruzado
        if provider == "together":
            result = self._try_together_then_hf(enhanced_prompt, filepath)
        else:
            result = self._try_hf_then_together(enhanced_prompt, filepath)

        if result:
            self._write_pendulum_state(provider)
            return f"/images/{filename}"

        # Motor Premium: NVIDIA Stable Diffusion 3 Medium
        print("   🟢 Ambas APIs fallaron. Intentando NVIDIA SD3 Medium...")
        if self._generate_nvidia_sd3(enhanced_prompt, filepath):
            self._write_pendulum_state(provider)
            return f"/images/{filename}"

        # Red de seguridad: Lexica
        print("   🔍 NVIDIA SD3 también falló. Intentando Lexica...")
        if self._search_lexica(prompt, filepath):
            self._write_pendulum_state(provider)
            return f"/images/{filename}"

        # Fallback local (NUNCA URLs externas)
        return self._get_fallback_image(category)

    # =========================================================
    # PROVEEDORES CON FALLBACK CRUZADO
    # =========================================================

    def _try_together_then_hf(self, prompt, filepath):
        """Turno Together → Fallback a HF si falla."""
        if self._generate_together(prompt, filepath):
            return True
        print("   ⚠️ Together falló. Activando fallback cruzado → HF...")
        return self._generate_hf(prompt, filepath)

    def _try_hf_then_together(self, prompt, filepath):
        """Turno HF → Fallback a Together si falla."""
        if self._generate_hf(prompt, filepath):
            return True
        print("   ⚠️ HF falló. Activando fallback cruzado → Together...")
        return self._generate_together(prompt, filepath)

    # =========================================================
    # FASE 2: GENERADORES DE IMAGEN
    # =========================================================

    def _generate_together(self, prompt, filepath):
        """Together AI — FLUX.1-schnell."""
        if not self.together_client:
            print("   ⚠️ TOGETHER_API_KEY no configurada. Saltando.")
            return False
        
        print("   👑 [Together AI] Generando con FLUX.1-schnell...")
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
            print(f"   ⚠️ Together error: {e}")
            return False

    def _generate_nvidia_sd3(self, prompt, filepath):
        """
        NVIDIA Stable Diffusion 3 Medium — Generación de imagen premium.
        Usa la API REST directa de NVIDIA (no el SDK de OpenAI).
        """
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_key:
            print("   ⚠️ NVIDIA_API_KEY no configurada. Saltando SD3.")
            return False
        
        print("   🟢 [NVIDIA SD3] Generando con Stable Diffusion 3 Medium...")
        try:
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Accept": "application/json",
            }
            
            payload = {
                "prompt": prompt[:1000],  # NVIDIA limita el prompt
                "cfg_scale": 5,
                "aspect_ratio": "16:9",
                "steps": 30,
                "seed": 0  # Random seed
            }
            
            resp = requests.post(
                "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if resp.status_code == 200:
                data = resp.json()
                # NVIDIA devuelve base64 en "image" o "artifacts"
                b64_data = data.get("image") or ""
                if not b64_data and data.get("artifacts"):
                    b64_data = data["artifacts"][0].get("base64", "")
                
                if b64_data:
                    image_bytes = base64.b64decode(b64_data)
                    return self._save_bytes(image_bytes, filepath)
                else:
                    print(f"   ⚠️ NVIDIA SD3: respuesta sin datos de imagen. Keys: {list(data.keys())}")
                    return False
            elif resp.status_code == 402:
                print("   ⚠️ NVIDIA SD3: Créditos agotados (HTTP 402). Saltando.")
                return False
            else:
                print(f"   ⚠️ NVIDIA SD3 error HTTP {resp.status_code}: {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"   ⚠️ NVIDIA SD3 error: {e}")
            return False

    def _generate_hf(self, prompt, filepath):
        """
        Hugging Face Serverless Inference API — FLUX.1-schnell.
        Incluye protección anti-rate-limit con retry + backoff.
        """
        if not self.hf_key:
            print("   ⚠️ HUGGINGFACE_API_KEY no configurada. Saltando.")
            return False
        
        print("   🤗 [Hugging Face] Generando con FLUX.1-schnell...")
        
        api_url = "https://router.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {self.hf_key}"}
        payload = {"inputs": prompt}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    # HF devuelve la imagen directamente como bytes
                    return self._save_bytes(response.content, filepath)
                
                elif response.status_code == 429:
                    # Rate limit — esperar y reintentar
                    wait_time = 20 * (attempt + 1)
                    print(f"   ⏳ Rate limit (429). Esperando {wait_time}s... (intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 503:
                    # Modelo cargando — esperar
                    wait_info = response.json().get("estimated_time", 30)
                    wait_time = min(float(wait_info), 60)
                    print(f"   ⏳ Modelo cargando. Esperando {wait_time:.0f}s... (intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                else:
                    print(f"   ⚠️ HF error HTTP {response.status_code}: {response.text[:200]}")
                    return False
                    
            except Exception as e:
                print(f"   ⚠️ HF error (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)
        
        print("   ❌ HF agotó todos los reintentos.")
        return False

    # =========================================================
    # UTILIDADES Y FALLBACKS
    # =========================================================

    def _save_bytes(self, content, filepath):
        """Guarda bytes crudos a archivo."""
        try:
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"   ✅ Guardado: {os.path.basename(filepath)} ({len(content)/1024:.1f} KB)")
            return True
        except Exception as e:
            print(f"   ❌ Error IO: {e}")
            return False

    def _search_lexica(self, simple_prompt, filepath):
        """Búsqueda en Lexica.art como red de seguridad."""
        print("   🔍 [Lexica] Buscando imagen similar...")
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
        
        generic = os.path.join(self.DEFAULT_DIR, "default-ia.jpg")
        if os.path.exists(generic):
            print(f"   🛡️ Usando default genérico: default-ia.jpg")
            return "/images/defaults/default-ia.jpg"
        
        print(f"   🚨 CRÍTICO: Sin imagen fallback para '{category}'.")
        return f"/images/defaults/default-{category}.jpg"


# =========================================================
# INTERFAZ PÚBLICA (compatible con main.py)
# =========================================================

# Singleton para mantener el estado del péndulo dentro de una misma ejecución
_engine_instance = None

def get_image(prompt, slug, category="ia"):
    """
    Punto de entrada principal. Usa un singleton para que el estado
    del péndulo se mantenga entre llamadas dentro del mismo proceso.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = NovumVisualEngine()
    return _engine_instance.generate_and_save(prompt, slug, category)
