import os
import glob
import time
import frontmatter
from content_engine_pro import main_upgrade_engine
from utils import ContentCleaner

def scan_and_rewrite():
    print("🚀 Iniciando Escaneo y Reescritura Masiva (CRISIS SPAM)")
    
    # 1. Encontrar archivos infectados
    bad_files = []
    for fpath in glob.glob('content/**/*.md', recursive=True):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar el segundo '---' que separa el frontmatter del body
            parts = content.split('---', 2)
            if len(parts) < 3: continue
            
            body = parts[2]
            
            # Condición de infección:
            is_infected = False
            if 'title:' in body or 'slug:' in body or '```json' in body or '```yaml' in body:
                is_infected = True
            elif len(body.split()) < 500: # Thin content extreme
                is_infected = True
                
            if is_infected:
                bad_files.append(fpath)
        except Exception as e:
            print(f"Error leyendo {fpath}: {e}")

    print(f"⚠️ {len(bad_files)} archivos identificados como Bajas Calidad/Leakeados.")
    
    # 2. Reescritura o Limpieza
    for i, path in enumerate(bad_files):
        print(f"\n[{i+1}/{len(bad_files)}] Procesando: {path}")
        
        # Opcional: limpiar metadatos residuales primero, aunque
        # content_engine_pro generará un contenido total nuevo.
        post = frontmatter.load(path)
        post.content = ContentCleaner.sanitize_body(post.content) 
        with open(path, 'wb') as f:
            frontmatter.dump(post, f)

        # Usar el motor V3 PRO para rehacerlo completamente con el nuevo System Prompt
        try:
             main_upgrade_engine(path)
             # Esperamos para no golpear rate limits
             time.sleep(3)
        except Exception as e:
             print(f"Error reescribiendo {path}: {e}")

    print("✅ Operación completada.")

if __name__ == "__main__":
    scan_and_rewrite()
