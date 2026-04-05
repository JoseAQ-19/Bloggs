
import os
import glob
import re

def fix_english_headers():
    # Ruta estricta para artículos en inglés
    base_path = r"c:\Users\usuario\Bloggs\content\en"
    pattern = os.path.join(base_path, "**", "*.md")
    files = glob.glob(pattern, recursive=True)
    
    count = 0
    print(f"🚀 Iniciando escaneo de {len(files)} archivos en /en/...")
    
    # Expresión regular para capturar el nivel de H2/H3 y la cadena errónea
    # Soporta: ## Resumen Ejecutivo, ### Resumen Ejecutivo, etc.
    regex_err = r"^(#{2,3})\s+Resumen Ejecutivo"
    
    for fpath in files:
        if os.path.basename(fpath).startswith("_index"):
            continue
            
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificamos si el error existe en este archivo
            if re.search(regex_err, content, re.MULTILINE):
                # Reemplazo dinámico respetando el nivel (#)
                new_content = re.sub(regex_err, r"\1 Executive Summary", content, flags=re.MULTILINE)
                
                with open(fpath, 'w', encoding='utf-8', newline='') as f:
                    f.write(new_content)
                
                print(f"✅ Corregido: {os.path.relpath(fpath, base_path)}")
                count += 1
        except Exception as e:
            print(f"❌ Error procesando {fpath}: {e}")
            
    print(f"\n✨ Operación completada. Se han corregido {count} artículos.")

if __name__ == "__main__":
    fix_english_headers()
