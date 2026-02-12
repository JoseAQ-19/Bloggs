import os
import re
import frontmatter

CONTENT_DIR = "content"
# Patrones agresivos para eliminar cualquier variante de TL;DR
PATTERNS = [
    r'\*\*?TL;?DR.*?\*\*?:?', 
    r'\*\*?Key Takeaways.*?\*\*?:?',
    r'\*\*?Resumen Rápido.*?\*\*?:?',
    r'^TL;DR',
    r'^Key Takeaways'
]

def force_sanitize():
    print("🧼 SANITIZACIÓN AGRESIVA DE HUELLAS IA...")
    count = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content
                original = content
                
                # 1. Eliminar TL;DR (Case insensitive, multiline)
                for p in PATTERNS:
                    content = re.sub(p, '', content, flags=re.IGNORECASE | re.MULTILINE)
                
                # 2. Limpiar líneas vacías iniciales resultantes
                content = content.lstrip()
                
                if content != original:
                    post.content = content
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    count += 1
                    # print(f"   ✨ Limpiado: {filename}")
                    
            except:
                pass
                
    print(f"✨ SANITIZACIÓN FINALIZADA: {count} archivos limpiados.")

if __name__ == "__main__":
    force_sanitize()
