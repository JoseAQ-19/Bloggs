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
    Gestor Central de LLMs con Inyección de Capa Cero (GitHub Models) y Exponential Backoff.
    Misión: Priorizar el ahorro de costes y alta disponibilidad ante Rate Limits.
    """
    
    @staticmethod
    def call_capa_cero(prompt, system_prompt, model_type="reasoning"):
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
            
        # Top 3 Modelos de GitHub Models a iterar
        github_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "meta-llama-3.1-70b-instruct"
        ]
        
        # Bucle 1: Iterar sobre las Cuentas (Tokens)
        for token_name, token_value in tokens:
            print(f"   [GITHUB] Cambiando a la cuenta: {token_name}...")
            
            client = OpenAI(api_key=token_value, base_url=base_url)
            
            # Bucle 2: Iterar sobre los Top 3 Modelos
            for current_model in github_models:
                print(f"      [GITHUB] [{token_name}] Intentando con modelo: {current_model}...")
                
                try:
                    resp = client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=8192,
                        timeout=180
                    )
                    
                    result = resp.choices[0].message.content.strip()
                    
                    # Validación de calidad estricta
                    if model_type == "reasoning":
                        is_ok = bool(result and len(result) > 200)
                    else:
                        is_ok = bool(result and len(result) > 1)
                        
                    if is_ok:
                        print(f"      [SUCCESS] Modelo {current_model} respondió con éxito ({len(result.split())} palabras).")
                        return result
                    else:
                        print(f"      [WARNING] Modelo {current_model} devolvió texto muy corto o vacío. Intentando siguiente modelo...")
                        time.sleep(2) # Backoff ligero por si acaso
                        continue # Salta al siguiente modelo
                        
                except Exception as e:
                    # Extract HTTP status code if available (OpenAI SDK wraps it)
                    status_code = getattr(e, 'status_code', None)
                    error_type = type(e).__name__
                    error_msg = str(e)[:200]  # Truncate for readability
                    
                    if status_code == 429:
                        logger.warning(f"[CAPA-CERO] {token_name} / {current_model} → 429 RATE LIMITED. {error_msg}")
                        backoff = 10
                    elif status_code and status_code >= 500:
                        logger.error(f"[CAPA-CERO] {token_name} / {current_model} → {status_code} SERVER ERROR. {error_msg}")
                        backoff = 5
                    else:
                        logger.warning(f"[CAPA-CERO] {token_name} / {current_model} → {error_type}: {error_msg}")
                        backoff = 5
                    
                    time.sleep(backoff)
                    continue
                    
        # Si agota ambos bucles (Tokens x Modelos) y no hay éxito
        logger.error("[CAPA-CERO] EXHAUSTA: Todas las combinaciones de tokens x modelos fallaron. Cayendo a cascada original.")
        return None

    @staticmethod
    def route_call(prompt, system_prompt, original_cascada_func, model_type="reasoning"):
        """
        Orquestador Principal: Intenta Capa Cero -> Fallback a Cascada Original.
        """
        result = LLMRouter.call_capa_cero(prompt, system_prompt, model_type)
        if result:
            logger.info(f"[ROUTE] Capa Cero respondió con éxito ({model_type}). Sin coste.")
            return result
            
        # Fallback de Seguridad
        logger.warning(f"[ROUTE] Capa Cero agotada. Escalando a CASCADA ORIGINAL ({model_type})...")
        try:
            cascade_result = original_cascada_func(prompt, system_prompt)
            if cascade_result:
                logger.info(f"[ROUTE] Cascada Original respondió con éxito ({len(cascade_result)} chars).")
            else:
                logger.error(f"[ROUTE] Cascada Original devolvió None. Sin respuesta disponible.")
            return cascade_result
        except Exception as e:
            logger.critical(f"[ROUTE] Fallo TOTAL en Cascada Original: {type(e).__name__}: {e}")
            return None
