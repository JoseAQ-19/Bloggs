import os
import re
import frontmatter

CONTENT_DIR = "content"
REPORT_FILE = "INDEXABILITY_REPORT.txt"

# Criterios
MIN_WORDS = 300
AI_PATTERNS = [
    r"TL;DR", r"Key Takeaways", r"As an AI", r"Como modelo de lenguaje",
    r"En resumen:", r"En conclusión:", r"In summary:", r"In conclusion:"
]
BROKEN_MEDIA = [
    "pollinations", "placehold.co", "![]()"
]

def seo_indexability_scan():
    print("🕷️ INICIANDO OPERACIÓN GOOGLE CRAWLER...")
    
    total = 0
    green = 0
    yellow = 0
    red = 0
    
    blacklist = []
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            total += 1
            
            try:
                post = frontmatter.load(filepath)
                content = post.content.strip()
                title = post.get('title', '')
                desc = post.get('description', '')
                image = post.get('featured_image', '')
                
                issues_crit = []
                issues_warn = []
                
                # 1. Thin Content Test
                word_count = len(content.split())
                if word_count < MIN_WORDS:
                    issues_crit.append(f"Thin Content ({word_count} palabras)")
                
                # 2. AI Footprint Test
                for pattern in AI_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues_crit.append(f"Huella de IA ('{pattern}')")
                        break
                
                # 3. Metadata Test
                if not desc:
                    issues_warn.append("Sin Meta-descripción")
                if len(title) > 70:
                    issues_warn.append(f"Título largo ({len(title)} chars)")
                    
                # 4. Media Test
                if any(x in image for x in BROKEN_MEDIA) or any(x in content for x in BROKEN_MEDIA):
                    issues_crit.append("Media Rota/Placeholder")
                
                # Clasificación
                if issues_crit:
                    red += 1
                    blacklist.append(f"{filepath} -> Motivo: {', '.join(issues_crit + issues_warn)}")
                elif issues_warn:
                    yellow += 1
                else:
                    green += 1
                    
            except Exception as e:
                print(f"❌ Error leyendo {filename}: {e}")

    # Generar Reporte
    report = f"""🕷️ REPORTE DE INDEXABILIDAD DE GOOGLE 🕷️
Total de posts analizados: {total}

✅ ESTADO VERDE (Listos para indexar sin problemas): {green} posts.
🟡 ESTADO AMARILLO (Indexables pero mejorables): {yellow} posts.
🔴 ESTADO ROJO (Peligro de penalización - NO INDEXAR): {red} posts.

📋 LISTA NEGRA (ACCIÓN INMEDIATA REQUERIDA):
"""
    for item in blacklist:
        report += f"1. {item}\n"
        
    with open(REPORT_FILE, "w") as f:
        f.write(report)
        
    print(report)

if __name__ == "__main__":
    seo_indexability_scan()
