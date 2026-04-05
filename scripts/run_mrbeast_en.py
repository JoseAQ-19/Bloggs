#!/usr/bin/env python3
"""
scripts/run_mrbeast_en.py - Newsjacking executor for MrBeast April 2026 (EN)

Runs the generation of a Tier 1 (US) viral article
using the pre-loaded research in data/mrbeast_scout_en.txt,
without needing TrendHunter.

USAGE:
    python scripts/run_mrbeast_en.py

The article will be saved under: content/en/youtube/
"""

import os
import sys
import hashlib

# Configure paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from niche_registry import NICHES
import orchestrator

# Newsjacking configuration
CATEGORY = "youtube"
LANG = "en"
TOPIC = (
    "MrBeast's $1,000,000 Streamer Showdown: Did xQc and Twitch Just Save "
    "His YouTube Empire?"
)
SCOUT_FILE = "data/mrbeast_scout_en.txt"


def main():
    print("=" * 70)
    print("🚀 NEWSJACKING: MRBEAST - April 2026 (EN / Tier 1)")
    print("=" * 70)

    # Check scout file exists
    if not os.path.exists(SCOUT_FILE):
        print(f"❌ ERROR: Missing {SCOUT_FILE}")
        print("   Run research first or create the file manually.")
        sys.exit(1)

    # Read scout content
    print(f"📂 Loading research from: {SCOUT_FILE}")
    with open(SCOUT_FILE, "r", encoding="utf-8") as f:
        scout_content = f.read()

    print(f"   📄 Research loaded: {len(scout_content)} characters")

    # Prepare context as if it came from the researcher
    contexto = {
        "content": scout_content,
        "layer": "scout_newsjacking",
        "sources": [
            "https://blog.youtube/news-and-events/mrbeast-streamer-challenge-one-million-dollars/",
            "https://www.dexerto.com/youtube/mrbeast-pits-50-streamers-against-each-other-with-final-four-competing-for-1m-live-3346619/",
            "https://www.fastcompany.com/91211168/mrbeasts-youtube-dominance-takes-a-dip",
            "https://www.svg.com/1644886/mrbeast-viewership-rapidly-dropping-amid-scandals/",
            "https://www.statista.com/statistics/1346129/mrbeast-video-view-numbers",
            "https://win.gg/roster-mrbeast-50-streamer-event/",
        ],
    }

    print(f"🎯 TOPIC: {TOPIC}")
    print(f"🌐 LANGUAGE: {LANG.upper()}")
    print(f"📁 CATEGORY: {CATEGORY}")
    print()

    # Deterministic translation key
    clean_hash = TOPIC.strip().lower()
    t_hash = hashlib.md5(clean_hash.encode("utf-8")).hexdigest()
    trans_key = f"{t_hash[:8]}-{t_hash[8:12]}-{t_hash[12:16]}-{t_hash[16:20]}-{t_hash[20:]}"
    print(f"🔑 [Hreflang] Translation Key: {trans_key}")

    # PHASE 1: Plan article
    print("\n📋 PHASE 1: Planning article...")
    category_config = NICHES[CATEGORY]
    meta = orchestrator.planificar_articulo(TOPIC, contexto, LANG, category_config)

    if not meta or "slug" not in meta:
        print("❌ ERROR: Article planning failed")
        sys.exit(1)

    print(f"   ✅ Planned title: {meta['titulo']}")
    print(f"   ✅ Slug: {meta['slug']}")

    # Save sources for the corrector
    print("   📝 Saving sources into Link Deposit...")
    orchestrator.guardar_fuentes(meta["slug"], contexto["sources"], lang=LANG)

    # PHASE 2: Write article
    print("\n✍️  PHASE 2: Generating article content (this can take 2-3 minutes)...")
    texto = orchestrator.escribir_articulo(
        meta,
        contexto,
        LANG,
        category_config,
        category=CATEGORY,
    )

    if not texto or len(texto) < 500:
        print("❌ ERROR: Generated article is too short or failed")
        sys.exit(1)

    word_count = len(texto.split())
    print(f"   ✅ Article generated: {word_count} words")

    # PHASE 3: Save article
    print("\n💾 PHASE 3: Saving article...")
    orchestrator.guardar_post(
        meta,
        texto,
        LANG,
        CATEGORY,
        translation_key=trans_key,
    )

    # Mark as completed
    completed_file = "data/completed.txt"
    with open(completed_file, "a", encoding="utf-8") as f:
        f.write(f"{CATEGORY}: {TOPIC}\n")

    # Final summary
    print("\n" + "=" * 70)
    print("✅ NEWSJACKING COMPLETED (EN)")
    print("=" * 70)
    print(f"📄 File: content/{LANG}/{CATEGORY}/{meta['slug']}.md")
    print(f"📝 Title: {meta['titulo']}")
    print(f"🔤 Words: {word_count}")
    print(f"🔑 Translation Key: {trans_key}")
    print()
    print("💡 Next steps:")
    print("   1. Review article: git diff content/")
    print("   2. Commit: git add content/ && git commit -m 'Add MrBeast EN newsjacking article'")
    print("   3. Push: git push origin main")
    print("=" * 70)


if __name__ == "__main__":
    main()
