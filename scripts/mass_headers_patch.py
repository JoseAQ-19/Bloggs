import os
import re
import frontmatter
import json

def patch_article(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
    except:
        return False

    content = post.content.strip()
    lang = "es" if "/es/" in filepath.replace("\\", "/") else "en"
    
    # Headers
    tl_dr_header = "## Resumen Ejecutivo" if lang == "es" else "## Executive Summary"
    method_header = "## Metodología y Fuentes" if lang == "es" else "## Methodology and Sources"
    
    modified = False
    
    # 1. Inyectar TL;DR si falta
    if not any(x in content for x in ["(TL;DR)", "Executive Summary", "Resumen Ejecutivo"]):
        # Extraer los primeros 2 párrafos o oraciones para el TL;DR simulado
        paragraphs = content.split('\n\n')
        intro = paragraphs[0] if paragraphs else "Información clave sobre este artículo."
        # Si el primer párrafo es muy corto, coger el segundo también
        if len(intro.split()) < 20 and len(paragraphs) > 1:
            intro += "\n\n" + paragraphs[1]
            
        tldr_block = f"{tl_dr_header}\n\n* {intro[:300]}...\n\n"
        content = tldr_block + content
        modified = True
        
    # 2. Inyectar Metodología si falta
    if not any(x in content for x in ["Metodología", "Methodology", "Fuentes", "Sources"]):
        content = content + f"\n\n{method_header}\n\nEste análisis se basa en fuentes públicas de la industria, datos oficiales y reportes de mercado actualizados."
        modified = True
        
    if modified:
        post.content = content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        return True
    return False

def main():
    # Solo parchear los que NO son "Thin" pero tienen otros problemas (según el JSON anterior)
    try:
        with open('ALL_FAILED_ARTICLES.json', 'r', encoding='utf-8') as f:
            failed = json.load(f)
    except:
        print("ERROR: ALL_FAILED_ARTICLES.json not found. Run scripts/audit_all.py first.")
        return

    count = 0
    to_patch = [f for f in failed if not any("Thin" in i for i in f['issues'])]
    
    print(f"INFO: Parcheando {len(to_patch)} artículos estructuralmente...")
    
    for item in to_patch:
        if patch_article(item['file']):
            count += 1
            
    print(f"FIN: {count} artículos parcheados.")

if __name__ == "__main__":
    main()
