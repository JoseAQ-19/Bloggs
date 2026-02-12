import os
import re
import frontmatter

CONTENT_DIR = "content"

PATTERNS_TO_REMOVE = [
    r'\*\*TL;DR\s*\(.*?\)\*\*:', # **TL;DR (Resumen Rápido)**:
    r'\*\*TL;DR\*\*:',
    r'TL;DR:',
    r'Key Takeaways:',
    r'Resumen Rápido:',
    r'En resumen:',
    r'\*\*Key Takeaways\*\*:'
]

def clean_text():
    print("🧹 INICIANDO LIMPIEZA DE 'RUIDO' IA EN TEXTOS...")
    
    count = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content
                description = post.get('description', '')
                
                modified = False
                
                # Limpiar Cuerpo
                for pattern in PATTERNS_TO_REMOVE:
                    # Usar re.sub con ignorecase
                    if re.search(pattern, content, re.IGNORECASE):
                        content = re.sub(pattern, '', content, count=1, flags=re.IGNORECASE).lstrip()
                        modified = True
                        
                # Limpiar Description (Frontmatter)
                for pattern in PATTERNS_TO_REMOVE:
                    if re.search(pattern, description, re.IGNORECASE):
                        description = re.sub(pattern, '', description, count=1, flags=re.IGNORECASE).lstrip()
                        post['description'] = description
                        modified = True
                
                if modified:
                    post.content = content
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    print(f"   ✨ Limpio: {filename}")
                    count += 1
                    
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n🧹 LIMPIEZA FINALIZADA: {count} archivos pulidos.")

if __name__ == "__main__":
    clean_text()
