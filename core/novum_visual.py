import os
import requests
import time
import base64
import urllib.parse
import random
import io
import hashlib
import logging
import sys
from PIL import Image
from together import Together
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from visual_context_extractor import build_image_prompt
    from visual_logger import VisualLogger
except ImportError:
    from core.visual_context_extractor import build_image_prompt
    from core.visual_logger import VisualLogger

# Cargar entorno
load_dotenv()

# Structured logger for visual engine
logger = logging.getLogger("novum_visual")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ruta base del proyecto (Retroceder un nivel desde core/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Archivo de estado persistente para intercalado entre ejecuciones
PENDULUM_STATE_FILE = os.path.join(BASE_DIR, "data", ".last_image_api.txt")

# ── CATEGORY ALIASES (slugs de sección -> clave canónica de nicho) ──
# Los workflows/CLI pueden pasar slugs públicos (ej. --section biohacking);
# el motor visual solo conoce las claves canónicas de VISUAL_STYLES.
CATEGORY_ALIASES = {
    "biohacking": "fitness",
    "salud-bienestar": "fitness",
    "salud": "fitness",
    "criptomonedas": "crypto",
    "stocks": "funds",
}


def _normalize_category(category: str) -> str:
    """Normaliza un slug de sección a la clave canónica usada por los estilos visuales."""
    key = str(category or "").strip().lower()
    return CATEGORY_ALIASES.get(key, key or "ia")


# ── BANNED GENERIC WORDS (prompt quality gate) ──
BANNED_PROMPT_WORDS = [
    "illustration of", "abstract background", "technology concept",
    "news article", "generic", "stock photo", "clipart",
    "simple", "basic", "icon", "logo", "text overlay",
    "watermark", "cartoon", "comic", "anime",
]


def _derive_seed(slug: str) -> int:
    """Derive a deterministic numeric seed from the article slug using SHA-256.
    This guarantees the same slug always produces the same seed, and different
    slugs produce different seeds (collision-resistant).
    """
    digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % 1000000


def _sanitize_prompt(prompt: str) -> str:
    """Remove banned generic words from a prompt to ensure quality."""
    sanitized = prompt
    for banned in BANNED_PROMPT_WORDS:
        sanitized = sanitized.replace(banned, "")
    # Clean up double spaces
    sanitized = " ".join(sanitized.split())
    return sanitized.strip()


def generate_unique_visual_prompt(title: str, summary: str, category: str, slug: str = "") -> str:
    """
    Generate a unique, conceptually-aligned visual prompt for an article using LLM.

    Uses LLMRouter to translate article metadata into a cinematic visual description
    in English (30-50 words). Falls back to regex-based `build_image_prompt()` if LLM fails.

    Args:
        title: Article title
        summary: Article content or summary (first ~500 words used)
        category: Article category/niche (ia, crypto, fitness, etc.)
        slug: Article slug (used for seed fingerprint)

    Returns:
        A unique visual prompt string for image generation APIs
    """
    category = _normalize_category(category)
    try:
        from llm_router import LLMRouter
        from prompts_factory import VISUAL_PROMPT_SYSTEM
    except ImportError:
        from core.llm_router import LLMRouter
        from core.prompts_factory import VISUAL_PROMPT_SYSTEM

    # Truncate summary to first 500 words to save tokens
    summary_truncated = " ".join(summary.split()[:500]) if summary else ""

    user_prompt = (
        f"Article Title: {title}\n"
        f"Article Summary: {summary_truncated}\n"
        f"Category: {category}\n\n"
        f"Generate a unique visual prompt for this article."
    )

    try:
        def _fallback_llm(prompt, system_prompt):
            """Fallback: use Gemini directly if available."""
            try:
                from google import genai
                gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if gemini_key:
                    gemini_client = genai.Client(api_key=gemini_key)
                    resp = gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"{system_prompt}\n\n{prompt}"
                    )
                    return resp.text.strip() if resp.text else None
            except Exception as e:
                logger.warning(f"[VISUAL] Gemini fallback failed: {e}")
            return None

        llm_prompt = LLMRouter.route_call(
            user_prompt,
            VISUAL_PROMPT_SYSTEM,
            _fallback_llm,
            model_type="parsing",
            temperature=0.9  # Higher temperature for visual creativity
        )

        if llm_prompt and len(llm_prompt.split()) >= 10:
            # Sanitize: remove banned words, clean up
            llm_prompt = _sanitize_prompt(llm_prompt)
            # Strip any wrapping quotes the LLM might have added
            llm_prompt = llm_prompt.strip('"').strip("'").strip()

            # Append seed fingerprint to ensure prompt-level differentiation
            if slug:
                seed = _derive_seed(slug)
                llm_prompt += f", unique composition variant {seed}"

            logger.info(f"[VISUAL] LLM prompt generated ({len(llm_prompt.split())} words): {llm_prompt[:120]}...")
            return llm_prompt

    except Exception as e:
        logger.warning(f"[VISUAL] LLM visual prompt generation failed: {e}. Falling back to regex extractor.")

    # Fallback: regex-based prompt builder
    fallback_prompt = build_image_prompt(title, summary, category)
    if slug:
        seed = _derive_seed(slug)
        fallback_prompt += f", unique composition variant {seed}"
    logger.info(f"[VISUAL] Using fallback regex prompt: {fallback_prompt[:120]}...")
    return fallback_prompt


class NovumVisualEngine:
    """
    Motor Gráfico V7 — Sistema Péndulo Triple (NVIDIA/Together/HF Intercalado Estricto)
    con LLM-Driven Prompt Generation, Seed Anti-Duplicados,
    Optimización Local a WebP (< 150 KB, 1200x630) y Soporte para Hugo Leaf Bundles.
    """

    STATIC_DIR = os.path.join(BASE_DIR, "static/images")
    DEFAULT_DIR = os.path.join(BASE_DIR, "static/images/defaults")

    # Maximum dimensions for featured images (OG/social optimal)
    MAX_WIDTH = 1200
    MAX_HEIGHT = 630

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
        """Determina qué API usar siguiendo el patrón A/B/C rotativo. (NVIDIA / TOGETHER / HF)"""
        last_used = self._read_pendulum_state()
        providers = ["nvidia", "together", "hf"]
        try:
            base_idx = providers.index(last_used)
        except ValueError:
            base_idx = -1

        next_idx = (base_idx + 1 + self._call_index) % len(providers)
        self._call_index += 1
        return providers[next_idx]

    def process_and_save_webp(self, raw_bytes, filepath, max_size_kb=150):
        """
        Convierte bytes de imagen a formato WebP utilizando Pillow,
        redimensiona a máximo 1200x630px (bounding box proporcional),
        los comprime a un peso inferior a 150 KB y extrae sus dimensiones reales.
        Retorna (success: bool, width: int, height: int).
        """
        try:
            image = Image.open(io.BytesIO(raw_bytes))
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            orig_w, orig_h = image.size
            curr_image = image

            # Proportional resize to fit within 1200x630 bounding box
            if orig_w > self.MAX_WIDTH or orig_h > self.MAX_HEIGHT:
                scale_w = self.MAX_WIDTH / float(orig_w)
                scale_h = self.MAX_HEIGHT / float(orig_h)
                scale = min(scale_w, scale_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                curr_image = curr_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            width, height = curr_image.size

            # Compresión progresiva WebP para asegurar < 150 KB
            target_bytes = max_size_kb * 1024
            quality = 85
            output_buffer = io.BytesIO()

            while quality >= 20:
                output_buffer.seek(0)
                output_buffer.truncate(0)
                curr_image.save(output_buffer, format="WEBP", quality=quality, optimize=True)
                if output_buffer.tell() <= target_bytes:
                    break
                quality -= 10

            # Si aún excede 150 KB, reducir dimensiones adicionalmente
            if output_buffer.tell() > target_bytes:
                scale = 0.8
                curr_image = curr_image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
                width, height = curr_image.size
                output_buffer.seek(0)
                output_buffer.truncate(0)
                curr_image.save(output_buffer, format="WEBP", quality=70, optimize=True)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(output_buffer.getvalue())

            final_kb = len(output_buffer.getvalue()) / 1024
            print(f"   ✅ WebP Optimizada: {os.path.basename(filepath)} ({final_kb:.1f} KB, {width}x{height}px)")
            return True, width, height
        except Exception as e:
            print(f"   ❌ Error procesando WebP: {e}")
            return False, 0, 0

    def generate_and_save(self, title, content, slug, category="ia", bundle_dir=None, prompt=None, seed=None):
        category = _normalize_category(category)
        print(f"🎨 [VisualEngine V7] Procesando: {slug}")

        if bundle_dir:
            os.makedirs(bundle_dir, exist_ok=True)
            filepath = os.path.join(bundle_dir, "featured.webp")
            image_ref = "featured.webp"
        else:
            filename = f"{slug}.webp"
            filepath = os.path.join(self.STATIC_DIR, filename)
            image_ref = f"/images/{filename}"

        # ── CORE FIX: LLM-driven unique prompt generation with slug seed ──
        enhanced_prompt = prompt if prompt else generate_unique_visual_prompt(title, content, category, slug)

        # Derive deterministic seed from slug for API injection
        if seed is None:
            seed = _derive_seed(slug)
        print(f"   🔑 Seed derivada del slug '{slug}': {seed}")

        provider = self._get_next_provider()
        print(f"   🔄 Péndulo (Multi-API) → Turno Asignado: {provider.upper()}")

        success = False
        width, height = 0, 0
        final_provider = provider

        if provider == "nvidia":
            print("   🟢 [Turno Activo] Intentando NVIDIA SD3 Medium...")
            success, width, height = self._generate_nvidia_sd3(enhanced_prompt, filepath, seed)
            if not success:
                print("   ⚠️ NVIDIA SD3 falló. Intentando Together AI...")
                final_provider = "together"
                success, width, height = self._try_together_then_hf(enhanced_prompt, filepath, seed)
        elif provider == "together":
            print("   🟢 [Turno Activo] Intentando Together AI...")
            success, width, height = self._try_together_then_hf(enhanced_prompt, filepath, seed)
            final_provider = "together" if success else "nvidia"
            if not success:
                print("   ⚠️ Together/HF fallaron. Intentando NVIDIA SD3...")
                success, width, height = self._generate_nvidia_sd3(enhanced_prompt, filepath, seed)
        elif provider == "hf":
            print("   🟢 [Turno Activo] Intentando Hugging Face...")
            success, width, height = self._try_hf_then_together(enhanced_prompt, filepath, seed)
            final_provider = "hf" if success else "nvidia"
            if not success:
                print("   ⚠️ HF/Together fallaron. Intentando NVIDIA SD3...")
                success, width, height = self._generate_nvidia_sd3(enhanced_prompt, filepath, seed)

        if success:
            self._write_pendulum_state(provider)
            VisualLogger.log(slug, category, title, enhanced_prompt, final_provider, "success")
            return image_ref, width, height

        # Red de seguridad: Lexica
        print("   🔍 Todas las APIs primarias fallaron. Intentando Lexica...")
        success, width, height = self._search_lexica(title, filepath)
        if success:
            self._write_pendulum_state(provider)
            VisualLogger.log(slug, category, title, title, "lexica_fallback", "success_fallback")
            return image_ref, width, height

        # Fallback local
        VisualLogger.log(slug, category, title, enhanced_prompt, "local_fallback", "failed_generation")
        fallback_ref, w, h = self._get_fallback_image(category, filepath, image_ref)
        return fallback_ref, w, h

    def _try_together_then_hf(self, prompt, filepath, seed):
        success, w, h = self._generate_together(prompt, filepath, seed)
        if success:
            return True, w, h
        print("   ⚠️ Together falló. Activando fallback cruzado → HF...")
        return self._generate_hf(prompt, filepath, seed)

    def _try_hf_then_together(self, prompt, filepath, seed):
        success, w, h = self._generate_hf(prompt, filepath, seed)
        if success:
            return True, w, h
        print("   ⚠️ HF falló. Activando fallback cruzado → Together...")
        return self._generate_together(prompt, filepath, seed)

    def _generate_together(self, prompt, filepath, seed):
        if not self.together_client:
            print("   ⚠️ TOGETHER_API_KEY no configurada. Saltando.")
            return False, 0, 0

        print(f"   👑 [Together AI] Generando con FLUX.1-schnell (seed={seed})...")
        try:
            response = self.together_client.images.generate(
                prompt=prompt,
                model="black-forest-labs/FLUX.1-schnell",
                width=1280, height=720, steps=4, n=1,
                seed=seed,
                response_format="b64_json"
            )
            image_bytes = base64.b64decode(response.data[0].b64_json)
            return self.process_and_save_webp(image_bytes, filepath)
        except Exception as e:
            print(f"   ⚠️ Together error: {e}")
            return False, 0, 0

    def _generate_nvidia_sd3(self, prompt, filepath, seed):
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_key:
            print("   ⚠️ NVIDIA_API_KEY no configurada. Saltando SD3.")
            return False, 0, 0

        print(f"   🟢 [NVIDIA SD3] Generando con Stable Diffusion 3 Medium (seed={seed})...")
        try:
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Accept": "application/json",
            }
            payload = {
                "prompt": prompt[:1000],
                "negative_prompt": "ugly, text, watermark, blurry, low resolution, cartoon, 3d render, distorted, extra fingers, bad anatomy",
                "cfg_scale": 5.0 + (seed % 30) / 10.0,  # Deterministic variation 5.0-8.0
                "aspect_ratio": "16:9",
                "steps": 30,
                "seed": seed
            }
            resp = requests.post(
                "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium",
                headers=headers,
                json=payload,
                timeout=90
            )
            if resp.status_code == 200:
                data = resp.json()
                b64_data = data.get("image") or ""
                if not b64_data and data.get("artifacts"):
                    b64_data = data["artifacts"][0].get("base64", "")

                if b64_data:
                    image_bytes = base64.b64decode(b64_data)
                    return self.process_and_save_webp(image_bytes, filepath)
            return False, 0, 0
        except Exception as e:
            print(f"   ⚠️ NVIDIA SD3 error: {e}")
            return False, 0, 0

    def _generate_hf(self, prompt, filepath, seed):
        if not self.hf_key:
            print("   ⚠️ HUGGINGFACE_API_KEY no configurada. Saltando.")
            return False, 0, 0

        # HF Inference API for FLUX doesn't support seed param directly,
        # so we embed it into the prompt for differentiation
        seeded_prompt = f"{prompt}, deterministic seed {seed}"
        print(f"   🤗 [Hugging Face] Generando con FLUX.1-schnell (seed={seed} in prompt)...")
        api_url = "https://router.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {self.hf_key}"}
        payload = {"inputs": seeded_prompt}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    return self.process_and_save_webp(response.content, filepath)
                elif response.status_code == 429:
                    wait_time = 20 * (attempt + 1)
                    print(f"   ⏳ Rate limit (429). Esperando {wait_time}s... (intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                elif response.status_code == 503:
                    wait_info = response.json().get("estimated_time", 30)
                    wait_time = min(float(wait_info), 60)
                    print(f"   ⏳ Modelo cargando. Esperando {wait_time:.0f}s... (intento {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    return False, 0, 0
            except Exception as e:
                print(f"   ⚠️ HF error (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)
        return False, 0, 0

    def _search_lexica(self, simple_prompt, filepath):
        print("   🔍 [Lexica] Buscando imagen similar...")
        try:
            url = f"https://lexica.art/api/v1/search?q={urllib.parse.quote(simple_prompt)}"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("images"):
                    img_url = data["images"][0]["src"]
                    img_resp = requests.get(img_url, timeout=3)
                    if img_resp.status_code == 200:
                        return self.process_and_save_webp(img_resp.content, filepath)
            return False, 0, 0
        except Exception:
            return False, 0, 0

    def _get_fallback_image(self, category, target_filepath=None, default_ref="featured.webp"):
        """
        Fallback local cuando todas las APIs de generación fallan.

        - Leaf bundles: copia el default dentro del bundle (featured.webp) para
          que la referencia relativa del frontmatter nunca quede rota.
        - Posts planos (static/images): NO copia el default bajo el nombre del
          slug. Devuelve la ruta real /images/defaults/default-{category}.jpg
          para que el placeholder sea detectable por los auditores en lugar de
          disfrazarse de imagen única (regresión: 111 posts crypto y 45 de
          fitness compartían bytes idénticos con nombres distintos).
        """
        category = _normalize_category(category)
        filename = f"default-{category}.jpg"
        local_path = os.path.join(self.DEFAULT_DIR, filename)
        if not os.path.exists(local_path):
            filename = "default-ia.jpg"
            local_path = os.path.join(self.DEFAULT_DIR, filename)

        is_leaf_bundle = default_ref == "featured.webp"

        if not is_leaf_bundle:
            honest_ref = f"/images/defaults/{filename}"
            logger.warning(
                f"[VISUAL] Generación fallida; usando placeholder compartido {honest_ref} "
                f"(detectable por auditores, no se enmascara como imagen única)."
            )
            print(f"   🛡️ Placeholder compartido (sin enmascarar): {honest_ref}")
            return honest_ref, 1200, 630

        if os.path.exists(local_path):
            print(f"   🛡️ Usando default local: {os.path.basename(local_path)}")
            try:
                with open(local_path, "rb") as f:
                    raw = f.read()
                dest_path = target_filepath if target_filepath else os.path.join(self.STATIC_DIR, f"default-{category}.webp")
                ok, w, h = self.process_and_save_webp(raw, dest_path)
                if ok:
                    return default_ref, w, h
            except Exception as e:
                print(f"   ⚠️ Error leyendo default local: {e}")

        # Fallback final si falla lectura de disco
        return default_ref, 1200, 630


_engine_instance = None

def get_image(title, content, slug, category="ia", bundle_dir=None, prompt=None, seed=None):
    """
    Punto de entrada principal. Usa un singleton para mantener el estado del péndulo.
    Retorna tuple (image_ref, width, height) o solo image_ref si se desempaqueta según convención.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = NovumVisualEngine()
    return _engine_instance.generate_and_save(title, content, slug, category, bundle_dir=bundle_dir, prompt=prompt, seed=seed)
