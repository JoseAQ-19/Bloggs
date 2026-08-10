import os
import time
import logging
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Structured logger for LLM routing — visible in GitHub Actions console
logger = logging.getLogger("llm_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LLMRouter:
    """
    Gestor Central de LLMs con Inyección de OmniRoute (AI Gateway Local), Capa Cero (GitHub Models) y Fallbacks.
    Misión: Priorizar el enrutamiento inteligente local, el ahorro de costes y alta disponibilidad ante Rate Limits.
    """

    @staticmethod
    def call_omniroute(prompt, system_prompt, model_type="reasoning", temperature=0.7):
        """
        Llama al Gateway AI local OmniRoute como proveedor primario.
        Endpoint por defecto: http://localhost:8000/v1
        Modelos por defecto: 'auto', 'auto/coding'
        """
        # Intentar obtener variables desde config.py o entorno
        try:
            import sys
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            from config import OMNIROUTE_BASE_URL, OMNIROUTE_API_KEY, OMNIROUTE_MODELS
            base_url = OMNIROUTE_BASE_URL
            api_key = OMNIROUTE_API_KEY
            models = OMNIROUTE_MODELS
        except ImportError:
            base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:8000/v1")
            api_key = os.getenv("OMNIROUTE_API_KEY", "sk-omniroute")
            models = ["auto", "auto/coding"]

        if os.getenv("OMNIROUTE_ENABLED", "true").lower() in ("false", "0", "no"):
            return None

        for model in models:
            try:
                logger.info(f"[OMNIROUTE] Intentando con modelo primario: {model} en {base_url}...")
                client = OpenAI(api_key=api_key, base_url=base_url)
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=8192,
                    timeout=5  # Timeout rápido para gateway local si no está activo
                )
                result = resp.choices[0].message.content
                if result:
                    result = result.strip()
                    is_ok = bool(result and (len(result) > 400 if model_type == "reasoning" else len(result) > 1))
                    if is_ok:
                        logger.info(f"[OMNIROUTE] [SUCCESS] Modelo {model} respondió con éxito ({len(result.split())} palabras).")
                        return result
                    else:
                        logger.warning(f"[OMNIROUTE] Modelo {model} devolvió texto insuficiente.")
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)[:150]
                logger.warning(f"[OMNIROUTE] {model} en {base_url} → {error_type}: {error_msg}. Saltando al siguiente fallback...")
                continue

        return None
    
    @staticmethod
    def call_capa_cero(prompt, system_prompt, model_type="reasoning", temperature=0.7):
        """
        Implementación de la Capa Cero (Zero Cost Tiers) con GitHub Models.
        Doble Bucle: Tokens (Prioridad PRO -> FREE) x Top 3 Modelos.
        """
        token_pro = os.getenv("MODELS_TOKEN_CEU")
        token_free = os.getenv("TOKEN_MODELS")
        base_url = "https://models.github.ai/inference"
        
        # Tokens y Nombres de Cuenta en Orden de Prioridad
        tokens = []
        if token_pro:
            tokens.append(("TIER 0-PRO (STUDENT)", token_pro))
        if token_free:
            tokens.append(("TIER 0-FREE (JOSEAQ)", token_free))
            
        if not tokens:
            print("   [Debug] No se encontraron tokens de GitHub Models configurados.")
            return None
            
        # Top Modelos de GitHub Models a iterar (Prioridad: Mini para maximizar cuota y ahorrar 429s)
        github_models = [
            "gpt-4o-mini",
            "gpt-4.1-mini",
            "gpt-4o"
        ]
        
        # Bucle 1: Iterar sobre las Cuentas (Tokens)
        for token_name, token_value in tokens:
            print(f"   [GITHUB] Cambiando a la cuenta: {token_name}...")
            
            client = OpenAI(api_key=token_value, base_url=base_url)
            
            # Bucle 2: Iterar sobre los Top Modelos
            for current_model in github_models:
                print(f"      [GITHUB] [{token_name}] Intentando con modelo: {current_model}...")
                
                max_retries = 2
                model_success = False
                
                for attempt in range(max_retries + 1):
                    try:
                        full_content = ""
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                        
                        # --- LOOP DE CONTINUIDAD (Anti-Truncamiento) ---
                        for jump in range(3): # Permitimos hasta 2 continuaciones
                            resp = client.chat.completions.create(
                                model=current_model,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=8192,
                                timeout=180
                            )
                            
                            chunk = resp.choices[0].message.content
                            full_content += chunk
                            finish_reason = getattr(resp.choices[0], 'finish_reason', 'stop')
                            
                            if finish_reason == "length":
                                print(f"      ⚠️ [TRUNCATED] {current_model} alcanzó el límite. Solicitando continuación (Salto {jump+1})...")
                                messages.append({"role": "assistant", "content": chunk})
                                messages.append({"role": "user", "content": "CONTINUE the text exactly where you left off. Do not repeat headers. Just continue the prose."})
                                continue
                            else:
                                break
                        
                        result = full_content.strip()
                        
                        # Validación de calidad estricta
                        if model_type == "reasoning":
                            is_ok = bool(result and len(result) > 400) # Subimos el listón
                        else:
                            is_ok = bool(result and len(result) > 1)
                            
                        if is_ok:
                            word_count = len(result.split())
                            print(f"      [SUCCESS] Modelo {current_model} respondió con éxito ({word_count} palabras).")
                            return result
                        else:
                            print(f"      [WARNING] Modelo {current_model} devolvió texto insuficiente. Intentando siguiente modelo...")
                            time.sleep(2)
                            break
                            
                    except Exception as e:
                        # Extract HTTP status code if available
                        status_code = getattr(e, 'status_code', None)
                        error_type = type(e).__name__
                        error_msg = str(e)[:200]
                        
                        if status_code == 429 or "ConnectionError" in error_type or "APIConnectionError" in error_type:
                            logger.warning(f"[CAPA-CERO] {token_name} / {current_model} → {error_type} (429/CONEXIÓN) [Intento {attempt+1}/{max_retries+1}].")
                            if attempt < max_retries:
                                time.sleep(2 * (attempt + 1))
                                continue
                            else:
                                logger.warning(f"[CAPA-CERO] {token_name} / {current_model} agotó reintentos. Saltando al siguiente token/modelo...")
                                break
                        
                        elif status_code and status_code >= 500:
                            logger.error(f"[CAPA-CERO] {token_name} / {current_model} → {status_code} SERVER ERROR.")
                            time.sleep(5)
                        else:
                            logger.warning(f"[CAPA-CERO] {token_name} / {current_model} → {error_type}: {error_msg}")
                            time.sleep(5)
                        
                        break
        
        return None

    @staticmethod
    def route_call(prompt, system_prompt, fallback_func, model_type="reasoning", temperature=0.7):
        """
        Enrutador inteligente: OmniRoute (AI Gateway Local) -> Capa Cero (GitHub) -> Fallback (API Original).
        """
        # --- CAPA 0 (OmniRoute AI Gateway Local Primario) ---
        try:
            omni_res = LLMRouter.call_omniroute(prompt, system_prompt, model_type, temperature)
            if omni_res:
                return omni_res
        except Exception as e:
            logger.warning(f"[ROUTE] OmniRoute no disponible ({e}). Escalando a Capa Cero...")

        # --- CAPA CERO (GitHub Models) ---
        res = LLMRouter.call_capa_cero(prompt, system_prompt, model_type, temperature)
        if res:
            return res
        
        # --- CAPA 1 (Fallback — API Original o Cascada) ---
        logger.warning(f"[ROUTE] Capa Cero AGOTADA (429 o fallos). Escalando a FALLBACK ({model_type})...")
        try:
            fallback_res = fallback_func(prompt, system_prompt)
            if fallback_res:
                logger.info(f"[ROUTE] Fallback respondió con éxito ({len(fallback_res)} chars).")
            else:
                logger.error(f"[ROUTE] Fallback devolvió None.")
            return fallback_res
        except Exception as e:
            logger.critical(f"[ROUTE] Fallo CRÍTICO en Fallback: {type(e).__name__}: {e}")
            return None
