import argparse
import sys
import re
import os

def validate_markdown(filepath):
    if not os.path.exists(filepath):
        print(f"FAIL: Archivo no encontrado - {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Separar frontmatter del body
    parts = content.split('---', 2)
    if len(parts) >= 3:
        body = parts[2]
    else:
        body = content

    # Contar palabras
    words = re.findall(r'\b\w+\b', body)
    word_count = len(words)

    # Contar headers H2
    h2_headers = re.findall(r'^##\s+(.+)$', body, flags=re.MULTILINE)
    h2_count = len(h2_headers)

    errors = []
    
    # Regla PRD: Al menos 1200 palabras
    if word_count < 1200:
        errors.append(f"Longitud insuficiente: {word_count} palabras (Se requieren mínimo 1200).")
    
    # Regla PRD: Estructura de cabeceras definida (exigimos al menos 5 para flexibilidad entre nichos, idealmente 7)
    if h2_count < 5:
        errors.append(f"Estructura pobre: {h2_count} headers H2 detectados (Se requieren mínimo 5).")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"   - {err}")
            
        # Cumplimiento del PRD: "Si no cumple, borrar el archivo, y reportar la tarea como fallida pero controlada."
        try:
            os.remove(filepath)
            print(f"   🗑️ Archivo borrado ({filepath}) para evitar 'Ghost Articles / Alucinaciones'.")
        except Exception as e:
            print(f"   ⚠️ No se pudo borrar el archivo: {e}")
            
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validar estructura de artículos MD (Anti-Alucinaciones)")
    parser.add_argument("--file", required=True, help="Ruta al archivo Markdown a validar")
    args = parser.parse_args()
    
    validate_markdown(args.file)
