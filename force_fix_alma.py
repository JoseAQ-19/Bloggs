import os
import frontmatter
from dotenv import load_dotenv
from novum_visual import get_image

load_dotenv()
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")

TARGET_FILES = [
    "content/fitness/alma-college-kinesiology-hypertrophy-longevity-en.md",
    "content/fitness/kinesiologia-ciencias-salud-alma-college-hipertrofia-longevidad.md",
    "content/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alma-college-en.md",
    "content/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alma-college.md"
]

STATIC_IMAGES = "static"

def force_fix_alma():
    print("☢️ INICIANDO OPERACIÓN NUKE (FUERZA BRUTA) SOBRE ALMA COLLEGE...")
    
    if not TOGETHER_KEY:
        raise Exception("❌ CRÍTICO: No hay TOGETHER_API_KEY. Abortando misión.")

    for filepath in TARGET_FILES:
        if not os.path.exists(filepath):
            print(f"⚠️ Archivo no encontrado: {filepath}")
            continue
            
        print(f"\n🔨 Procesando: {os.path.basename(filepath)}")
        
        # 1. PURGA DE TEXTO ABSOLUTA
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        original_len = len(raw_content)
        
        # Reemplazo Brutal (String Replace)
        # Atacamos todas las variantes posibles en Frontmatter y Body
        clean_content = raw_content.replace("**TL;DR (Key Takeaways):**", "") \
                                   .replace("**TL;DR:**", "") \
                                   .replace("TL;DR:", "") \
                                   .replace("TL;DR", "") \
                                   .replace("Key Takeaways:", "")
                                   
        # Limpieza de espacios dobles resultantes
        clean_content = clean_content.replace("\n\n\n", "\n\n")
        
        if len(clean_content) != original_len:
            print(f"   ✂️ Texto purgado (-{original_len - len(clean_content)} chars)")
        
        # 2. REGENERACIÓN DE IMAGEN OBLIGATORIA
        # Parseamos para sacar el slug de la imagen
        try:
            post = frontmatter.loads(clean_content)
            img_rel = post.get('featured_image', '')
            
            if not img_rel:
                raise Exception(f"❌ El post {filepath} no tiene featured_image definida.")
                
            img_phys = os.path.join(STATIC_IMAGES, img_rel.lstrip('/'))
            
            # Borrado Físico Previo
            if os.path.exists(img_phys):
                os.remove(img_phys)
                print(f"   🗑️ Imagen anterior eliminada: {img_phys}")
            
            # Prompt Específico
            prompt = "Cinematic, highly detailed, realistic photo of a college student doing kinesiology fitness training in a high-end gym, hyperrealistic, 8k"
            slug = os.path.basename(img_rel).replace('.jpg', '')
            
            print(f"   🎨 Generando FLUX (Tolerancia Cero)...")
            
            # Llamada directa al motor
            # get_image maneja la llamada a Together y guarda el archivo
            # Si falla, devuelve None o ruta placeholder
            new_path = get_image(prompt, slug, category="fitness")
            
            # Verificación Paranoica
            final_phys_path = os.path.join(STATIC_IMAGES, new_path.lstrip('/'))
            if not os.path.exists(final_phys_path):
                raise Exception(f"❌ FATAL: La imagen no se generó físicamente en {final_phys_path}")
            
            if os.path.getsize(final_phys_path) < 100000:
                 raise Exception(f"❌ FATAL: La imagen generada es demasiado pequeña ({os.path.getsize(final_phys_path)} bytes). Es basura.")
                 
            print(f"   ✅ Imagen regenerada correctamente ({os.path.getsize(final_phys_path)/1024:.1f} KB)")
            
            # Guardado final del texto limpio
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(clean_content)
                
        except Exception as e:
            print(f"❌ ERROR CRÍTICO PROCESANDO {filepath}")
            raise e # Detener ejecución inmediatamente

    print("\n☢️ OPERACIÓN NUKE COMPLETADA CON ÉXITO.")

if __name__ == "__main__":
    force_fix_alma()
