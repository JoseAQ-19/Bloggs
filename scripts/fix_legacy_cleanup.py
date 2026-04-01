#!/usr/bin/env python3
"""
FASE 4: Limpieza masiva de artículos legacy.
- Rellena description: "" con las primeras 155 chars del contenido.
- Cambia draft: true → draft: false (publicar todo).
"""
import re
import glob

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # --- FIX 1: description vacía ---
    if 'description: ""' in content or "description: ''" in content:
        # Extraer el cuerpo del post (después del segundo ---)
        parts = content.split('---', 2)
        if len(parts) >= 3:
            body = parts[2].strip()
            # Limpiar markdown del body para description
            clean_body = re.sub(r'[#*\[\]!()]', '', body)
            clean_body = re.sub(r'\n+', ' ', clean_body).strip()
            clean_body = clean_body[:155].replace('"', "'").strip()
            if len(clean_body) > 20:
                clean_body += "..."
                content = content.replace('description: ""', f'description: "{clean_body}"')
                content = content.replace("description: ''", f'description: "{clean_body}"')
                changes.append("description")
    
    # --- FIX 2: draft: true → false ---
    if 'draft: true' in content:
        content = content.replace('draft: true', 'draft: false')
        changes.append("draft")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []

def main():
    files = glob.glob('content/**/*.md', recursive=True)
    fixed_desc = 0
    fixed_draft = 0
    
    for fpath in files:
        if '_index.md' in fpath:
            continue
        changes = fix_file(fpath)
        if 'description' in changes:
            fixed_desc += 1
        if 'draft' in changes:
            fixed_draft += 1
    
    print(f"\n✅ LIMPIEZA COMPLETA:")
    print(f"   📝 Descriptions reparadas: {fixed_desc}")
    print(f"   📤 Drafts publicados: {fixed_draft}")
    print(f"   📁 Total archivos escaneados: {len(files)}")

if __name__ == "__main__":
    main()
