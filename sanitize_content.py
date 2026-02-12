import os
import re
import frontmatter

CONTENT_DIR = "content"

PATTERNS_TO_REMOVE = [
    r'\*\*TL;DR\s*\(.*?\)\*\*:', 
    r'\*\*TL;DR\*\*:',
    r'TL;DR:',
    r'Key Takeaways:',
    r'Resumen Rápido:',
    r'En resumen:',
    r'\*\*Key Takeaways\*\*:',
    r'As an AI language model',
    r'Como modelo de lenguaje'
]

def sanitize_content():
    print("👨‍⚕️ INICIANDO CIRUGÍA DE CONTENIDO (SANITIZATION)...")
    
    cleaned_count = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content
                title = post.get('title', '').strip()
                
                modified = False
                
                # 1. ELIMINAR TL;DR y HUELLAS IA
                original_content = content
                for pattern in PATTERNS_TO_REMOVE:
                    if re.search(pattern, content, re.IGNORECASE):
                        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                
                # 2. ELIMINAR IMÁGENES DEL BODY
                content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
                
                # 3. LIMPIEZA DE TÍTULO DUPLICADO AL INICIO
                lines = content.strip().split('\n')
                if lines:
                    first_line = lines[0].strip()
                    # Eliminar H1 (# Titulo)
                    if first_line.startswith('# '):
                        lines.pop(0)
                    # Eliminar Titulo repetido
                    elif first_line.lower() == title.lower():
                        lines.pop(0)
                        
                    # Eliminar líneas vacías iniciales
                    while lines and not lines[0].strip():
                        lines.pop(0)
                        
                    content = '\n'.join(lines)

                # Check cambio
                if content != post.content:
                    post.content = content
                    modified = True
                    
                if modified:
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    cleaned_count += 1
                    # print(f"   ✨ Saneado: {filename}")
                    
            except Exception as e:
                print(f"❌ Error saneando {filename}: {e}")

    print(f"\n👨‍⚕️ CIRUGÍA COMPLETADA: {cleaned_count} archivos intervenidos.")

if __name__ == "__main__":
    sanitize_content()
