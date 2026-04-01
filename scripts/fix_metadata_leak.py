import os
import re
import glob

def clean_metadata_leak(content):
    """
    Busca metadatos fugados en el cuerpo del artículo (debajo del frontmatter)
    y los elimina.
    """
    # Separar frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return content, False
    
    frontmatter = parts[1]
    body = parts[2]
    
    # Patrones de metadatos a eliminar del cuerpo
    # Buscamos líneas que empiecen por key: value o similares
    patterns = [
        r'^\s*title\s*:\s*.*$',
        r'^\s*slug\s*:\s*.*$',
        r'^\s*translationKey\s*:\s*.*$',
        r'^\s*language\s*:\s*.*$',
        r'^\s*categories\s*:\s*.*$',
        r'^\s*description\s*:\s*.*$',
        r'^\s*date\s*:\s*.*$',
        r'^#\s*title:.*$',
        r'^#\s*TÍTULO\s*[:].*$',
    ]
    
    lines = body.split('\n')
    new_lines = []
    removed_count = 0
    
    for line in lines:
        is_leak = False
        for pattern in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_leak = True
                break
        
        if is_leak:
            removed_count += 1
            print(f"      [CLEAN] Eliminando línea fugada: {line[:50]}...")
        else:
            new_lines.append(line)
            
    if removed_count > 0:
        new_body = '\n'.join(new_lines)
        return f"---{frontmatter}---{new_body}", True
    
    return content, False

def run():
    print("🚀 Iniciando Limpieza Masiva de Fugas de Metadatos...")
    base_dir = "content"
    md_files = glob.glob(os.path.join(base_dir, "**", "*.md"), recursive=True)
    
    processed = 0
    fixed = 0
    
    for filepath in md_files:
        processed += 1
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except Exception as e:
                print(f"   ❌ Error leyendo {filepath}: {e}")
                continue
                
        new_content, was_fixed = clean_metadata_leak(content)
        
        if was_fixed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            fixed += 1
            print(f"   ✅ Arreglado: {filepath}")
            
    print(f"\n📊 RESUMEN:")
    print(f"   - Archivos procesados: {processed}")
    print(f"   - Archivos corregidos: {fixed}")

if __name__ == "__main__":
    run()
