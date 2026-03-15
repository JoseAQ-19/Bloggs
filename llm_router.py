import os
import time
import logging
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

class LLMRouter:
    """
    Gestor Central de LLMs con Inyección de Capa Cero (GitHub Models) y Exponential Backoff.
    Misión: Priorizar el ahorro de costes y alta disponibilidad ante Rate Limits.
    """
    
    @staticmethod
    def call_capa_cero(prompt, system_prompt, model_type="reasoning"):
        """
        Implementación de la Capa Cero (Zero Cost Tiers).
        Intento 1: MODELS_TOKEN_CEU (Prioridad 1 - Límites Pro)
        Intento 2: TOKEN_MODELS (Prioridad 2 - Fallback Estándar)
        """
        token1 = os.getenv("MODELS_TOKEN_CEU")
        token2 = os.getenv("TOKEN_MODELS")
        base_url = "https://models.inference.ai.azure.com"
        
        # Enrutamiento Inteligente: 
        # Tareas de razonamiento/corrección -> GPT-4o
        # Tareas de parseo/formateo -> GPT-4o-mini
        if model_type == "reasoning":
            model = "gpt-4o"
        else:
            model = "gpt-4o-mini"
            
        attempts = [
            ("TIER 0-A (GITHUB-CEU)", token1),
            ("TIER 0-B (GITHUB-STD)", token2)
        ]
        
        if token1: print(f"   [Debug] Token 1 detectado: {len(token1)} chars")
        if token2: print(f"   [Debug] Token 2 detectado: {len(token2)} chars")
        
        for name, token in attempts:
            if not token or len(token) < 10:
                print(f"   [Debug] Token para {name} inválido o vacío.")
                continue
                
            try:
                print(f"   [GITHUB] [{name}] Intentando {model} en GitHub Models...")
                
                # Función decorada con Backoff (Tenacity) para reintentar solo excepciones OpenAI
                @retry(wait=wait_exponential(multiplier=2, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
                def _do_request():
                    client = OpenAI(api_key=token, base_url=base_url)
                    return client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4096,
                        timeout=180
                    )
                
                resp = _do_request()
                result = resp.choices[0].message.content.strip()
                # Validación dinámica de éxito:
                # - razonamiento/redacción: requiere longitud (>200 chars)
                # - parsing/research_outline: aceptamos lo que venga si no es nulo
                is_ok = False
                if model_type == "reasoning":
                    is_ok = bool(result and len(result) > 200)
                else:
                    is_ok = bool(result and len(result) > 1)

                if is_ok:
                    print(f"   [SUCCESS] {name} respondió con éxito ({len(result.split())} palabras).")
                    return result
                else:
                    print(f"   [WARNING] [{name}] Respuesta demasiado corta o vacía.")
            except Exception as e:
                error_str = str(e)
                print(f"   [ERROR] [{name}] Error: {error_str}")
        
        return None

    @staticmethod
    def route_call(prompt, system_prompt, original_cascada_func, model_type="reasoning"):
        """
        Orquestador Principal: Intenta Capa Cero -> Fallback a Cascada Original.
        """
        result = LLMRouter.call_capa_cero(prompt, system_prompt, model_type)
        if result:
            return result
            
        # Fallback de Seguridad
        print(f"   [FALLBACK] [Capa Cero] Agotada o en error. Saltando a la CASCADA ORIGINAL...")
        try:
            return original_cascada_func(prompt, system_prompt)
        except Exception as e:
            logging.error(f"❌ Fallo crítico en Cascada Original: {e}")
            return None
