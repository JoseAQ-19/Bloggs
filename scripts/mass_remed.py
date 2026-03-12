import os
import glob
import sys
from pathlib import Path

# Añadir el raíz al path
sys.path.append(str(Path(__file__).parent.parent))
from scripts.remed import optimize_article

def mass_fix_26():
    # Obtener artículos MD (excluyendo _index)
    md_files = glob.glob(os.path.join("content", "**", "*.md"), recursive=True)
    md_files = [f for f in md_files if not os.path.basename(f).startswith("_index")]
    
    # Ordenar por fecha de modificación (más recientes primero)
    md_files.sort(key=os.path.getmtime, reverse=True)
    
    # Los 26 más recientes (o menos si hay pocos)
    target_articles = md_files[:26]
    
    print(f"STARTING: mass remediation of the {len(target_articles)} latest articles...")
    
    success_count = 0
    for i, path in enumerate(target_articles):
        print(f"[{i+1}/26] Processing: {path}")
        if optimize_article(path):
            success_count += 1
        else:
            print(f"  [-] Failed optimization of {path}")
        import time
        time.sleep(2)
            
    print(f"\nDONE. {success_count}/{len(target_articles)} articles optimized.")

if __name__ == "__main__":
    mass_fix_26()
