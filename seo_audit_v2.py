import os
import re
import frontmatter

CONTENT_DIR = "content"

AI_FOOTPRINTS = [
    "TL;DR", "Key Takeaways", "En resumen", "In conclusion", 
    "As an AI", "Como modelo de lenguaje"
]

def seo_audit():
    print("🕵️‍♂️ INICIANDO AUDITORÍA SEO Y DETECCIÓN DE HUELLAS IA...")
    
    stats = {
        "ai_footprints": 0,
        "broken_images": 0,
        "missing_desc": 0,
        "long_title": 0
    }
    
    count = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            count += 1
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content
                title = post.get('title', '')
                desc = post.get('description', '')
                
                # 1. Huellas IA
                for footprint in AI_FOOTPRINTS:
                    if footprint.lower() in content.lower()[:500]: # Check intro
                        # print(f"   🤖 Huella IA en {filename}: {footprint}")
                        stats["ai_footprints"] += 1
                        break
                        
                # 2. Imágenes Rotos en Body
                if "![" in content:
                    # print(f"   🖼️ Imagen en body detectada: {filename}")
                    stats["broken_images"] += 1
                    
                # 3. Metadatos
                if not desc:
                    stats["missing_desc"] += 1
                
                if len(title) > 70:
                    stats["long_title"] += 1
                    
            except Exception as e:
                print(f"❌ Error leyendo {filename}: {e}")

    print("\n📊 REPORTE DE CALIDAD:")
    print(f"   Total Artículos: {count}")
    print(f"   🤖 Huellas IA (TL;DR, etc.): {stats['ai_footprints']}")
    print(f"   🖼️ Imágenes en Texto (Riesgo): {stats['broken_images']}")
    print(f"   📝 Sin Descripción SEO: {stats['missing_desc']}")
    print(f"   📏 Títulos Largos (>70 chars): {stats['long_title']}")

if __name__ == "__main__":
    seo_audit()
