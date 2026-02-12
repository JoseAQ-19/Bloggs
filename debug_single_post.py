import os
import frontmatter

TITLE_TARGET = "The Unfolding Impact of AI on the American Job Market: Beyond the Hype"
CONTENT_ROOT = "content"
STATIC_ROOT = "static"

def debug_single():
    print(f"🔬 DEBUGGING: '{TITLE_TARGET}'")
    
    found_md = None
    
    # 1. Buscar archivo
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md"): continue
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                if post.get('title') == TITLE_TARGET:
                    found_md = filepath
                    image_ref = post.get('featured_image', 'NO_IMAGE')
                    break
            except:
                pass
        if found_md: break
    
    if not found_md:
        print("❌ Archivo MD no encontrado con ese título exacto.")
        return

    print(f"✅ Archivo MD: {found_md}")
    print(f"📄 Frontmatter featured_image: '{image_ref}'")
    
    # 2. Verificar imagen física
    if not image_ref or "placehold" in image_ref:
        print("❌ La imagen apunta a un placeholder o está vacía.")
        return

    # Normalización de ruta para chequeo físico
    # Hugo usa rutas relativas a 'static'.
    # Si frontmatter dice '/images/foto.jpg', busca en 'static/images/foto.jpg'
    
    clean_ref = image_ref.lstrip('/') 
    phys_path = os.path.join(STATIC_ROOT, clean_ref)
    
    print(f"🔍 Ruta Física Esperada: {phys_path}")
    
    if os.path.exists(phys_path):
        size = os.path.getsize(phys_path)
        print(f"✅ ARCHIVO EXISTE. Peso: {size/1024:.2f} KB")
    else:
        print(f"❌ ARCHIVO NO EXISTE.")
        
        # Búsqueda fuzzy por si el nombre difiere ligeramente
        dir_name = os.path.dirname(phys_path)
        base_name = os.path.basename(phys_path)
        if os.path.exists(dir_name):
            candidates = [f for f in os.listdir(dir_name) if base_name[:10] in f]
            if candidates:
                print(f"   💡 ¿Quizás querías decir?: {candidates}")

if __name__ == "__main__":
    debug_single()
