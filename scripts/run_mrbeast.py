#!/usr/bin/env python3
"""
scripts/run_mrbeast.py - Newsjacking Ejecutor para MrBeast Abril 2026

Ejecuta la generación de un artículo viral usando el research pre-cargado
en data/mrbeast_scout.txt sin necesidad de TrendHunter.

USO:
    python scripts/run_mrbeast.py

El artículo se guardará en: content/es/youtube/
"""

import os
import sys
import hashlib

# Configurar paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from niche_registry import NICHES
import orchestrator

# Configuración del Newsjacking
CATEGORY = "youtube"
LANG = "es"
TOPIC = "La última baza de MrBeast: Por qué ha tenido que recurrir a tus streamers favoritos tras la caída del 50% de sus visitas"
SCOUT_FILE = "data/mrbeast_scout.txt"


def main():
    print("=" * 70)
    print("🚀 NEWSJACKING: MRBEAST - Abril 2026")
    print("=" * 70)

    # Verificar que existe el archivo scout
    if not os.path.exists(SCOUT_FILE):
        print(f"❌ ERROR: No existe {SCOUT_FILE}")
        print("   Ejecuta primero la investigación o crea el archivo manualmente.")
        sys.exit(1)

    # Leer el contenido del scout
    print(f"📂 Cargando research desde: {SCOUT_FILE}")
    with open(SCOUT_FILE, 'r', encoding='utf-8') as f:
        scout_content = f.read()

    print(f"   📄 Research cargado: {len(scout_content)} caracteres")

    # Preparar el contexto como si viniera del researcher
    contexto = {
        'content': scout_content,
        'layer': 'scout_newsjacking',
        'sources': [
            'https://blog.youtube/news-and-events/mrbeast-streamer-challenge-one-million-dollars/',
            'https://www.dexerto.com/youtube/mrbeast-pits-50-streamers-against-each-other-with-final-four-competing-for-1m-live-3346619/',
            'https://www.fastcompany.com/91211168/mrbeasts-youtube-dominance-takes-a-dip',
            'https://www.svg.com/1644886/mrbeast-viewership-rapidly-dropping-amid-scandals/',
            'https://www.statista.com/statistics/1346129/mrbeast-video-view-numbers',
            'https://win.gg/roster-mrbeast-50-streamer-event/',
        ]
    }

    print(f"🎯 TEMA: {TOPIC}")
    print(f"🌐 IDIOMA: {LANG.upper()}")
    print(f"📁 CATEGORÍA: {CATEGORY}")
    print()

    # Generar translation key determinista
    clean_hash = TOPIC.strip().lower()
    t_hash = hashlib.md5(clean_hash.encode('utf-8')).hexdigest()
    trans_key = f"{t_hash[:8]}-{t_hash[8:12]}-{t_hash[12:16]}-{t_hash[16:20]}-{t_hash[20:]}"
    print(f"🔑 [Hreflang] Translation Key: {trans_key}")

    # FASE 1: Planificar artículo
    print("\n📋 FASE 1: Planificación del artículo...")
    category_config = NICHES[CATEGORY]
    meta = orchestrator.planificar_articulo(TOPIC, contexto, LANG, category_config)

    if not meta or 'slug' not in meta:
        print("❌ ERROR: Falló la planificación del artículo")
        sys.exit(1)

    print(f"   ✅ Título planificado: {meta['titulo']}")
    print(f"   ✅ Slug: {meta['slug']}")

    # Guardar fuentes para el corrector
    print("   📝 Guardando fuentes en Link Deposit...")
    orchestrator.guardar_fuentes(meta['slug'], contexto["sources"], lang=LANG)

    # FASE 2: Escribir artículo
    print("\n✍️  FASE 2: Generación del contenido (esto puede tomar 2-3 minutos)...")
    texto = orchestrator.escribir_articulo(
        meta,
        contexto,
        LANG,
        category_config,
        category=CATEGORY
    )

    if not texto or len(texto) < 500:
        print("❌ ERROR: El artículo generado es demasiado corto o falló")
        sys.exit(1)

    word_count = len(texto.split())
    print(f"   ✅ Artículo generado: {word_count} palabras")

    # FASE 3: Guardar
    print("\n💾 FASE 3: Guardando artículo...")
    orchestrator.guardar_post(
        meta,
        texto,
        LANG,
        CATEGORY,
        translation_key=trans_key
    )

    # Registrar como completado
    COMPLETED_FILE = 'data/completed.txt'
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{CATEGORY}: {TOPIC}\n")

    # Resumen final
    print("\n" + "=" * 70)
    print("✅ NEWSJACKING COMPLETADO")
    print("=" * 70)
    print(f"📄 Archivo: content/{LANG}/{CATEGORY}/{meta['slug']}.md")
    print(f"📝 Título: {meta['titulo']}")
    print(f"🔤 Palabras: {word_count}")
    print(f"🔑 Translation Key: {trans_key}")
    print()
    print("💡 Próximos pasos:")
    print("   1. Revisa el artículo: git diff content/")
    print("   2. Commit: git add content/ && git commit -m '...'")
    print("   3. Push: git push origin main")
    print("=" * 70)


if __name__ == "__main__":
    main()
