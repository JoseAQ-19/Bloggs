import os
import re
import frontmatter

CONTENT_DIR = "content"
AI_FOOTPRINTS = [
    "en conclusión", "en resumen", "in conclusion", "in summary", 
    "este artículo explorará", "this article will explore", 
    "recuerda que", "remember that", "cabe destacar", "it is worth noting"
]

def seo_audit():
    print("🔎 INICIANDO AUDITORÍA SEO TÉCNICA (GOOGLE FRIENDLY)...")
    
    total_files = 0
    passed = 0
    failed = 0
    warnings = 0
    
    report_lines = []
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            if filename.startswith("_index"): continue
            
            total_files += 1
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content.strip()
                words = len(content.split())
                
                # Check 1: Longitud
                status_len = "🟢"
                if words < 350: status_len = "🔴"
                elif words < 600: status_len = "🟡"
                
                # Check 2: Metadatos
                has_desc = post.get('description') or post.get('summary')
                status_meta = "🟢" if has_desc else "🔴"
                
                # Check 3: Estructura
                has_h1_in_body = re.search(r'^#\s+', content, re.MULTILINE)
                has_h2 = '##' in content
                status_struct = "🟢"
                if has_h1_in_body: status_struct = "🔴 (H1 Duplicado)"
                elif not has_h2: status_struct = "🔴 (Sin H2)"
                
                # Check 4: AI Footprints
                ai_detected = []
                for phrase in AI_FOOTPRINTS:
                    if phrase.lower() in content.lower()[:500] or phrase.lower() in content.lower()[-500:]:
                        ai_detected.append(phrase)
                status_ai = "🟢" if not ai_detected else f"🟡 ({', '.join(ai_detected)})"
                
                # Evaluar Resultado General
                is_failed = "🔴" in [status_len, status_meta, status_struct]
                is_warning = "🟡" in [status_len, status_ai] and not is_failed
                
                if is_failed:
                    failed += 1
                    report_lines.append(f"🔴 {filename}")
                    if status_len == "🔴": report_lines.append(f"   - Thin Content: {words} palabras")
                    if status_meta == "🔴": report_lines.append(f"   - Falta Descripción")
                    if "🔴" in status_struct: report_lines.append(f"   - Estructura: {status_struct}")
                elif is_warning:
                    warnings += 1
                    # Opcional: mostrar warnings si se quiere detalle
                    # report_lines.append(f"🟡 {filename} - {status_ai} - {words} words")
                    pass
                else:
                    passed += 1
                    
            except Exception as e:
                print(f"❌ Error leyendo {filename}: {e}")

    print(f"\n📊 RESUMEN FINAL:")
    print(f"   Total Artículos: {total_files}")
    print(f"   🟢 VERDES (Listos): {passed}")
    print(f"   🟡 AMARILLOS (Revisables): {warnings}")
    print(f"   🔴 ROJOS (Bloqueantes): {failed}")
    
    if failed > 0:
        print("\n🚨 DETALLE DE ERRORES CRÍTICOS:")
        for line in report_lines:
            print(line)
    else:
        print("\n✨ ¡CATÁLOGO LIMPIO! Todo listo para Google.")

if __name__ == "__main__":
    seo_audit()
