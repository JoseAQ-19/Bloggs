"""
purge_cliches.py — Replaces AI cliché phrases in H2 headers and body text.
"""
import os
import re
import glob

CONTENT_DIRS = [
    os.path.join(os.getcwd(), 'content', 'en'),
    os.path.join(os.getcwd(), 'content', 'es'),
]

# Map: cliche phrase -> replacement (context-aware where possible)
HEADER_REPLACEMENTS = {
    # H2 "Double-Edged Sword" in various contexts
    r"(##\s+.*?)Double-Edged Sword": r"\1Risks and Tradeoffs",
    r"(##\s+.*?)double-edged sword": r"\1Risks and Tradeoffs",
    r"(##\s+.*?)Doble Filo": r"\1Riesgos y Compromisos",
    r"(##\s+.*?)doble filo": r"\1Riesgos y Compromisos",
}

# Body text replacements: cliche -> neutral alternative
BODY_REPLACEMENTS = [
    (r'(?i)a double-edged sword', 'a significant tradeoff'),
    (r'(?i)double-edged sword',   'notable tradeoff'),
    (r'(?i)de doble filo',         'con riesgos significativos'),
    (r'(?i)game[\s-]?changer',     'significant shift'),
    (r'(?i)In conclusion,',        ''),
    (r'(?i)En conclusión,',        ''),
    (r'(?i)In the ever-evolving landscape of', 'In'),
    (r'(?i)In today\'s rapidly evolving', 'In the current'),
    (r'(?i)It\'s worth noting that', ''),
    (r'(?i)It is worth noting that', ''),
    (r'(?i)Cabe destacar que', ''),
]

stats = {'files': 0, 'replacements': 0}


def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return

    original = content

    # Header replacements
    for pattern, replacement in HEADER_REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)

    # Body replacements
    for pattern, replacement in BODY_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    # Clean double spaces from empty replacements
    content = re.sub(r'  +', ' ', content)
    content = re.sub(r'^ +', '', content, flags=re.MULTILINE)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        stats['files'] += 1
        count = sum(1 for a, b in zip(original, content) if a != b)
        stats['replacements'] += 1
        print(f"  FIXED: {os.path.basename(filepath)}")


def main():
    print("=" * 60)
    print("PURGE CLICHES - Eliminando frases prohibidas de IA")
    print("=" * 60)

    all_files = []
    for d in CONTENT_DIRS:
        all_files.extend(glob.glob(os.path.join(d, '**', '*.md'), recursive=True))

    for f in all_files:
        process_file(f)

    print(f"\nArchivos corregidos: {stats['files']}")
    print("=" * 60)

    # Verify
    remaining = 0
    for f in all_files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                c = fh.read()
                if re.search(r'(?i)double.edged sword', c):
                    remaining += 1
                    print(f"  WARNING remains: {os.path.basename(f)}")
        except Exception:
            pass
    
    if remaining == 0:
        print("VERIFICACION: CERO frases 'double-edged sword' restantes.")
    else:
        print(f"ALERTA: {remaining} archivos aun tienen la frase.")

if __name__ == "__main__":
    main()
