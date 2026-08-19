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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for d in [os.path.join(ROOT_DIR, "core"), os.path.join(ROOT_DIR, "scripts")]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Importar Módulos Propios
import researcher
import trend_hunter
from niche_registry import NICHES

COMPLETED_FILE = 'data/completed.txt'

import orchestrator

SECTION_ALIASES = {
    "ia-saas": "ia",
    "ia_saas": "ia",
    "biohacking": "fitness",
    "creators": "youtube"
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', '--section', dest='section', type=str, required=True, help='Category/Section or tools')
    parser.add_argument('--scout-only', action='store_true', help='Ejecutar solo la fase Scout de tendencias')
    args = parser.parse_args()
    raw_cat = args.section.lower().strip()
    cat = SECTION_ALIASES.get(raw_cat, raw_cat)
    forced_lang = args.lang
    
    # --- MODO STANDARD ---
    if cat not in NICHES:
        print(f"❌ Categoría inválida.")
        return

    # --- MODO SCOUT ONLY ---
    if args.scout_only:
        import trend_scout
        scout_lang = forced_lang or "es"
        print(f"🔭 [Scout-Only] Ejecutando scouting para '{cat}' [{scout_lang.upper()}]")
        trend_scout.scout(cat, scout_lang)
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
    
    # --- FALLBACK: TrendScout / TrendHunter directo si no hay JSON en disco ---
    if not tema:
        print(f"   🔄 [Fallback Directo] Sin JSON previo en disco. Ejecutando Scout en vivo...")
        try:
            import trend_scout
            target_scout_lang = forced_lang or "es"
            trend_scout.scout(cat, target_scout_lang)
            if os.path.exists(trends_file):
                with open(trends_file, 'r', encoding='utf-8') as f:
                    fresh_data = json.load(f)
                for t in fresh_data.get("topics", []):
                    candidate = t.get("title", "")
                    if candidate and orchestrator.safety_check(candidate) and not orchestrator.is_topic_redundant(candidate, cat):
                        tema = candidate
                        if not tema_lang:
                            tema_lang = t.get("lang", target_scout_lang)
                        print(f"   ✅ [Fallback Scout] Tema seleccionado: {tema} [{tema_lang.upper()}]")
                        os.remove(trends_file)
                        break
        except Exception as e_scout:
            print(f"   ⚠️ [Fallback Scout Error] {e_scout}")

    if not tema:
        print(f"   🔄 [Fallback TrendHunter] Buscando tendencia en fuentes adicionales...")
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
            tema_lang = forced_lang or random.choice(["es", "en"])
            break
    
    if not tema:
        print(f"🚫 ABORTADO: No se encontró tema válido para '{cat}'.")
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
    orchestrator.guardar_post(meta, texto, tema_lang, cat, translation_key=trans_key, contexto=contexto)
        
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{cat}: {tema}\n")

    # ── AUTO-DEPLOY: Git Sync + Vercel Deploy Hook ──
    try:
        from deploy_notifier import trigger_production_deploy
        commit_msg = f"feat(content): {cat}/{tema_lang} — {meta.get('slug', 'new-article')} [auto-deploy]"
        deploy_result = trigger_production_deploy(
            commit_message=commit_msg,
            run_git=not os.environ.get("GITHUB_ACTIONS"),  # Skip git in CI (workflow handles git push)
            run_vercel=True
        )
        logging.info(f"[AUTO-DEPLOY] Resultado: {deploy_result}")
    except Exception as e:
        logging.warning(f"[AUTO-DEPLOY] No se pudo ejecutar el deploy automático: {e}")

if __name__ == "__main__":
    main()
