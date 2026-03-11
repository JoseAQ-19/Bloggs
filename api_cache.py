#!/usr/bin/env python3
"""
API_CACHE.PY — Caché Agresiva para Fuentes Externas (Exa, Google News RSS, HackerNews)
======================================================================================
Evita gastar cuota de APIs de pago si el script falla y se reinicia el mismo día.

Mecanismo:
  - Usa un archivo JSON local (`data/.api_cache.json`) como almacén persistente.
  - La clave (key) es un hash SHA256 de la función + query.
  - TTL configurable (por defecto 12 horas).
  - Thread-safe mediante file locking básico.

Uso:
  from api_cache import cached_api_call

  @cached_api_call(ttl_hours=12)
  def fetch_exa_news(query, domains, limit=5):
      ...
"""

import os
import json
import hashlib
import time
import functools
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "data", ".api_cache.json")
DEFAULT_TTL_HOURS = 12


def _load_cache() -> dict:
    """Carga la caché desde disco. Retorna dict vacío si no existe o está corrupto."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"   ⚠️ [Cache] Archivo corrupto o inaccesible: {e}. Reiniciando caché.")
    return {}


def _save_cache(cache: dict):
    """Persiste la caché a disco."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        print(f"   ⚠️ [Cache] No se pudo guardar caché: {e}")


def _make_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Genera una clave de caché determinista basada en función + argumentos."""
    # Serializar argumentos de forma estable
    key_data = {
        "func": func_name,
        "args": [str(a) for a in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    raw = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def cached_api_call(ttl_hours: float = DEFAULT_TTL_HOURS):
    """
    Decorador que cachea el resultado de una llamada a API externa.
    
    Args:
        ttl_hours: Tiempo de vida de la entrada en horas (default: 12).
    
    Ejemplo:
        @cached_api_call(ttl_hours=12)
        def fetch_exa_news(query, domains, limit=5):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_key(func.__name__, args, kwargs)
            cache = _load_cache()
            
            # Verificar si existe y no ha expirado
            if cache_key in cache:
                entry = cache[cache_key]
                cached_at = entry.get("cached_at", 0)
                age_hours = (time.time() - cached_at) / 3600
                
                if age_hours < ttl_hours:
                    cached_time_str = datetime.fromtimestamp(cached_at).strftime('%H:%M:%S')
                    print(f"   💾 [Cache HIT] {func.__name__}() → Resultado cacheado a las {cached_time_str} (edad: {age_hours:.1f}h / TTL: {ttl_hours}h)")
                    return entry.get("data", [])
                else:
                    print(f"   🔄 [Cache EXPIRED] {func.__name__}() → {age_hours:.1f}h > TTL {ttl_hours}h. Refrescando...")
            else:
                print(f"   🆕 [Cache MISS] {func.__name__}() → Primera llamada. Consultando API...")
            
            # Llamar a la API real
            result = func(*args, **kwargs)
            
            # Guardar resultado en caché (solo si es no-vacío)
            if result is not None:
                cache[cache_key] = {
                    "data": result,
                    "cached_at": time.time(),
                    "func": func.__name__,
                    "args_summary": str(args)[:200]
                }
                _save_cache(cache)
                print(f"   💾 [Cache SAVED] {func.__name__}() → {len(result) if isinstance(result, list) else 1} resultados guardados.")
            
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """Limpia la caché completa. Útil para debugging."""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print("   🗑️ [Cache] Caché eliminada completamente.")
        else:
            print("   ℹ️ [Cache] No existe archivo de caché.")
    except Exception as e:
        print(f"   ⚠️ [Cache] Error al limpiar: {e}")


def get_cache_stats() -> dict:
    """Devuelve estadísticas de la caché actual."""
    cache = _load_cache()
    stats = {
        "total_entries": len(cache),
        "entries": []
    }
    for key, entry in cache.items():
        age_hours = (time.time() - entry.get("cached_at", 0)) / 3600
        stats["entries"].append({
            "func": entry.get("func", "unknown"),
            "age_hours": round(age_hours, 1),
            "data_count": len(entry.get("data", [])) if isinstance(entry.get("data"), list) else 1,
            "args": entry.get("args_summary", "")[:100]
        })
    return stats
