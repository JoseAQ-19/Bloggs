import os
import sys
import json
import random
import argparse
import logging
import hashlib
from dotenv import load_dotenv

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Cargar variables de entorno (Prioridad .env)
load_dotenv()

# Importar Módulos Propios
import researcher
import trend_hunter 
from niche_registry import NICHES

COMPLETED_FILE = 'data/completed.txt'

import orchestrator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True, help='Category or tools')
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None, help='Force language: es (Spain) or en (US)')
    args = parser.parse_args()
    cat = args.category.lower()
    forced_lang = args.lang
    
    # --- MODO STANDARD ---
    if cat not in NICHES:
        print(f"❌ Categoría inválida.")
        return

    print(f"🚀 INICIANDO PENTAGON: {NICHES[cat]['name']}")
    
    # --- RELAY-RACE V2: Leer temas pre-investigados del Scout ---
    # Buscar primero el JSON con sufijo de idioma (nuevo), luego sin sufijo (viejo)
    tema = None
    tema_lang = forced_lang  # Si viene de CLI, ya sabemos el idioma
    
    if forced_lang:
        trends_file = f"data/trends_{cat}_{forced_lang}.json"
    else:
        trends_file = f"data/trends_{cat}.json"
    
    # Fallback: si no existe el archivo con sufijo, probar sin sufijo
    if not os.path.exists(trends_file) and forced_lang:
        fallback_file = f"data/trends_{cat}.json"
        if os.path.exists(fallback_file):
            trends_file = fallback_file
            print(f"   🔄 [Relay-Race] Fichero con sufijo no encontrado, usando fallback: {trends_file}")
    
    if os.path.exists(trends_file):
        print(f"   📂 [Relay-Race] Leyendo temas pre-investigados: {trends_file}")
        try:
            with open(trends_file, 'r', encoding='utf-8') as f:
                trends_data = json.load(f)
            
            topics = trends_data.get("topics", [])
            scouted_at = trends_data.get("scouted_at", "")
            json_lang = trends_data.get("lang", None)
            print(f"   📋 {len(topics)} temas disponibles (scouted: {scouted_at[:19]}, lang: {json_lang})")
            
            # Buscar el primer tema que pase safety check y no sea redundante
            for t in topics:
                candidate = t.get("title", "")
                if not candidate:
                    continue
                if not orchestrator.safety_check(candidate):
                    print(f"   ⚠️ Tema '{candidate}' falló safety check. Saltando...")
                    continue
                if orchestrator.is_topic_redundant(candidate, cat):
                    print(f"   🔄 Tema '{candidate}' es redundante. Saltando...")
                    continue
                tema = candidate
                # El idioma viene del CLI o del JSON del topic
                if not tema_lang:
                    tema_lang = t.get("lang", json_lang or "es")
                print(f"   ✅ [Relay-Race] Tema seleccionado: {tema} [{tema_lang.upper()}]")
                break
            
            # Limpiar el JSON después de leer (evitar reusar temas viejos)
            if tema:
                os.remove(trends_file)
                print(f"   🗑️ [Relay-Race] {trends_file} consumido y eliminado")
                
        except Exception as e:
            print(f"   ⚠️ [Relay-Race] Error leyendo {trends_file}: {e}. Cayendo a TrendHunter...")
    
    # --- FALLBACK: TrendHunter clásico si no hay JSON o no hay temas válidos ---
    if not tema:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print("🛑 [Relay-Race] Ejecución en GitHub Actions: no hay JSON válido. Terminando paso con 0 para evitar errores en falso.")
            sys.exit(0)
            
        print(f"   🔄 [Fallback] Usando TrendHunter clásico...")
        for topic_attempt in range(5):
            candidate = trend_hunter.TrendHunter.get_trend(cat)
            if not candidate:
                print(f"   ⚠️ [Intento {topic_attempt+1}/5] TrendHunter no devolvió tema. Reintentando...")
                continue
            if not orchestrator.safety_check(candidate):
                print(f"   ⚠️ [Intento {topic_attempt+1}/5] Tema '{candidate}' falló safety check. Reintentando...")
                continue
            if orchestrator.is_topic_redundant(candidate, cat):
                print(f"   🔄 [Intento {topic_attempt+1}/5] Tema '{candidate}' es redundante. Reintentando...")
                continue
            tema = candidate
            tema_lang = random.choice(["es", "en"])
            break
    
    if not tema:
        print(f"🚫 ABORTADO: No se encontró tema válido para '{cat}'.")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            sys.exit(0)
        return
    
    print(f"🎯 TEMA: {tema} | IDIOMA ORIGEN: {tema_lang.upper()}")
    res = researcher.Researcher()
    
    # === HREFLANG DETERMINISTA (Bilingüismo Desacoplado) ===
    # En lugar de generar un UUID aleatorio que rompe el enlazado en Hugo cuando corren 2 actions distintos,
    # generamos un hash MD5 predictivo basado en el titulo bruto del tema.
    # Así, writer-ia-en y writer-ia-es generarán la misma llave si cogen el mismo trend del JSON.
    import hashlib
    clean_topic_hash = tema.strip().lower()
    t_hash = hashlib.md5(clean_topic_hash.encode('utf-8')).hexdigest()
    trans_key = f"{t_hash[:8]}-{t_hash[8:12]}-{t_hash[12:16]}-{t_hash[16:20]}-{t_hash[20:]}"
    print(f"   🔑 [Hugo Hreflang] Translation Key (Determinista): {trans_key}")
    
    # === AISLAMIENTO: Variables limpias por idioma ===
    meta = None
    texto = None
    contexto = None
    
    print(f"   🌐 [Relay-Race] Ejecutando tubería nativa SOLO para audiencia: {tema_lang.upper()}")
    
    # V5 GEO-RESEARCH: Investigar Específicamente por Idioma Autóctono
    contexto = res.research_topic(
        topic=tema,
        category=cat,
        search_context=NICHES[cat].get('search_context', ''),
        lang=tema_lang
    )
    
    meta = orchestrator.planificar_articulo(tema, contexto, tema_lang, NICHES[cat])
    
    # ── LINK DEPOSIT: Guardar fuentes para el Corrector ──
    if contexto and isinstance(contexto, dict) and "sources" in contexto:
        orchestrator.guardar_fuentes(meta['slug'], contexto["sources"], lang=tema_lang)
        
    texto = orchestrator.escribir_articulo(meta, contexto, tema_lang, NICHES[cat], category=cat)
    orchestrator.guardar_post(meta, texto, tema_lang, cat, translation_key=trans_key)
        
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
