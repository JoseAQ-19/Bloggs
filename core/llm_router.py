import os
import time
import logging
from openai import OpenAI

# Structured logger for LLM routing — visible in GitHub Actions console
logger = logging.getLogger("llm_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LLMRouter:
    """
    Gestor Central de LLMs respaldado 100% por OmniRoute AI Gateway (http://localhost:8000/v1).
    OmniRoute gestiona internamente los Rate Limits (429), balanceo de carga y la rotación inteligente de modelos en modo 'auto'.
    """

    @staticmethod
    def call_omniroute(prompt, system_prompt, model_type="reasoning", temperature=0.7):
        """
        Envía la solicitud al endpoint de OmniRoute Gateway en segundo plano.
        Base URL: os.getenv("OMNIROUTE_BASE_URL", "http://localhost:8000/v1")
        API Key: os.getenv("OMNIROUTE_API_KEY", "sk-omniroute")
        Model: os.getenv("LLM_MODEL", "auto")
        """
        base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:8000/v1")
        api_key = os.getenv("OMNIROUTE_API_KEY", "sk-omniroute")
        
        if model_type == "coding":
            model = os.getenv("LLM_MODEL_CODING", "auto/coding")
        else:
            model = os.getenv("LLM_MODEL", "auto")

        if os.getenv("OMNIROUTE_ENABLED", "true").lower() in ("false", "0", "no"):
            logger.warning("[OMNIROUTE] OmniRoute está deshabilitado por variable de entorno.")
            return None

        try:
            logger.info(f"[OMNIROUTE] Solicitando a OmniRoute ({base_url}) con modelo '{model}'...")
            client = OpenAI(api_key=api_key, base_url=base_url)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=8192,
                timeout=int(os.getenv("OMNIROUTE_TIMEOUT", "60"))
            )
            
            result = resp.choices[0].message.content
            if result:
                result = result.strip()
                word_count = len(result.split())
                logger.info(f"[OMNIROUTE] [SUCCESS] OmniRoute respondió con éxito ({word_count} palabras).")
                return result
            else:
                logger.warning("[OMNIROUTE] OmniRoute devolvió respuesta vacía.")
                return None

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:200]
            logger.warning(f"[OMNIROUTE] Error en OmniRoute ({base_url}) → {error_type}: {error_msg}")
            return None

    @staticmethod
    def call_capa_cero(prompt, system_prompt, model_type="reasoning", temperature=0.7):
        """
        Wrapper de compatibilidad: delega directamente en call_omniroute.
        """
        return LLMRouter.call_omniroute(prompt, system_prompt, model_type=model_type, temperature=temperature)

    @staticmethod
    def route_call(prompt, system_prompt, fallback_func=None, model_type="reasoning", temperature=0.7):
        """
        Enrutador Principal: Delegación 100% en OmniRoute con fallback de seguridad opcional.
        """
        # --- LLAMADA PRINCIPAL: OMNIROUTE AI GATEWAY ---
        res = LLMRouter.call_omniroute(prompt, system_prompt, model_type, temperature)
        if res:
            return res

        # --- FALLBACK DE SEGURIDAD (Si OmniRoute falla y se proporciona fallback) ---
        if fallback_func:
            logger.warning(f"[ROUTE] OmniRoute no disponible o sin respuesta. Escalando a FALLBACK_FUNC ({model_type})...")
            try:
                fallback_res = fallback_func(prompt, system_prompt)
                if fallback_res:
                    logger.info(f"[ROUTE] Fallback_func respondió con éxito ({len(fallback_res)} chars).")
                else:
                    logger.error("[ROUTE] Fallback_func devolvió None.")
                return fallback_res
            except Exception as e:
                logger.critical(f"[ROUTE] Fallo en Fallback_func: {type(e).__name__}: {e}")
                return None

        logger.error("[ROUTE] OmniRoute falló y no se proporcionó fallback_func.")
        return None
