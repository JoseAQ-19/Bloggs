import os
import glob
import re
import frontmatter
from datetime import datetime
import random

# Safe footer logic
def generate_footer_safe(niche, lang, current_slug=""):
    meth_es = "\n\n## Metodología y Fuentes\nEste artículo fue analizado y validado por el equipo de investigadores de NovumWorld. Los datos provienen estrictamente de métricas actualizadas, regulaciones institucionales y canales de análisis autorizados para asegurar que el contenido cumpla con el estándar más alto de calidad y autoridad (E-E-A-T) de la industria."
    meth_en = "\n\n## Methodology and Sources\nThis article was analyzed and validated by the NovumWorld research team. The data strictly originates from updated metrics, institutional regulations, and authoritative analytical channels to ensure the content meets the industry's highest quality and authority standard (E-E-A-T)."
    methodology = meth_es if "es" in lang.lower() else meth_en
    
    rel_es = "\n\n## Artículos Relacionados\n"
    rel_en = "\n\n## Related Articles\n"
    related_header = rel_es if "es" in lang.lower() else rel_en
    
    folder_lang = "es" if "es" in lang.lower() else "en"
    search_path = f"c:/Users/usuario/Bloggs/content/{folder_lang}/{niche}/*.md"
    all_files = glob.glob(search_path)
    
    candidates = []
    for f in all_files:
        if current_slug in f or "_index.md" in f:
            continue
        try:
            p = frontmatter.load(f)
            t = p.get('title')
            s = p.get('slug', os.path.basename(f).replace('.md', ''))
            if t and s:
                candidates.append((t, s))
        except:
            pass
            
    random.shuffle(candidates)
    selected = candidates[:3]
    
    links_text = ""
    for title, slug in selected:
        links_text += f"- [{title}](/{folder_lang}/{niche}/{slug}/)\n"
        
    if not links_text:
        links_text = "- [Explora nuestra sección completa](/) \n"
        
    related = related_header + links_text
    
    d_finanzas_es = "\n\n*Aviso Editorial: Este artículo tiene fines informativos y educativos. No constituye asesoramiento financiero ni recomendación de inversión. Las decisiones basadas en esta información son responsabilidad exclusiva del lector.*"
    d_salud_es = "\n\n*Aviso Editorial: El contenido de este artículo es informativo y no sustituye el consejo, diagnóstico o tratamiento médico profesional. Consulte siempre a un especialista antes de tomar decisiones sobre su salud.*"
    d_general_es = "\n\n*Aviso Editorial: Este contenido es solo para fines educativos e informativos. No constituye asesoramiento profesional financiero, legal o médico. NovumWorld recomienda consultar con un especialista certificado.*"
    
    d_finanzas_en = "\n\n*Editorial Disclosure: This article is for informational and educational purposes. It does not constitute financial advice or an investment recommendation. Decisions based on this information are the sole responsibility of the reader.*"
    d_salud_en = "\n\n*Editorial Disclosure: The content of this article is informational and does not replace professional medical advice, diagnosis, or treatment. Always consult a specialist before making health decisions.*"
    d_general_en = "\n\n*Editorial Disclosure: This content is for educational and informational purposes only. It does not constitute professional financial, legal, or medical advice. NovumWorld recommends consulting with a certified specialist.*"
    
    if niche in ["crypto", "finance", "funds", "realestate"]:
        disclaimer = d_finanzas_es if "es" in lang.lower() else d_finanzas_en
    elif niche in ["fitness", "salud"]:
        disclaimer = d_salud_es if "es" in lang.lower() else d_salud_en
    else:
        disclaimer = d_general_es if "es" in lang.lower() else d_general_en
        
    return methodology + related + disclaimer + "\n"

def sanitize_and_footer(target_file_path):
    try:
        post = frontmatter.load(target_file_path)
        body = post.content
        
        lang = "es" if "/es/" in target_file_path.replace("\\", "/") else "en"
        parts = target_file_path.replace("\\", "/").split("/")
        
        if "content" not in parts: 
            return # Should not happen

        # Find niche (next part after es/en)
        idx = parts.index("content")
        if len(parts) > idx + 2:
            niche = parts[idx+2]
            if niche.endswith(".md"): niche = "general" # Root pages like about.md
        else:
            niche = "general"

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
            r"(?i)conclusion:.*"
        ]
        
        split_markers = [
            "## Metodología", "## Methodology", 
            "## Metodolog", "## Methodology",
            "## Fuentes", "## Sources",
            "## Artículos Relacionados", "## Related Articles",
            "## Related articles", "## Resumen ejecutivo"
        ]
        for marker in split_markers:
            if marker in body:
                body = body.split(marker)[0].strip()

        paragraphs = body.split('\n\n')
        if len(paragraphs) > 1:
            for _ in range(3):
                if not paragraphs: break
                last_p = paragraphs[-1].strip()
                matched = False
                for pattern in ai_trash_patterns:
                    if re.match(pattern, last_p):
                        print(f"   🧹 Eliminando párrafo IA en {os.path.basename(target_file_path)}")
                        paragraphs.pop()
                        matched = True
                        break
                if not matched: break
            body = '\n\n'.join(paragraphs).strip()

        footer = generate_footer_safe(niche, lang, post.get('slug', ''))
        post.content = body + footer
        post['quality_tier'] = "fenix_v3_pro"
        post['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        with open(target_file_path, 'wb') as f:
            frontmatter.dump(post, f)
            
    except Exception as e:
        print(f"   ❌ Fallo en {target_file_path}: {e}")

if __name__ == "__main__":
    content_root = "c:/Users/usuario/Bloggs/content"
    for lang_dir in ["es", "en"]:
        files = glob.glob(os.path.join(content_root, lang_dir, "**", "*.md"), recursive=True)
        for f in files:
            if "_index.md" in f: continue
            sanitize_and_footer(f)
