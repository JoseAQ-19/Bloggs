
import os
import glob
import time
import frontmatter
import re
from content_engine_pro import main_upgrade_engine
from utils import ContentCleaner

def is_bad_quality(path):
    """
    Detecta si un artículo es basura según los criterios del PASO 2:
    - Fugas de metadatos (title:, slug:, etc)
    - Emojis en títulos (H2/H3)
    - Falta de secciones GEO (TL;DR y Metodología)
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Detectar Frontmatter leak en el body
        parts = content.split('---', 2)
        if len(parts) < 3: return True # Mal formato
        
        body = parts[2]
        
        # Leaks crudos
        if any(x in body.lower() for x in ['title:', 'slug:', 'translationkey:', '---']):
            print(f"   🚩 Fuga detectada en {path}")
            return True
            
        # 2. Detectar Emojis en headers (H2/H3)
        # Regex para emojis
        emoji_pattern = re.compile(r'##+.*[\U00010000-\U0010ffff]')
        if emoji_pattern.search(body):
            print(f"   🚩 Emojis en headers detectados en {path}")
            return True
            
        # 3. Falta de secciones GEO
        # Buscamos "## Resumen Ejecutivo" o similar
        if not re.search(r'##\s*(?:Resumen Ejecutivo|TL;DR)', body, re.IGNORECASE):
            print(f"   🚩 Falta TL;DR en {path}")
            return True
        
        if not re.search(r'##\s*(?:Metodología y Fuentes|Sources|Fuentes)', body, re.IGNORECASE):
            print(f"   🚩 Falta sección de Fuentes en {path}")
            return True
            
        # 4. Thin content
        if len(body.split()) < 1000:
            print(f"   🚩 Contenido demasiado corto ({len(body.split())} palabras) en {path}")
            return True
            
        return False
    except Exception as e:
        print(f"Error analizando {path}: {e}")
        return True

import argparse

def transform_to_masterpieces(limit=None):
    print("💎 INICIANDO TRANSFORMACIÓN: DE BASURA A OBRA MAESTRA 💎")
    
    # Escaneamos todo el contenido
    all_files = glob.glob('content/**/*.md', recursive=True)
    # Excluir _index.md
    target_files = [f for f in all_files if not os.path.basename(f).startswith('_index')]
    
    bad_files = []
    for f in target_files:
        if is_bad_quality(f):
            bad_files.append(f)
            
    print(f"📊 Resultado del escaneo: {len(bad_files)} de {len(target_files)} artículos necesitan reescritura.")
    
    # Aplicar límite
    to_process = bad_files[:limit] if limit else bad_files
    
    for i, path in enumerate(to_process):
        print(f"\n✨ [{i+1}/{len(to_process)}] Elevando a Obra Maestra: {path}")
        try:
            # Reescritura total
            main_upgrade_engine(path)
            # Pequeño delay para Rate Limits de Gemini
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error procesando masterpiece {path}: {e}")
            
    print(f"\n✅ PROCESO FINALIZADO. {len(to_process)} obras maestras generadas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Límite de artículos a procesar")
    args = parser.parse_args()
    
    transform_to_masterpieces(limit=args.limit)
