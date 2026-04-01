import os
import re
import frontmatter

def remove_h1_global():
    print("🧹 ELIMINANDO CABECERAS H1 REDUNDANTES (GLOBAL)...")
    count = 0
    for root, dirs, files in os.walk("content"):
        for filename in files:
            if not filename.endswith(".md"): continue
            filepath = os.path.join(root, filename)
            try:
                post = frontmatter.load(filepath)
                content = post.content
                
                # Regex para eliminar H1 al inicio del texto
                new_content = re.sub(r'^\s*#\s+.*(\n|$)', '', content, count=1).lstrip()
                
                if new_content != content:
                    post.content = new_content
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    print(f"   ✂️ H1 Eliminado en: {filename}")
                    count += 1
            except: pass
    print(f"✨ LIMPIEZA H1 FINALIZADA: {count} archivos corregidos.")

if __name__ == "__main__":
    remove_h1_global()
