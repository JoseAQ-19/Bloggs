
import os
import glob
import re
import frontmatter
from datetime import datetime
import sys

# Add scripts directory to path to import generation logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from content_engine_pro import generate_footer, detect_language_context

def aggressive_cleanup():
    content_dir = 'content'
    files = glob.glob(f'{content_dir}/**/*.md', recursive=True)
    
    # Phrases that indicate AI fluff at the end of the article
    ai_trash_patterns = [
        r"(?i)en conclusión.*",
        r"(?i)en resumen.*",
        r"(?i)el rápido desarrollo de.*",
        r"(?i)stay tuned.*",
        r"(?i)visto lo visto.*",
        r"(?i)para terminar.*",
        r"(?i)resumiendo.*",
        r"(?i)in conclusion.*",
        r"(?i)summary:.*",
        r"(?i)conclusion:.*",
        r"(?i)the rapid development of.*",
        r"(?i)in summary.*",
        r"(?i)lastly.*",
        r"(?i)finally.*",
        r"(?i)overall.*",
        r"(?i)llegados a este punto.*",
        r"(?i)como hemos visto.*",
        r"(?i)as we have seen.*"
    ]
    
    # Markers that indicate the start of segments we want to REPLACE or REMOVE to clean AI footprint
    footer_markers = [
        "## Metodología", "## Methodology", 
        "## Fuentes", "## Sources",
        "## Artículos Relacionados", "## Related Articles",
        "*Aviso Editorial", "*Editorial Disclosure",
        "Aviso Editorial:", "Editorial Disclosure:",
        "## Nuestra Opinión", "## Our Opinion",
        "## Preguntas Frecuentes", "## FAQ", "## Frequently Asked Questions"
    ]

    count = 0
    for filepath in files:
        if os.path.basename(filepath).startswith('_index'):
            continue
            
        print(f"🧹 Procesando: {filepath}")
        try:
            post = frontmatter.load(filepath)
            body = post.content
            
            # 1. Identify where the footer starts to strip it
            cut_index = len(body)
            for marker in footer_markers:
                idx = body.find(marker)
                if idx != -1 and idx < cut_index:
                    cut_index = idx
            
            clean_body = body[:cut_index].strip()
            
            # 2. AI Footprint Removal (check last two paragraphs of the clean body)
            paragraphs = clean_body.split('\n\n')
            for _ in range(2):
                if not paragraphs:
                    break
                last_p = paragraphs[-1].strip()
                matches_trash = False
                for pattern in ai_trash_patterns:
                    # Match only if the paragraph STARTS with or is mostly the pattern
                    if re.match(pattern, last_p):
                        matches_trash = True
                        break
                
                if matches_trash:
                    print(f"   🗑️ Eliminando párrafo IA: '{last_p[:50]}...'")
                    paragraphs.pop()
                else:
                    break
            
            clean_body = '\n\n'.join(paragraphs).strip()
            
            # --- 3. RE-INJECT FOOTER & DISCLOSURES ---
            lang_context = detect_language_context(filepath)
            folder_lang = "es" if "es" in lang_context.lower() or "spanish" in lang_context.lower() else "en"
            
            # Detect niche from path for Related Articles
            normalized_path = filepath.lower().replace("\\", "/")
            parts = normalized_path.split("/")
            niche = "ia"
            if "content" in parts:
                p_idx = parts.index("content")
                if len(parts) > p_idx + 2:
                    niche = parts[p_idx+2]
            
            footer = generate_footer(niche, lang_context, post.get('slug', ''))
            
            # 4. YMYL Keyword Scan (Health/Finance)
            full_content_lower = (clean_body + post.get('title', '')).lower()
            is_health = any(h in normalized_path for h in ['fitness', 'salud', 'health']) or any(h in full_content_lower for h in ['salud mental', 'mental health', 'médico', 'médica'])
            is_finance = any(f in normalized_path for f in ['crypto', 'funds', 'realestate', 'finance']) or any(f in full_content_lower for f in ['inversión', 'investment', 'criptomonedas', 'cryptocurrency'])
            
            if is_health:
                final_disclaimer = "\n\n*Aviso Editorial: El contenido de este artículo es informativo y no sustituye el consejo, diagnóstico o tratamiento médico profesional. Consulte siempre a un especialista antes de tomar decisiones sobre su salud.*" if folder_lang == "es" else "\n\n*Editorial Disclosure: The content of this article is for informational purposes and does not replace professional medical advice, diagnosis, or treatment. Always consult a specialist before making health decisions.*"
            elif is_finance:
                final_disclaimer = "\n\n*Aviso Editorial: Este artículo tiene fines informativos y educativos. No constituye asesoramiento financiero ni recomendación de inversión. Las decisiones basadas en esta información son responsabilidad exclusiva del lector.*" if folder_lang == "es" else "\n\n*Editorial Disclosure: This article is for informational and educational purposes. It does not constitute financial advice or an investment recommendation. Decisions based on this information are the sole responsibility of the reader.*"
            else:
                final_disclaimer = "\n\n*Aviso Editorial: Este contenido es para fines informativos y educativos. No constituye asesoramiento profesional. NovumWorld recomienda consultar con un experto certificado en la materia.*" if folder_lang == "es" else "\n\n*Editorial Disclosure: This content is for informational and educational purposes only. It does not constitute professional advice. NovumWorld recommends consulting with a certified expert in the field.*"

            # 5. English Leak fix
            if "/en/" in normalized_path:
                clean_body = clean_body.replace("Metodología y Fuentes", "Methodology and Sources")
                clean_body = clean_body.replace("Artículos Relacionados", "Related Articles")
                clean_body = clean_body.replace("Aviso Editorial", "Editorial Disclosure")

            post.content = clean_body + footer + final_disclaimer
            
            # Update metadata trace
            post['author'] = "NovumWorld Editorial Team"
            post['quality_tier'] = "fenix_v3_pro_sanitized"
            post['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            
            with open(filepath, 'wb') as f:
                frontmatter.dump(post, f)
            count += 1
            
        except Exception as e:
            print(f"   ❌ Error en {filepath}: {e}")

    print(f"\n✨ Saneamiento Agresivo completado. {count} archivos procesados.")

if __name__ == "__main__":
    aggressive_cleanup()
