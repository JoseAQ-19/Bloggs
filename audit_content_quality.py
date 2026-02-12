import os
import re
import frontmatter

CONTENT_DIR = "content"
STATIC_IMAGES_DIR = "static"

# Reglas de Auditoría
MIN_WORDS = 300
FORBIDDEN_PHRASES = [
    "TL;DR", "Key Takeaways", "En resumen", "In conclusion", 
    "As an AI", "Como modelo de lenguaje", "I cannot generate", 
    "September 2021", "Septiembre 2021", "In summary",
    "It is important to note", "Cabe destacar"
]

def check_image_health(rel_path):
    """Retorna True si la imagen es válida y local."""
    if not rel_path: return False
    if "placehold.co" in rel_path: return False
    if rel_path.startswith("http"): return False # Externa no permitida para imagen destacada
    
    phys_path = os.path.join(STATIC_IMAGES_DIR, rel_path.lstrip('/'))
    if not os.path.exists(phys_path): return False
    if os.path.getsize(phys_path) < 50000: return False # < 50KB basura
    
    return True

def audit_quality():
    print("🕵️‍♂️ INICIANDO AUDITORÍA DE CALIDAD ADSENSE...")
    
    total = 0
    passed = 0
    failed = 0
    failures = []
    
    report_file = open("AUDIT_REPORT.txt", "w")
    report_file.write("📊 INFORME DETALLADO DE CALIDAD\n===============================\n\n")

    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            total += 1
            
            try:
                post = frontmatter.load(filepath)
                content = post.content.strip()
                title = post.get('title', 'Sin Título')
                
                errors = []
                
                # TEST 1: Longitud
                word_count = len(content.split())
                if word_count < MIN_WORDS:
                    errors.append(f"Thin Content ({word_count} palabras)")
                
                # TEST 2: Huellas IA
                for phrase in FORBIDDEN_PHRASES:
                    if phrase.lower() in content.lower()[:1000] or phrase.lower() in content.lower()[-1000:]:
                        errors.append(f"Huella IA ('{phrase}')")
                        break # Con una basta
                
                # TEST 3: Imágenes Rotas en Body
                if "![" in content:
                    errors.append("Imagen Incrustada en Texto (Riesgo)")
                
                # TEST 4: Imagen Destacada
                img_ref = post.get('featured_image', '')
                if not check_image_health(img_ref):
                    errors.append(f"Imagen Destacada Rota/Baja Calidad ('{img_ref}')")
                
                # TEST 5: Estructura (Warning como Error para AdSense estricto)
                if "##" not in content:
                    errors.append("Sin Subtítulos H2 (Muro de texto)")
                
                # VEREDICTO
                if errors:
                    failed += 1
                    fail_msg = f"❌ {title[:50]}... -> {', '.join(errors)}"
                    failures.append(fail_msg)
                    report_file.write(f"{fail_msg}\n   File: {filepath}\n\n")
                else:
                    passed += 1
                    report_file.write(f"✅ {title[:50]}... OK\n")
                    
            except Exception as e:
                print(f"Error leyendo {filename}: {e}")

    report_file.close()

    # OUTPUT CONSOLA
    print("\n📊 RESUMEN DE AUDITORÍA:")
    print("-" * 50)
    print(f"✅ APROBADOS (Listos para Indexar): [{passed}] artículos.")
    print(f"❌ RECHAZADOS (Peligro de Baneo): [{failed}] artículos.")
    print("-" * 50)
    
    if failures:
        print("DETALLE DE RECHAZADOS (TOP 10 EJEMPLOS):")
        for i, fail in enumerate(failures[:10]):
            print(f"{i+1}. {fail}")

if __name__ == "__main__":
    audit_quality()
