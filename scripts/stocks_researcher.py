#!/usr/bin/env python3
"""
STOCKS_RESEARCHER.PY — Análisis de Competidores para Fondos de Inversión
=========================================================================
Extrae estilos de escritura, frases comunes y detecta disclaimers
de los principales portales financieros en ES y EN.

REGLA DE ORO: Este archivo NO importa ni modifica NADA del núcleo existente.
Usa requests + BeautifulSoup de forma aislada.
"""

import os
import re
import json
import time
import logging
import requests
import sys
from datetime import datetime, timedelta

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logging.warning("BeautifulSoup no instalado. pip install beautifulsoup4")

from stocks_instructions import COMPETITORS

# Configurar stdout/stderr para UTF-8 en Windows y evitar errores de "charmap"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Configuración
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"
}
TIMEOUT = 15


# ============================================================
# UTILIDADES DE SCRAPING LIGERO
# ============================================================

def _safe_get(url, timeout=TIMEOUT):
    """GET robusto con manejo de errores y rate-limiting educado."""
    try:
        time.sleep(1)  # Rate-limiting: mínimo 1s entre requests
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 403:
            logging.warning(f"   ⚠️ 403 Forbidden: {url} (probablemente WAF/bot protection)")
            return None
        elif resp.status_code == 429:
            logging.warning(f"   ⚠️ 429 Rate Limited: {url}")
            return None
        else:
            logging.warning(f"   ⚠️ HTTP {resp.status_code}: {url}")
            return None
    except requests.exceptions.Timeout:
        logging.warning(f"   ⚠️ Timeout ({timeout}s): {url}")
        return None
    except requests.exceptions.ConnectionError:
        logging.warning(f"   ⚠️ Connection Error: {url}")
        return None
    except Exception as e:
        logging.warning(f"   ⚠️ Error inesperado: {url} — {e}")
        return None


def _extract_text_blocks(html, max_blocks=20):
    """Extrae bloques de texto significativos de una página HTML."""
    if not html or not BeautifulSoup:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Eliminar scripts, styles, nav, footer
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()
    
    blocks = []
    for p in soup.find_all(['p', 'li', 'h2', 'h3', 'blockquote']):
        text = p.get_text(strip=True)
        if len(text) > 40:  # Filtrar fragmentos triviales
            blocks.append(text)
            if len(blocks) >= max_blocks:
                break
    
    return blocks


def _detect_disclaimers(text_blocks):
    """Detecta presencia de disclaimers financieros en el contenido."""
    disclaimer_keywords = [
        "disclaimer", "aviso legal", "no constituye", "asesoramiento",
        "past performance", "risk", "prospectus", "folleto informativo",
        "inversión conlleva riesgo", "investment advice", "not constitute",
        "riesgo de pérdida", "loss of capital", "rendimientos pasados"
    ]
    
    found = []
    for block in text_blocks:
        lower = block.lower()
        for kw in disclaimer_keywords:
            if kw in lower:
                found.append({
                    "keyword": kw,
                    "context": block[:200]
                })
                break
    
    return found


def _extract_common_phrases(text_blocks, min_freq=2):
    """Extrae frases y patrones de escritura recurrentes."""
    # Extraer bigrams y trigrams
    all_words = []
    for block in text_blocks:
        words = re.findall(r'\b[a-záéíóúñü]{3,}\b', block.lower())
        all_words.extend(words)
    
    # Bigrams
    bigrams = {}
    for i in range(len(all_words) - 1):
        bg = f"{all_words[i]} {all_words[i+1]}"
        bigrams[bg] = bigrams.get(bg, 0) + 1
    
    # Filtrar los más frecuentes
    common = {k: v for k, v in sorted(bigrams.items(), key=lambda x: -x[1]) 
              if v >= min_freq}
    
    return dict(list(common.items())[:20])  # Top 20


# ============================================================
# ANÁLISIS DE COMPETIDORES — ESPAÑA
# ============================================================

def analyze_stock_competitors_spain():
    """
    Analiza los competidores financieros españoles:
    - morningstar.es
    - bestinver.com
    - carmignac.es
    - vanguardinvestor.es
    
    Returns:
        dict con análisis de estilo, frases comunes y disclaimers detectados.
    """
    print("\n🇪🇸 [Stocks Researcher] Analizando competidores ESPAÑA...")
    
    competitors_es = COMPETITORS.get("es", {})
    results = {
        "lang": "es",
        "analyzed_at": datetime.now().isoformat(),
        "competitors": {}
    }
    
    # URLs de artículos/páginas representativas para analizar
    target_pages = {
        "morningstar_es": [
            "https://www.morningstar.es/es/news/latest.aspx",
        ],
        "bestinver": [
            "https://www.bestinver.es/blog/",
        ],
        "carmignac_es": [
            "https://www.carmignac.es/es_ES/analisis-de-mercado",
        ],
        "vanguard_es": [
            "https://www.es.vanguard/content/institucional/es/es/insights.html",
        ]
    }
    
    for comp_id, comp_info in competitors_es.items():
        print(f"   📊 Analizando: {comp_info['name']}...")
        
        all_blocks = []
        pages_scraped = 0
        
        urls = target_pages.get(comp_id, [comp_info["url"]])
        for url in urls:
            html = _safe_get(url)
            if html:
                blocks = _extract_text_blocks(html)
                all_blocks.extend(blocks)
                pages_scraped += 1
                print(f"      ✅ {len(blocks)} bloques extraídos de {url}")
            else:
                print(f"      ⚠️ No se pudo acceder a {url}")
        
        # Análisis del contenido extraído
        disclaimers = _detect_disclaimers(all_blocks)
        phrases = _extract_common_phrases(all_blocks) if all_blocks else {}
        
        results["competitors"][comp_id] = {
            "name": comp_info["name"],
            "url": comp_info["url"],
            "declared_style": comp_info["style"],
            "pages_scraped": pages_scraped,
            "text_blocks_extracted": len(all_blocks),
            "sample_texts": all_blocks[:5],  # 5 muestras representativas
            "disclaimers_detected": disclaimers,
            "common_phrases": phrases,
            "has_disclaimer": len(disclaimers) > 0
        }
    
    successful = sum(1 for c in results["competitors"].values() if c["pages_scraped"] > 0)
    print(f"\n   📈 [ES] Análisis completado: {successful}/{len(competitors_es)} competidores accesibles")
    
    return results


# ============================================================
# ANÁLISIS DE COMPETIDORES — USA / GLOBAL
# ============================================================

def analyze_stock_competitors_us():
    """
    Analiza los competidores financieros anglosajones:
    - morningstar.com
    - fidelity.com
    - vanguard.com
    - blackrock.com
    
    Returns:
        dict con análisis de estilo, frases comunes y disclaimers detectados.
    """
    print("\n🇺🇸 [Stocks Researcher] Analizando competidores USA/GLOBAL...")
    
    competitors_en = COMPETITORS.get("en", {})
    results = {
        "lang": "en",
        "analyzed_at": datetime.now().isoformat(),
        "competitors": {}
    }
    
    target_pages = {
        "morningstar_com": [
            "https://www.morningstar.com/funds",
        ],
        "fidelity": [
            "https://www.fidelity.com/viewpoints/investing-ideas",
        ],
        "vanguard_com": [
            "https://investor.vanguard.com/insights",
        ],
        "blackrock": [
            "https://www.blackrock.com/us/individual/insights",
        ]
    }
    
    for comp_id, comp_info in competitors_en.items():
        print(f"   📊 Analyzing: {comp_info['name']}...")
        
        all_blocks = []
        pages_scraped = 0
        
        urls = target_pages.get(comp_id, [comp_info["url"]])
        for url in urls:
            html = _safe_get(url)
            if html:
                blocks = _extract_text_blocks(html)
                all_blocks.extend(blocks)
                pages_scraped += 1
                print(f"      ✅ {len(blocks)} blocks extracted from {url}")
            else:
                print(f"      ⚠️ Could not access {url}")
        
        disclaimers = _detect_disclaimers(all_blocks)
        phrases = _extract_common_phrases(all_blocks) if all_blocks else {}
        
        results["competitors"][comp_id] = {
            "name": comp_info["name"],
            "url": comp_info["url"],
            "declared_style": comp_info["style"],
            "pages_scraped": pages_scraped,
            "text_blocks_extracted": len(all_blocks),
            "sample_texts": all_blocks[:5],
            "disclaimers_detected": disclaimers,
            "common_phrases": phrases,
            "has_disclaimer": len(disclaimers) > 0
        }
    
    successful = sum(1 for c in results["competitors"].values() if c["pages_scraped"] > 0)
    print(f"\n   📈 [EN] Analysis complete: {successful}/{len(competitors_en)} competitors accessible")
    
    return results


# ============================================================
# ANÁLISIS COMBINADO
# ============================================================

def analyze_all_competitors():
    """Ejecuta análisis de competidores en ambos mercados."""
    print("\n" + "=" * 60)
    print("🔬 STOCKS RESEARCHER — Análisis de Competidores Completo")
    print("=" * 60)
    
    es_results = analyze_stock_competitors_spain()
    en_results = analyze_stock_competitors_us()
    
    combined = {
        "analyzed_at": datetime.now().isoformat(),
        "markets": {
            "es": es_results,
            "en": en_results
        },
        "summary": {
            "total_competitors": len(es_results["competitors"]) + len(en_results["competitors"]),
            "es_with_disclaimers": sum(1 for c in es_results["competitors"].values() if c["has_disclaimer"]),
            "en_with_disclaimers": sum(1 for c in en_results["competitors"].values() if c["has_disclaimer"]),
        }
    }
    
    # Guardar cache del análisis
    os.makedirs("data", exist_ok=True)
    cache_path = "data/stocks_competitors_analysis.json"
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\n   💾 Análisis guardado en: {cache_path}")
    
    return combined


def get_cached_analysis():
    """Lee el análisis cacheado si existe y tiene menos de 24h."""
    cache_path = "data/stocks_competitors_analysis.json"
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analyzed_at = datetime.fromisoformat(data.get("analyzed_at", "2000-01-01"))
        if datetime.now() - analyzed_at > timedelta(hours=24):
            logging.info("   ♻️ Cache de análisis expirado (>24h). Re-analizando...")
            return None
        
        logging.info(f"   📦 Usando análisis cacheado ({analyzed_at.strftime('%Y-%m-%d %H:%M')})")
        return data
    except Exception:
        return None


# ============================================================
# MAIN (ejecución independiente para testing)
# ============================================================

if __name__ == "__main__":
    results = analyze_all_competitors()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL ANÁLISIS")
    print("=" * 60)
    
    for market, data in results["markets"].items():
        print(f"\n  🌍 Mercado: {market.upper()}")
        for comp_id, comp_data in data["competitors"].items():
            status = "✅" if comp_data["pages_scraped"] > 0 else "❌"
            disclaimer = "🛡️" if comp_data["has_disclaimer"] else "⚠️ Sin disclaimer"
            print(f"    {status} {comp_data['name']}: "
                  f"{comp_data['text_blocks_extracted']} bloques | {disclaimer}")
