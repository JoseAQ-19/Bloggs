#!/usr/bin/env python3
"""
fix_adsense_batch.py — Correcciones masivas Pre-AdSense para NovumWorld
=======================================================================
Ejecuta todas las correcciones Tier 1 de la auditoría:
1. Eliminar artículos OAKM duplicados (mantener el mejor)
2. Eliminar artículo RE VC duplicado
3. Limpiar artefactos "GEMINI GROUNDING E-E-A-T" de todo el contenido
4. Mover artículos en español de /en/ia/ a /es/ia/
5. Reemplazar "The Machine's Verdict" → "Our Verdict" en artículos EN
6. Reemplazar "Nuestra lectura" → "Nuestra Opinión" en artículos ES
7. Corregir meta descriptions truncadas
"""

import os
import re
import glob
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE, "content")

# Counters
stats = {
    "deleted_duplicates": 0,
    "gemini_cleaned": 0,
    "moved_es_files": 0,
    "verdict_fixed_en": 0,
    "lectura_fixed_es": 0,
    "meta_fixed": 0,
}


# =====================================================
# 1. DELETE DUPLICATE OAKM ARTICLES (keep the longest)
# =====================================================
def delete_oakm_duplicates():
    print("\n" + "=" * 60)
    print("STEP 1: Deleting duplicate OAKM articles...")
    print("=" * 60)

    funds_dir = os.path.join(CONTENT_DIR, "en", "funds")
    oakm_files = glob.glob(os.path.join(funds_dir, "oakm-*.md"))

    if len(oakm_files) <= 1:
        print("   ✅ No duplicates found (≤1 OAKM article)")
        return

    # Find the longest article (best one to keep)
    best_file = None
    best_size = 0
    for f in oakm_files:
        size = os.path.getsize(f)
        if size > best_size:
            best_size = size
            best_file = f

    print(f"   🏆 Keeping: {os.path.basename(best_file)} ({best_size} bytes)")

    for f in oakm_files:
        if f != best_file:
            os.remove(f)
            print(f"   🗑️  Deleted: {os.path.basename(f)}")
            stats["deleted_duplicates"] += 1


# =====================================================
# 1b. DELETE DUPLICATE RE VC ARTICLES
# =====================================================
def delete_revc_duplicates():
    print("\n" + "=" * 60)
    print("STEP 1b: Deleting duplicate RE VC articles...")
    print("=" * 60)

    funds_dir = os.path.join(CONTENT_DIR, "en", "funds")
    revc_files = glob.glob(os.path.join(funds_dir, "re-vc-*.md"))

    if len(revc_files) <= 1:
        print("   ✅ No duplicates found (≤1 RE VC article)")
        return

    best_file = None
    best_size = 0
    for f in revc_files:
        size = os.path.getsize(f)
        if size > best_size:
            best_size = size
            best_file = f

    print(f"   🏆 Keeping: {os.path.basename(best_file)} ({best_size} bytes)")

    for f in revc_files:
        if f != best_file:
            os.remove(f)
            print(f"   🗑️  Deleted: {os.path.basename(f)}")
            stats["deleted_duplicates"] += 1


# =====================================================
# 1c. DELETE DUPLICATE MORNINGSTAR/KNOCKOUTSTOCKS
# =====================================================
def delete_morningstar_duplicates():
    print("\n" + "=" * 60)
    print("STEP 1c: Deleting duplicate Morningstar comparison articles...")
    print("=" * 60)

    funds_dir = os.path.join(CONTENT_DIR, "en", "funds")
    # These two are essentially the same topic with reversed framing
    ms_files = [
        os.path.join(funds_dir, "morningstar-outperforms-knockoutstocks-by-5-in-2026s-key-sectors-en.md"),
        os.path.join(funds_dir, "knockoutstocks-vs-morningstar-a-2026-head-to-head-based-on-5-key-metrics-en.md"),
    ]
    existing = [f for f in ms_files if os.path.exists(f)]
    if len(existing) <= 1:
        print("   ✅ No duplicates found")
        return

    # Keep the longer one
    best_file = max(existing, key=os.path.getsize)
    print(f"   🏆 Keeping: {os.path.basename(best_file)}")
    for f in existing:
        if f != best_file:
            os.remove(f)
            print(f"   🗑️  Deleted: {os.path.basename(f)}")
            stats["deleted_duplicates"] += 1

    # Also check S&P 500 duplicates
    sp_files = glob.glob(os.path.join(funds_dir, "sp-500-fund*-en.md"))
    if len(sp_files) > 1:
        best = max(sp_files, key=os.path.getsize)
        print(f"   🏆 Keeping S&P: {os.path.basename(best)}")
        for f in sp_files:
            if f != best:
                os.remove(f)
                print(f"   🗑️  Deleted S&P: {os.path.basename(f)}")
                stats["deleted_duplicates"] += 1

    # Vanguard fee duplicates
    vg_files = glob.glob(os.path.join(funds_dir, "vanguard*-en.md"))
    if len(vg_files) > 1:
        best = max(vg_files, key=os.path.getsize)
        print(f"   🏆 Keeping Vanguard: {os.path.basename(best)}")
        for f in vg_files:
            if f != best:
                os.remove(f)
                print(f"   🗑️  Deleted Vanguard: {os.path.basename(f)}")
                stats["deleted_duplicates"] += 1


# =====================================================
# 2. CLEAN GEMINI GROUNDING ARTIFACTS
# =====================================================
def clean_gemini_artifacts():
    print("\n" + "=" * 60)
    print("STEP 2: Cleaning GEMINI GROUNDING artifacts...")
    print("=" * 60)

    all_md = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)

    for filepath in all_md:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if "GEMINI GROUNDING" not in content and "GEMINI_GROUNDING" not in content:
            continue

        original = content
        # Remove patterns like: "according to **GEMINI GROUNDING E-E-A-T**"
        content = re.sub(r',?\s*according to \*\*GEMINI[^*]*\*\*', '', content)
        content = re.sub(r',?\s*as detailed by \*\*GEMINI[^*]*\*\*', '', content)
        content = re.sub(r',?\s*as reported by \*\*GEMINI[^*]*\*\*', '', content)
        # Remove standalone **GEMINI GROUNDING E-E-A-T**
        content = re.sub(r'\*\*GEMINI[^*]*GROUNDING[^*]*\*\*', '', content)
        # Clean up any double spaces left behind
        content = re.sub(r'  +', ' ', content)
        # Clean up comma-space-period patterns
        content = re.sub(r',\s*\.', '.', content)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   🧹 Cleaned: {os.path.relpath(filepath, BASE)}")
            stats["gemini_cleaned"] += 1


# =====================================================
# 3. MOVE SPANISH ARTICLES FROM /en/ia/ TO /es/ia/
# =====================================================
def move_spanish_articles():
    print("\n" + "=" * 60)
    print("STEP 3: Moving Spanish articles from /en/ia/ to /es/ia/...")
    print("=" * 60)

    en_ia_dir = os.path.join(CONTENT_DIR, "en", "ia")
    es_ia_dir = os.path.join(CONTENT_DIR, "es", "ia")

    spanish_files = [
        "democracia-digital-la-mayor-estafa-del-siglo-xxi.md",
        "donde-estan-mis-coches-voladores-la-estafa-futuris.md",
        "el-futuro-es-ahora-las-7-tendencias-que-los-gobier.md",
        "el-futuro-es-distopico-y-ya-esta-aqui.md",
        "geopolitica-2026-el-ano-en-que-dejamos-de-fingir.md",
        "groenlandia-el-nuevo-jaque-mate-geopolitico-que-hu.md",
        "la-elites-digitales-amos-del-mundo-o-nuevos-parasi.md",
        "la-ia-te-miente-por-que-la-personalidad-artificial.md",
        "la-ia-viene-a-quitarte-el-almuerzo-y-no-se-disculp.md",
        "tecnoutopia-fallida-el-sueno-digital-se-convierte.md",
    ]

    os.makedirs(es_ia_dir, exist_ok=True)

    for filename in spanish_files:
        src = os.path.join(en_ia_dir, filename)
        dst = os.path.join(es_ia_dir, filename)
        if os.path.exists(src):
            # Check if destination already exists
            if os.path.exists(dst):
                # If the file already exists in ES, just delete the EN copy
                os.remove(src)
                print(f"   🗑️  Deleted (already in ES): {filename}")
            else:
                # Also fix the language field in frontmatter
                with open(src, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = re.sub(r'language:\s*"en"', 'language: "es"', content)
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.remove(src)
                print(f"   📦 Moved: {filename}")
            stats["moved_es_files"] += 1
        else:
            print(f"   ⚠️  Not found: {filename}")


# =====================================================
# 4. FIX "The Machine's Verdict" → "Our Verdict" (EN)
# =====================================================
def fix_machine_verdict():
    print("\n" + "=" * 60)
    print("STEP 4: Fixing 'The Machine's Verdict' → 'Our Verdict' (EN)...")
    print("=" * 60)

    all_md = glob.glob(os.path.join(CONTENT_DIR, "en", "**", "*.md"), recursive=True)

    for filepath in all_md:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Fix all variants of "The Machine's Verdict"
        content = re.sub(
            r"(#{1,3}\s*)The Machine's Verdict.*",
            r"\1Our Verdict",
            content
        )
        content = re.sub(
            r"\*\*The Machine's Verdict\*\*",
            "**Our Verdict**",
            content
        )
        # Also fix inline references like "The Machine sees through..."
        content = content.replace("The Machine sees through", "We see through")
        content = content.replace("The Machine's Verdict:", "Our Verdict:")

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✏️  Fixed: {os.path.relpath(filepath, BASE)}")
            stats["verdict_fixed_en"] += 1


# =====================================================
# 5. FIX "Nuestra lectura" → "Nuestra Opinión" (ES)
# =====================================================
def fix_nuestra_lectura():
    print("\n" + "=" * 60)
    print("STEP 5: Fixing 'Nuestra lectura' → 'Nuestra Opinión' (ES)...")
    print("=" * 60)

    all_md = glob.glob(os.path.join(CONTENT_DIR, "es", "**", "*.md"), recursive=True)

    for filepath in all_md:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Case-insensitive replacement of all variants
        content = re.sub(
            r"(#{1,3}\s*)Nuestra [Ll]ectura\b(.*)",
            r"\1Nuestra Opinión\2",
            content
        )

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✏️  Fixed: {os.path.relpath(filepath, BASE)}")
            stats["lectura_fixed_es"] += 1


# =====================================================
# 6. FIX TRUNCATED META DESCRIPTIONS
# =====================================================
def fix_meta_descriptions():
    print("\n" + "=" * 60)
    print("STEP 6: Fixing truncated meta descriptions...")
    print("=" * 60)

    all_md = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)

    for filepath in all_md:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find description field in frontmatter
        match = re.search(r'description:\s*"([^"]*)"', content)
        if not match:
            continue

        desc = match.group(1)

        # Check if truncated (ends with incomplete word or dangling "and", "or", "the", etc.)
        truncation_patterns = [
            r'\band\s*\.?$',      # ends with "and" or "and."
            r'\bor\s*\.?$',       # ends with "or"
            r'\bthe\s*\.?$',      # ends with "the"
            r'\ba\s*\.?$',        # ends with "a"
            r'\bfor\s*\.?$',      # ends with "for"
            r'\bin\s*\.?$',       # ends with "in"
            r'\bto\s*\.?$',       # ends with "to"
            r'\bits\s*\.?$',      # ends with "its"
            r'\bof\s*\.?$',       # ends with "of"
            r'\bwith\s*\.?$',     # ends with "with"
            r'\bpara\s*\.?$',     # ends with "para" (ES)
            r'\bcon\s*\.?$',      # ends with "con" (ES)
            r'\ben\s*\.?$',       # ends with "en" (ES)
            r'\bde\s*\.?$',       # ends with "de" (ES)
            r'\by\s*\.?$',        # ends with "y" (ES)
            r'\bsu\s*\.?$',       # ends with "su" (ES)
            r'\besta\s*\.?$',     # ends with "esta" (ES)
        ]

        is_truncated = False
        for pattern in truncation_patterns:
            if re.search(pattern, desc.strip(), re.IGNORECASE):
                is_truncated = True
                break

        if not is_truncated:
            continue

        # Fix: find last complete sentence
        cleaned = desc.strip()
        # Find last sentence-ending punctuation
        last_period = cleaned.rfind('.')
        last_excl = cleaned.rfind('!')
        last_quest = cleaned.rfind('?')
        cut_point = max(last_period, last_excl, last_quest)

        if cut_point > 60:  # Ensure minimum reasonable length
            fixed_desc = cleaned[:cut_point + 1]
        else:
            # Fallback: cut at last complete word before the dangling part
            words = cleaned.split()
            # Remove the last dangling word(s)
            while words and re.match(r'^(and|or|the|a|for|in|to|its|of|with|para|con|en|de|y|su|esta)\.?$', words[-1], re.IGNORECASE):
                words.pop()
            fixed_desc = ' '.join(words)
            if not fixed_desc.endswith(('.', '!', '?')):
                fixed_desc += '.'

        if fixed_desc != desc:
            content = content.replace(f'description: "{desc}"', f'description: "{fixed_desc}"')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📝 Fixed meta: {os.path.relpath(filepath, BASE)}")
            print(f"      Before: \"{desc[-40:]}\"")
            print(f"       After: \"{fixed_desc[-40:]}\"")
            stats["meta_fixed"] += 1


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    print("🔧 NovumWorld Pre-AdSense Batch Fix")
    print("=" * 60)

    delete_oakm_duplicates()
    delete_revc_duplicates()
    delete_morningstar_duplicates()
    clean_gemini_artifacts()
    move_spanish_articles()
    fix_machine_verdict()
    fix_nuestra_lectura()
    fix_meta_descriptions()

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print(f"\n   Total changes: {sum(stats.values())}")
    print("=" * 60)
    print("✅ Done! Review changes with: git diff --stat")
