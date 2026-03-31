"""
fix_h2.py — Fixes empty H2 tags by replacing them with a meaningful conclusion title.
"""
import os
import re
import glob

CONTENT_DIRS = [
    os.path.join(os.getcwd(), 'content', 'en'),
    os.path.join(os.getcwd(), 'content', 'es'),
]

# Pattern for empty H2 (e.g. "## ", "##", "##    ")
EMPTY_H2_PATTERN = re.compile(r'^##\s*$', re.MULTILINE)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False
        
    if not EMPTY_H2_PATTERN.search(content):
        return False
        
    # Determine language from directory
    is_spanish = '/es/' in filepath or '\\es\\' in filepath
    
    replacement = '## En Resumen' if is_spanish else '## The Bottom Line'
    
    new_content = EMPTY_H2_PATTERN.sub(replacement, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    print("=" * 60)
    print("FIX EMPTY H2 - Eliminando H2 vacíos (AdSense SEO Blocker)")
    print("=" * 60)
    
    modified = 0
    all_files = []
    for d in CONTENT_DIRS:
        all_files.extend(glob.glob(os.path.join(d, '**', '*.md'), recursive=True))
        
    for filepath in all_files:
        if process_file(filepath):
            modified += 1
            print(f"  FIXED empty H2 in: {os.path.basename(filepath)}")
            
    print("=" * 60)
    print(f"Total de archivos reparados: {modified}")
    
if __name__ == "__main__":
    main()
