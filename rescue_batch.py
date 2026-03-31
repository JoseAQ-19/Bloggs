"""
rescue_batch.py — Operación Rescate: rehabilitación masiva de artículos en cuarentena.

FASE 1: Fix mecánico de metadatos + limpieza regex + repatriación.
"""
import os
import re
import glob
import json
import hashlib
import shutil
import audit_v2

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DRAFTS_DIR = os.path.join(os.getcwd(), 'content', 'drafts_to_fix')
CONTENT_EN = os.path.join(os.getcwd(), 'content', 'en')
CONTENT_ES = os.path.join(os.getcwd(), 'content', 'es')

# AI prompt leaks to eliminate
AI_LEAKS = [
    r"(?i)^here is the (?:rewritten |revised |)(?:article|text|content)[:\.]?\s*\n*",
    r"(?i)^sure[,!]?\s*here(?:'s| is).*?\n+",
    r"(?i)^aqui tienes.*?\n+",
    r"(?i)^claro que si.*?\n+",
    r"(?i)^(?:of course|certainly)[,!]?\s*here.*?\n+",
]

# Robotic/cliché phrases to purge (exact match within text)
BANNED_PHRASES_EN = [
    "in conclusion,", "in conclusion.", "In conclusion,", "In conclusion.",
    "in summary,", "in summary.", "In summary,", "In summary.",
    "it remains to be seen", "It remains to be seen",
    "game-changer", "Game-changer", "game changer",
    "double-edged sword", "Double-edged sword",
    "in the ever-evolving", "In the ever-evolving",
    "ever-evolving landscape", "ever-evolving world",
    "delve into", "Delve into", "delving into",
    "a world of possibilities",
    "unlock your potential", "Unlock your potential",
    "it goes without saying", "It goes without saying",
    "without a doubt", "Without a doubt",
    "the bottom line is", "The Bottom Line",
    "final thoughts", "Final Thoughts",
    "as we have seen,", "As we have seen,",
    "here is a list", "Here is a list",
    "is revolutionizing", "poised for explosive growth",
    "driving innovation",
]
BANNED_PHRASES_ES = [
    "en conclusión,", "en conclusión.", "En conclusión,", "En conclusión.",
    "en resumen,", "en resumen.", "En resumen,", "En resumen.",
    "en el vertiginoso mundo", "En el vertiginoso mundo",
    "queda por ver", "Queda por ver",
    "un arma de doble filo", "Un arma de doble filo",
    "a continuación", "A continuación,",
    "es importante destacar", "Es importante destacar",
    "promete revolucionar", "crecimiento explosivo",
    "como hemos visto,", "Como hemos visto,",
    "sin lugar a dudas", "Sin lugar a dudas",
    "en última instancia", "En última instancia",
    "aquí tienes", "Aquí tienes",
    "en definitiva,", "En definitiva,",
    "revolucionando el mañana",
    "un mundo de posibilidades",
]


def generate_translation_key(filename):
    """Generate a stable translationKey from the filename slug."""
    slug = os.path.splitext(filename)[0]
    # Remove language suffix if present
    slug = re.sub(r'-(?:en|es)$', '', slug)
    # Create a short, stable hash
    short_hash = hashlib.md5(slug.encode()).hexdigest()[:8]
    return f"{slug[:50]}-{short_hash}"


def detect_language(frontmatter, filename):
    """Detect article language from frontmatter or filename."""
    lang_match = re.search(r'language:\s*["\']?(\w+)', frontmatter)
    if lang_match:
        lang = lang_match.group(1).lower().strip()
        if lang in ('es', 'en'):
            return lang
    # Fallback: check filename
    if filename.endswith('-en.md'):
        return 'en'
    if filename.endswith('-es.md') or filename.endswith('.md'):
        # Check for Spanish indicators in frontmatter or body
        if any(x in frontmatter.lower() for x in ['es-es', 'español', 'spanish']):
            return 'es'
    # Heuristic: check for common Spanish words in frontmatter
    if any(x in frontmatter.lower() for x in ['categorías', 'descripción', 'título']):
        return 'es'
    # Default based on filename pattern 
    if filename.endswith('-en.md'):
        return 'en'
    return 'es'  # Default for non-suffixed files


def detect_niche(frontmatter, filename):
    """Detect the article niche from frontmatter categories or filename patterns."""
    cat_match = re.search(r'categories:\s*\[?\s*["\']?(\w+)', frontmatter)
    if cat_match:
        return cat_match.group(1).lower()
    
    niche_keywords = {
        'crypto': ['bitcoin', 'crypto', 'ethereum', 'defi', 'blockchain', 'stablecoin', 'nft', 'web3', 'token'],
        'ia': ['ai-', 'ai_', 'anthropic', 'claude', 'openai', 'llm', 'saas', 'chatgpt', 'gemini', 'nvidia'],
        'fitness': ['fitness', 'workout', 'gym', 'muscle', 'exercise', 'health', 'bodyweight', 'vo2'],
        'youtube': ['youtube', 'creator', 'mrbeast', 'streamer', 'tiktok', 'twitch', 'monetization'],
        'funds': ['fund', 'morningstar', 'vanguard', 'etf', 'investment', 'blackrock', 'fidelity', 'sp-500'],
        'viral': ['viral', 'meme', 'trend', 'controversy', 'scandal', 'outrage'],
        'tools': ['tool', 'software', 'review', 'teardown', 'craftsman', 'keychain'],
        'realestate': ['realestate', 'real-estate', 'housing', 'mortgage', 'property'],
    }
    fn_lower = filename.lower()
    for niche, keywords in niche_keywords.items():
        if any(kw in fn_lower for kw in keywords):
            return niche
    return 'ia'  # Fallback niche


def fix_frontmatter(content, filename):
    """Inject translationKey and fix language if missing."""
    parts = content.split('---')
    if len(parts) < 3:
        return content, False  # Broken frontmatter, skip
    
    frontmatter = parts[1]
    body = '---'.join(parts[2:])
    modified = False
    
    # 1. Inject translationKey if missing 
    if 'translationKey' not in frontmatter or re.search(r'translationKey:\s*(?:"|\')?(?:none|null|""|\'\')\s*$', frontmatter, re.IGNORECASE | re.MULTILINE):
        tkey = generate_translation_key(filename)
        frontmatter = frontmatter.rstrip() + f'\ntranslationKey: "{tkey}"\n'
        modified = True
    
    # 2. Ensure language field exists
    if 'language:' not in frontmatter:
        lang = detect_language(frontmatter, filename)
        frontmatter = frontmatter.rstrip() + f'\nlanguage: "{lang}"\n'
        modified = True
    
    return f'---{frontmatter}---{body}', modified


def fix_h1_to_h2(body):
    """Convert H1 headers in the body to H2."""
    # Only match lines that start with exactly one # followed by space
    new_body = re.sub(r'^# (?!#)', '## ', body, flags=re.MULTILINE)
    return new_body, new_body != body


def purge_ai_leaks(content):
    """Remove AI prompt leakage phrases from the beginning of the body."""
    modified = False
    for pattern in AI_LEAKS:
        new_content = re.sub(pattern, '', content, count=1)
        if new_content != content:
            modified = True
            content = new_content
    return content, modified


def purge_banned_phrases(body, lang):
    """Remove banned robotic/cliché phrases."""
    phrases = BANNED_PHRASES_EN if lang == 'en' else BANNED_PHRASES_ES
    modified = False
    for phrase in phrases:
        if phrase in body:
            # Replace with empty string, clean up double spaces/newlines
            body = body.replace(phrase, '')
            modified = True
    # Clean up artifacts from removal (double spaces, empty lines, etc.)
    body = re.sub(r'  +', ' ', body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body, modified


def has_critical_ai_leak(content):
    """Check if the article still has deep AI prompt leaks after cleaning."""
    leak_markers = [
        "soy un modelo de inteligencia",
        "as an ai", "i'm an ai",
        "```json", "```yaml",
        "{{", "}}",  # Hugo template leaks
    ]
    lower = content.lower()
    return any(marker in lower for marker in leak_markers)


def run_rescue():
    files = glob.glob(os.path.join(DRAFTS_DIR, '*.md'))
    
    stats = {
        'total': len(files),
        'rescued': 0,
        'still_quarantined': 0,
        'tkey_fixed': 0,
        'h1_fixed': 0,
        'leaks_cleaned': 0,
        'phrases_cleaned': 0,
        'rescued_en': 0,
        'rescued_es': 0,
        'by_niche': {},
    }
    
    quarantine_log = []
    rescue_log = []

    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Skip legal/structural pages
        if any(x in filename for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md', 'terms-of-service.md']):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            quarantine_log.append(f"ERROR reading {filename}: {e}")
            stats['still_quarantined'] += 1
            continue
        
        # === APPLY ALL FIXES ===
        
        # Fix 1: Frontmatter (translationKey + language)
        content, tkey_mod = fix_frontmatter(content, filename)
        if tkey_mod:
            stats['tkey_fixed'] += 1
        
        # Split for body-level fixes
        parts = content.split('---')
        if len(parts) < 3:
            quarantine_log.append(f"BROKEN FRONTMATTER: {filename}")
            stats['still_quarantined'] += 1
            continue
        
        frontmatter = parts[1]
        body = '---'.join(parts[2:])
        lang = detect_language(frontmatter, filename)
        niche = detect_niche(frontmatter, filename)
        
        # Fix 2: H1 → H2
        body, h1_mod = fix_h1_to_h2(body)
        if h1_mod:
            stats['h1_fixed'] += 1
        
        # Fix 3: AI prompt leaks
        body, leak_mod = purge_ai_leaks(body)
        if leak_mod:
            stats['leaks_cleaned'] += 1
        
        # Fix 4: Banned phrases
        body, phrase_mod = purge_banned_phrases(body, lang)
        if phrase_mod:
            stats['phrases_cleaned'] += 1
        
        # Reconstruct
        content = f'---{frontmatter}---{body}'
        
        # === DECISION: RESCUE OR KEEP IN QUARANTINE ===
        
        if has_critical_ai_leak(content):
            # Still has deep structural leaks — keep quarantined
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)  # Save fixes anyway
            quarantine_log.append(f"STILL QUARANTINED (deep leak): {filename}")
            stats['still_quarantined'] += 1
            continue
        
        # Determine destination folder
        niche_folder = niche
        dest_dir = os.path.join(CONTENT_EN if lang == 'en' else CONTENT_ES, niche_folder)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        
        # Write fixed content and move
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Remove from drafts
        try:
            os.remove(filepath)
        except Exception:
            pass
        
        stats['rescued'] += 1
        if lang == 'en':
            stats['rescued_en'] += 1
        else:
            stats['rescued_es'] += 1
        stats['by_niche'][niche] = stats['by_niche'].get(niche, 0) + 1
        rescue_log.append(f"RESCUED -> {dest_dir}/{filename}")

    # === GENERATE REPORT ===
    report = []
    report.append("=" * 60)
    report.append("OPERACION RESCATE — INFORME DE RESULTADOS")
    report.append("=" * 60)
    report.append(f"Total archivos procesados:     {stats['total']}")
    report.append(f"Articulos RESCATADOS:          {stats['rescued']}")
    report.append(f"  - Ingles (EN):               {stats['rescued_en']}")
    report.append(f"  - Espanol (ES):              {stats['rescued_es']}")
    report.append(f"Aun en cuarentena:             {stats['still_quarantined']}")
    report.append("-" * 60)
    report.append("FIXES APLICADOS:")
    report.append(f"  TranslationKey inyectado:    {stats['tkey_fixed']}")
    report.append(f"  H1 -> H2 convertido:         {stats['h1_fixed']}")
    report.append(f"  Fugas IA limpiadas:          {stats['leaks_cleaned']}")
    report.append(f"  Frases roboticas purgadas:   {stats['phrases_cleaned']}")
    report.append("-" * 60)
    report.append("DISTRIBUCION POR NICHO:")
    for niche, count in sorted(stats['by_niche'].items(), key=lambda x: -x[1]):
        report.append(f"  {niche:20s}: {count}")
    report.append("=" * 60)
    
    if quarantine_log:
        report.append("\nARCHIVOS AUN EN CUARENTENA:")
        for entry in quarantine_log:
            report.append(f"  {entry}")
    
    with open('rescue_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # Print summary to stdout (ASCII-safe)
    for line in report[:20]:
        print(line)
    print(f"\nInforme completo: rescue_report.txt")


if __name__ == "__main__":
    run_rescue()
