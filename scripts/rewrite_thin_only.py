import frontmatter
import os
import time
import re
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))
from scripts.llm_router import LLMRouter

load_dotenv()

def clean_leaked_tags(content):
    # Eliminar bloques YAML y tags repetidos
    patterns = [
        r"^---\s*$.*?^---\s*$",
        r"^(title|slug|language|description|categories|tags|date|featured_image|canonical|translationKey):\s*.*$",
    ]
    cleaned = content
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.MULTILINE | re.DOTALL)
    return cleaned.strip()

def rewrite_thin_article(path):
    print(f"INFO: Reescribiendo THIN CONTENT {os.path.basename(path)}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            title = post.get('title', 'Unknown Title')
            original_content = clean_leaked_tags(post.content)
    except: return False
        
    lang = "es" if "/es/" in path.replace("\\", "/") else "en"
    tl_dr = "## Resumen Ejecutivo" if lang == "es" else "## Executive Summary"
    method = "## Metodología y Fuentes" if lang == "es" else "## Methodology and Sources"
    ymyl = "*Aviso YMYL: Información educativa. Consulte especialistas.*" if lang == "es" else "*YMYL Disclaimer: For informational purposes only.*"

    system_prompt = "Periodista experto AdSense Tier 1. Long-form content (>1000 words)."
    prompt = f"TITULO: {title}\nIDIOMA: {lang.upper()}\n\nReescribe este artículo con profundidad analítica (>1000 palabras).\nORDEN: {tl_dr}, Cuerpo H2/H3 desglosado por puntos técnicos, {method}, {ymyl}.\nCERO YAML.\nCONTENIDO BASE: {original_content}"

    try:
        new_content = LLMRouter.call_capa_cero(prompt, system_prompt, model_type="reasoning")
        if not new_content: return False
            
        new_content = clean_leaked_tags(new_content)
        if not new_content.startswith('##'): new_content = f"{tl_dr}\n" + new_content

        post.content = new_content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        print("✅ OK.")
        return True
    except: return False

if __name__ == "__main__":
    with open('ALL_FAILED_ARTICLES.json', 'r', encoding='utf-8') as f:
        failed = json.load(f)
    
    thin_files = [x['file'] for x in failed if 'Thin' in str(x['issues'])]
    print(f"--- REGENERANDO {len(thin_files)} ARTÍCULOS THIN ---")
    
    count = 0
    for f in thin_files:
        if os.path.exists(f):
            if rewrite_thin_article(f): count += 1
            time.sleep(2)
    print(f"\nFIN EXORCISMO THIN: {count}/{len(thin_files)}")
