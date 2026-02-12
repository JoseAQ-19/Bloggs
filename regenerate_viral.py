import os
import frontmatter
import re
from novum_visual import get_image

CONTENT_DIR = "content/viral"
STATIC_IMAGES_ROOT = "static"

def regenerate_viral():
    print("🕶️ INICIANDO OPERACIÓN VIRAL RESCUE...")
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ No existe {CONTENT_DIR}")
        return

    files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    count = 0
    
    for filename in files:
        filepath = os.path.join(CONTENT_DIR, filename)
        
        try:
            post = frontmatter.load(filepath)
            title = post.get('title', 'Untitled')
            
            # --- FASE 1: LIMPIEZA DE FRONTMATTER ---
            # Eliminar type/layout para usar _default (Dark Mode)
            # Aunque el script 'organize' puso type='viral', si queremos forzar _default...
            # Espera, si 'viral' usa 'baseof.html' que tiene inyección de tema 'theme-viral',
            # y hemos arreglado el CSS de theme-viral, DEBERÍA verse oscuro.
            # El problema del fondo blanco era el CSS. Ya lo arreglé en custom.css.
            # Así que NO hace falta borrar el type. 
            # Pero voy a asegurarme de que no haya layout: custom raro.
            
            if 'layout' in post: del post['layout']
            
            # --- FASE 2: REGENERACIÓN VISUAL INTELIGENTE ---
            print(f"   🔄 Regenerando imagen: {title[:40]}...")
            
            slug = filename.replace('.md', '')
            
            # PROMPT ESPECÍFICO BASADO EN TÍTULO
            # Limpiar título de caracteres raros para el prompt
            clean_title = re.sub(r'[^\w\s]', '', title)
            prompt = f"Cinematic shot representing: {clean_title}. Serious tone, dramatic lighting, 8k, realistic."
            
            # Borrar imagen vieja para forzar
            old_img_rel = post.get('featured_image', '').lstrip('/')
            old_img_phys = os.path.join(STATIC_IMAGES_ROOT, old_img_rel)
            if os.path.exists(old_img_phys):
                try: os.remove(old_img_phys)
                except: pass
            
            # Generar
            new_path = get_image(prompt, slug, category="viral")
            
            if new_path:
                post['featured_image'] = new_path
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                print(f"      ✅ Nueva imagen oscura: {new_path}")
                count += 1
            else:
                print("      ❌ Fallo generación.")
                
        except Exception as e:
            print(f"❌ Error en {filename}: {e}")

    print(f"\n🕶️ OPERACIÓN FINALIZADA. {count} artículos virales rescatados.")

if __name__ == "__main__":
    regenerate_viral()
