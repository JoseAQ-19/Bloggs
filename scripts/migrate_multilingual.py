import os
import shutil

CONTENT_ROOT = "content"
LANGS = ["es", "en"]
CATEGORIES = ["ia", "crypto", "fitness", "youtube", "viral", "tools"]

def migrate_multilingual():
    print("🧱 INICIANDO MIGRACIÓN A ESTRUCTURA BILINGÜE ESTRICTA...")
    
    # 1. Crear estructura destino
    for lang in LANGS:
        for cat in CATEGORIES:
            os.makedirs(os.path.join(CONTENT_ROOT, lang, cat), exist_ok=True)
            
    # 2. Mover Archivos
    # Recorremos la estructura antigua (que es content/[categoria]/file.md)
    # CUIDADO: os.walk verá las nuevas carpetas también. Filtremos.
    
    # Lista de archivos a mover antes de iterar para no confundirnos
    moves = []
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        # Ignorar las nuevas carpetas 'es' y 'en' si ya existen
        if "content/es" in root or "content/en" in root: continue
        
        category = os.path.basename(root)
        if category not in CATEGORIES and category != "content": continue
        
        for filename in files:
            if not filename.endswith(".md"): continue
            
            src_path = os.path.join(root, filename)
            
            # Detectar idioma
            if filename.endswith("-en.md") or filename == "option-1-benefit-focused.md": # Casos conocidos EN
                target_lang = "en"
                # Limpiar el sufijo '-en' del nombre final si queremos URLs limpias? 
                # Mejor mantenerlo por ahora para no romper links internos
            else:
                target_lang = "es"
                
            # Destino
            if category == "content": # Páginas estáticas en raíz (about, contact...)
                # Estas van a la raíz de content/es y content/en
                # Pero Hugo espera content/es/about.md
                target_folder = os.path.join(CONTENT_ROOT, target_lang)
            else:
                target_folder = os.path.join(CONTENT_ROOT, target_lang, category)
                
            dest_path = os.path.join(target_folder, filename)
            moves.append((src_path, dest_path))

    # Ejecutar movimientos
    for src, dest in moves:
        try:
            # Asegurar dir
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)
            print(f"📦 Movido: {os.path.basename(src)} -> {dest}")
        except Exception as e:
            print(f"❌ Error moviendo {src}: {e}")

    # 3. Duplicar _index.md y estáticos base si faltan en EN
    # (Como movemos todo, los _index se habrán movido a ES o EN según nombre, 
    # pero _index.md no tiene sufijo -en. Se habrán ido todos a ES).
    # Necesitamos copiar los _index de ES a EN.
    
    print("📋 Duplicando Estructura Base (Índices)...")
    for cat in CATEGORIES:
        src_index = os.path.join(CONTENT_ROOT, "es", cat, "_index.md")
        dest_index = os.path.join(CONTENT_ROOT, "en", cat, "_index.md")
        
        if os.path.exists(src_index) and not os.path.exists(dest_index):
            shutil.copy(src_index, dest_index)
            print(f"   ➕ Creado índice EN: {cat}")

    # 4. Limpieza de carpetas vacías antiguas
    for cat in CATEGORIES:
        old_dir = os.path.join(CONTENT_ROOT, cat)
        try:
            if os.path.exists(old_dir) and not os.listdir(old_dir):
                os.rmdir(old_dir)
                print(f"   🗑️ Carpeta vacía eliminada: {old_dir}")
        except: pass

    print("🧱 MIGRACIÓN COMPLETADA.")

if __name__ == "__main__":
    migrate_multilingual()
