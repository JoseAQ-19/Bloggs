import os
import shutil
import frontmatter
from novum_visual import get_image

CONTENT_ROOT = "content"
STATIC_ROOT = "static"

def surgery():
    print("🏥 INICIANDO CIRUGÍA DE URGENCIA...")
    
    # --- TAREA 1: LA IA EN FITNESS ---
    wrong_path = "content/es/fitness/la-ia-te-saluda-pero-no-te-salvara-por-que-la-cort.md"
    right_dir = "content/es/ia"
    
    if os.path.exists(wrong_path):
        print("   🔪 Extrayendo post de IA en Fitness...")
        
        post = frontmatter.load(wrong_path)
        
        # Corrección de Metadatos
        post['categories'] = ['ia']
        post['type'] = 'ia'
        title = post.get('title')
        
        # Generar Nueva Imagen Cyberpunk
        print("   🎨 Pintando nueva portada Cyberpunk...")
        new_img = get_image(title, "la-ia-te-saluda-cyberpunk", "ia")
        post['featured_image'] = new_img
        
        # Mover
        filename = os.path.basename(wrong_path)
        dest_path = os.path.join(right_dir, filename)
        
        with open(dest_path, 'wb') as f:
            frontmatter.dump(post, f)
            
        os.remove(wrong_path)
        print(f"   ✅ Trasplante exitoso a: {dest_path}")
    else:
        print("   ⚠️ No se encontró el paciente 'la-ia-te-saluda' en Fitness.")

    # --- TAREA 2: EL POST DE LOS BANCOS (Busca y Repara) ---
    print("   🔎 Buscando post de 'bancos' roto...")
    
    # Lista de sospechosos (basada en grep anterior)
    suspects = [
        "content/es/ia/crisis-la-estafa-del-siglo-como-nos-venden-el-derr.md",
        "content/es/ia/deuda-global-2026-el-subprime-que-nadie-vio-venir.md",
        "content/es/ia/el-capitalismo-zombi-anatomia-de-un-sistema-fallid.md"
    ]
    
    for path in suspects:
        if not os.path.exists(path): continue
        
        post = frontmatter.load(path)
        img_rel = post.get('featured_image', '')
        
        needs_fix = False
        if not img_rel: needs_fix = True
        else:
            phys = os.path.join(STATIC_ROOT, img_rel.lstrip('/'))
            if not os.path.exists(phys) or os.path.getsize(phys) < 50000:
                needs_fix = True
        
        if needs_fix:
            print(f"   🚑 Encontrado paciente crítico: {os.path.basename(path)}")
            title = post.get('title')
            slug = os.path.basename(path).replace('.md', '')
            
            # Generar imagen financiera
            new_img = get_image(title, slug, "crypto") # Usamos estilo crypto/finance
            post['featured_image'] = new_img
            
            with open(path, 'wb') as f:
                frontmatter.dump(post, f)
            print(f"   ✅ Imagen restaurada.")

if __name__ == "__main__":
    surgery()
