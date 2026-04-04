import os
import re

directories_to_scan = [
    r'c:\Users\usuario\Bloggs\content',
    r'c:\Users\usuario\Bloggs\scripts'
]

def clean_tldr(content):
    # Fix explicit headers
    content = re.sub(r'##\s*Resumen Ejecutivo\s*[-–]?\s*\(?TL;DR\)?', '## Resumen Ejecutivo', content, flags=re.IGNORECASE)
    content = re.sub(r'##\s*Executive Summary\s*[-–]?\s*\(?TL;DR\)?', '## Executive Summary', content, flags=re.IGNORECASE)
    
    # Fix mentions in prompts or text (with or without '##')
    content = re.sub(r'Resumen Ejecutivo\s*[-–]?\s*\(?TL;DR\)?', 'Resumen Ejecutivo', content, flags=re.IGNORECASE)
    content = re.sub(r'Executive Summary\s*[-–]?\s*\(?TL;DR\)?', 'Executive Summary', content, flags=re.IGNORECASE)
    
    # Catch stray (TL;DR) or - TL;DR without the "Executive Summary" prefix but in contexts
    # Actually, the user asked to specifically:
    # "Busca cualquier variación de encabezados como ## Resumen Ejecutivo (TL;DR) o ## Resumen Ejecutivo - TL;DR (y sus versiones en inglés como Executive Summary (TL;DR))."
    # "Reemplázalos estrictamente por un sobrio y profesional ## Resumen Ejecutivo (para español) y ## Executive Summary (para inglés)."
    # "Elimina cualquier instrucción que obligue a la IA o a Python a escribir "(TL;DR)"."
    
    # Optional: strip just "(TL;DR)" strictly when it stands alone if needed, but the above rules cover the requested cases perfectly.
    return content

changed_files = 0
for directory in directories_to_scan:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md') or file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = clean_tldr(content)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed: {file_path}")
                        changed_files += 1
                except Exception as e:
                    print(f"Error reading/writing {file_path}: {e}")

print(f"\nTotal files updated: {changed_files}")
