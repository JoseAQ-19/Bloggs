import os
import re
import glob
import shutil

CONTENT_DIR = "content"
STATIC_IMAGES_DIR = "static/images"

def get_base_slug(filename):
    """
    Normaliza el nombre del archivo para agrupar ES y EN.
    Ej: 'articulo-bueno-en.md' -> 'articulo-bueno'
    Ej: 'articulo-bueno.md' -> 'articulo-bueno'
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    if name.endswith("-en"):
        return name[:-3]
    return name

def shorten_name(base_slug):
    """
    Crea un nombre corto y seguro (max 50 chars + extension).
    """
    safe_slug = re.sub(r'[^a-z0-9-]', '', base_slug.lower())
    if len(safe_slug) > 50:
        safe_slug = safe_slug[:50].rstrip('-')
    return f"{safe_slug}.jpg" # Asumimos JPG por estandarización

def main():
    print("🛡️ INICIANDO PROTOCOLO DE REPARACIÓN DE IMÁGENES...")
    
    # 1. Agrupar archivos .md
    groups = {}
    md_files = glob.glob(f"{CONTENT_DIR}/**/*.md", recursive=True)
    
    for md_path in md_files:
        if "_index.md" in md_path: continue
        
        base = get_base_slug(md_path)
        if base not in groups:
            groups[base] = []
        groups[base].append(md_path)
        
    print(f"📊 Detectados {len(groups)} grupos de artículos.")
    
    count_fixed = 0
    
    # 2. Procesar cada grupo
    for base, files in groups.items():
        # Buscar imagen candidata en los archivos
        image_candidates = []
        
        for md_file in files:
            with open(md_file, 'r') as f:
                content = f.read()
                match = re.search(r'featured_image:\s*([^\s]+)', content)
                if match:
                    img_path = match.group(1).strip()
                    # Quitar /images/ o static/images/ para tener nombre archivo
                    img_name = os.path.basename(img_path)
                    candidates = [
                        os.path.join(STATIC_IMAGES_DIR, img_name),
                        # A veces la ruta en MD es absoluta local, probar static directo
                    ]
                    
                    found = False
                    for c in candidates:
                         if os.path.exists(c):
                             image_candidates.append(c)
                             found = True
                             break
        
        if not image_candidates:
            # print(f"⚠️ No hay imágenes físicas para: {base}")
            continue
            
        # Elegir imagen maestra (la primera que exista)
        master_src = image_candidates[0]
        
        # Crear nombre corto
        short_name = shorten_name(base)
        dest_path = os.path.join(STATIC_IMAGES_DIR, short_name)
        
        # Renombrar/Mover
        if master_src != dest_path:
            # Si el destino ya existe (y no es el source), lo sobrescribimos o usamos?
            # Mejor: Si ya existe, asumimos que es correcto y lo usamos.
            if not os.path.exists(dest_path):
                shutil.move(master_src, dest_path)
                print(f"✨ Renombrado: {os.path.basename(master_src)} -> {short_name}")
            else:
                 # Si ya existe, nos aseguramos que master_src no sea left over (si son distintos)
                 if os.path.abspath(master_src) != os.path.abspath(dest_path):
                     # Borramos el viejo largo ya que usaremos el corto existente
                     os.remove(master_src)
                     pass

        # 3. Actualizar TODOS los MD del grupo
        for md_file in files:
            with open(md_file, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            changed = False
            for line in lines:
                if line.strip().startswith("featured_image:"):
                    old_line = line
                    new_line = f"featured_image: /images/{short_name}\n"
                    if old_line != new_line:
                        new_lines.append(new_line)
                        changed = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if changed:
                with open(md_file, 'w') as f:
                    f.writelines(new_lines)
                count_fixed += 1
                
        # 4. Limpieza: Borrar otras imágenes candidatas que NO sean la short_name
        # (Deduplicación real)
        unique_candidates = set(image_candidates)
        for cand in unique_candidates:
            if os.path.exists(cand) and os.path.abspath(cand) != os.path.abspath(dest_path):
                print(f"🗑️ Eliminando duplicado/largo: {os.path.basename(cand)}")
                os.remove(cand)

    print(f"✅ FINALIZADO. {count_fixed} artículos actualizados.")

if __name__ == "__main__":
    main()
