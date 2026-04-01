import os
import requests
import time
import base64
import urllib.parse
import random
from together import Together
from dotenv import load_dotenv

from visual_context_extractor import build_image_prompt
from visual_logger import VisualLogger

# Cargar entorno
load_dotenv()

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Archivo de estado persistente para intercalado entre ejecuciones
PENDULUM_STATE_FILE = os.path.join(BASE_DIR, "data", ".last_image_api.txt")


class NovumVisualEngine:
    """
    Motor Gráfico V6 — Sistema Péndulo Triple (NVIDIA/Together/HF Intercalado Estricto).
    
    Arquitectura:
    - Turno A: NVIDIA SD3 Medium
    - Turno B: Together AI (FLUX.1-schnell)
    - Turno C: Hugging Face Serverless (FLUX.1-schnell)
    - Fallback cruzado: si falla el turno asignado, usa los otros motores.
    - Red de seguridad: Lexica → Default local
    - NUNCA devuelve URLs externas. Siempre rutas locales /images/...
    """
    
    STATIC_DIR = os.path.join(BASE_DIR, "static/images")
    DEFAULT_DIR = os.path.join(BASE_DIR, "static/images/defaults")

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
    # FASE 1: SISTEMA PÉNDULO (TICK-TOCK-TACK)
    # =========================================================

    def _read_pendulum_state(self):
        """Lee el último proveedor usado del archivo de estado persistente."""
        try:
            if os.path.exists(PENDULUM_STATE_FILE):
                with open(PENDULUM_STATE_FILE, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "hf"  # Default fallback to make `nvidia` start first

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
        Determina qué API usar siguiendo el patrón A/B/C rotativo. (NVIDIA / TOGETHER / HF)
        """
        last_used = self._read_pendulum_state()
        
        providers = ["nvidia", "together", "hf"]
        
        try:
            base_idx = providers.index(last_used)
        except ValueError:
            base_idx = -1
            
        next_idx = (base_idx + 1 + self._call_index) % len(providers)
        self._call_index += 1
        
        return providers[next_idx]

    # =========================================================
    # ENTRADA PRINCIPAL
    # =========================================================

    def generate_and_save(self, title, content, slug, category="ia"):
        print(f"🎨 [VisualEngine V6] Procesando: {slug}")
        filename = f"{slug}.jpg"
        filepath = os.path.join(self.STATIC_DIR, filename)

        # Generar prompt dinámico usando el Context Extractor
        enhanced_prompt = build_image_prompt(title, content, category)

        provider = self._get_next_provider()
        print(f"   🔄 Péndulo (Multi-API) → Turno Asignado: {provider.upper()}")

        success = False
        final_provider = provider

        if provider == "nvidia":
            print("   🟢 [Turno Activo] Intentando NVIDIA SD3 Medium...")
            success = self._generate_nvidia_sd3(enhanced_prompt, filepath)
            if not success:
                print("   ⚠️ NVIDIA SD3 falló. Intentando Together AI...")
                final_provider = "together"
                success = self._try_together_then_hf(enhanced_prompt, filepath)
                if not success: final_provider = "hf" # assuming hf would be tried inside _try_together_then_hf
        elif provider == "together":
            print("   🟢 [Turno Activo] Intentando Together AI...")
            success = self._try_together_then_hf(enhanced_prompt, filepath)
            final_provider = "together" if success else "nvidia" # Not perfectly accurate parsing inside, but simple enough
            if not success:
                print("   ⚠️ Together/HF fallaron. Intentando NVIDIA SD3...")
                success = self._generate_nvidia_sd3(enhanced_prompt, filepath)
        elif provider == "hf":
            print("   🟢 [Turno Activo] Intentando Hugging Face...")
            success = self._try_hf_then_together(enhanced_prompt, filepath)
            final_provider = "hf" if success else "nvidia"
            if not success:
                print("   ⚠️ HF/Together fallaron. Intentando NVIDIA SD3...")
                success = self._generate_nvidia_sd3(enhanced_prompt, filepath)

        if success:
            self._write_pendulum_state(provider)
            # Log successful generation
            VisualLogger.log(slug, category, title, enhanced_prompt, final_provider, "success")
            return f"/images/{filename}"

        # Red de seguridad: Lexica
        print("   🔍 Todas las APIs primarias fallaron. Intentando Lexica...")
        if self._search_lexica(title, filepath):
            self._write_pendulum_state(provider)
            VisualLogger.log(slug, category, title, title, "lexica_fallback", "success_fallback")
            return f"/images/{filename}"

        # Fallback local (NUNCA URLs externas)
        VisualLogger.log(slug, category, title, enhanced_prompt, "local_fallback", "failed_generation")
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
                "negative_prompt": "ugly, text, watermark, blurry, low resolution, cartoon, 3d render, distorted, extra fingers, bad anatomy",
                "cfg_scale": random.uniform(4.0, 7.0), # Variabilidad de guidance
                "aspect_ratio": "16:9",
                "steps": 30,
                "seed": random.randint(0, 4294967295)  # Destruyendo el Efecto Clon
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

def get_image(title, content, slug, category="ia"):
    """
    Punto de entrada principal. Usa un singleton para que el estado
    del péndulo se mantenga entre llamadas dentro del mismo proceso.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = NovumVisualEngine()
    return _engine_instance.generate_and_save(title, content, slug, category)
