import os
import frontmatter

CONTENT_DIRS = [
    'content/ia', 'content/crypto', 'content/fitness', 'content/youtube', 'content/viral'
]

def clean_duplicates():
    print("🧹 INICIANDO LIMPIEZA DE TÍTULOS DUPLICADOS...")
    
    count = 0
    
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        
        print(f"\n📂 Escaneando carpeta: {folder}...")
        files = [f for f in os.listdir(folder) if f.endswith('.md') and not f.startswith('_index')]
        
        for filename in files:
            filepath = os.path.join(folder, filename)
            try:
                post = frontmatter.load(filepath)
                title = post.get('title', '').strip()
                content = post.content.strip()
                
                lines = content.split('\n')
                if not lines: continue
                
                modified = False
                
                # Regla 1: Eliminar H1 (# Titulo)
                if lines[0].strip().startswith('# '):
                    print(f"   ✂️ Eliminando H1 en: {filename}")
                    lines.pop(0)
                    modified = True
                    
                # Regla 2: Eliminar Título Literal (aunque no tenga #)
                # A veces la IA repite el título tal cual
                elif lines[0].strip().lower() == title.lower():
                    print(f"   ✂️ Eliminando Título Repetido en: {filename}")
                    lines.pop(0)
                    modified = True
                    
                # Limpieza de líneas vacías al inicio
                while lines and not lines[0].strip():
                    lines.pop(0)
                    modified = True

                if modified:
                    post.content = '\n'.join(lines)
                    with open(filepath, 'wb') as f:
                        frontmatter.dump(post, f)
                    count += 1
                    
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n✨ LIMPIEZA COMPLETADA: {count} archivos corregidos.")

if __name__ == "__main__":
    clean_duplicates()
