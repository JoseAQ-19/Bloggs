import os
import re

CONTENT_ROOT = "content"

def clean_embedded_images():
    print("✂️ INICIANDO LIMPIEZA QUIRÚRGICA DE IMÁGENES INCRUSTADAS...")
    
    count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Regex para eliminar cualquier ![]() que NO sea el Frontmatter (aunque frontmatter no usa esa sintaxis)
                # Eliminamos imagenes Markdown
                clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
                
                # Eliminamos etiquetas HTML img también por si acaso
                clean_content = re.sub(r'<img.*?>', '', clean_content, flags=re.IGNORECASE)
                
                if len(clean_content) != len(content):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(clean_content)
                    print(f"   ✂️ Limpiado: {filename}")
                    count += 1
                    
            except Exception as e:
                print(f"❌ Error en {filename}: {e}")

    print(f"\n✨ LIMPIEZA COMPLETADA: {count} archivos purgados.")

if __name__ == "__main__":
    clean_embedded_images()
