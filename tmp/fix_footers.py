import sys
import glob
import random
import frontmatter
import os

def generate_footer(niche, lang, current_slug=""):
    # 1. Metodología
    meth_es = "\n\n## Metodología y Fuentes\nEste artículo fue analizado y validado por el equipo de investigadores de NovumWorld. Los datos provienen estrictamente de métricas actualizadas, regulaciones institucionales y canales de análisis autorizados para asegurar que el contenido cumpla con el estándar más alto de calidad y autoridad (E-E-A-T) de la industria."
    meth_en = "\n\n## Methodology and Sources\nThis article was analyzed and validated by the NovumWorld research team. The data strictly originates from updated metrics, institutional regulations, and authoritative analytical channels to ensure the content meets the industry's highest quality and authority standard (E-E-A-T)."
    methodology = meth_es if "es" in lang.lower() or "spanish" in lang.lower() else meth_en
    
    # 2. Artículos relacionados
    rel_es = "\n\n## Artículos Relacionados\n"
    rel_en = "\n\n## Related Articles\n"
    related_header = rel_es if "es" in lang.lower() or "spanish" in lang.lower() else rel_en
    
    folder_lang = "es" if "es" in lang.lower() or "spanish" in lang.lower() else "en"
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
        except Exception as e:
            pass
            
    random.shuffle(candidates)
    selected = candidates[:3]
    
    links_text = ""
    for title, slug in selected:
        links_text += f"- [{title}](/{folder_lang}/{niche}/{slug}/)\n"
        
    if not links_text:
        links_text = "- [Explora nuestra sección completa](/) \n"
        
    related = related_header + links_text
    
    # 3. YMYL Disclaimer
    d_finanzas_es = "\n\n*Aviso Editorial: Este artículo tiene fines informativos y educativos. No constituye asesoramiento financiero ni recomendación de inversión. Las decisiones basadas en esta información son responsabilidad exclusiva del lector.*"
    d_salud_es = "\n\n*Aviso Editorial: El contenido de este artículo es informativo y no sustituye el consejo, diagnóstico o tratamiento médico profesional. Consulte siempre a un especialista antes de tomar decisiones sobre su salud.*"
    d_general_es = "\n\n*Aviso Editorial: Este contenido es solo para fines educativos e informativos. No constituye asesoramiento profesional financiero, legal o médico. NovumWorld recomienda consultar con un especialista certificado.*"
    
    d_finanzas_en = "\n\n*Editorial Disclosure: This article is for informational and educational purposes. It does not constitute financial advice or an investment recommendation. Decisions based on this information are the sole responsibility of the reader.*"
    d_salud_en = "\n\n*Editorial Disclosure: The content of this article is informational and does not replace professional medical advice, diagnosis, or treatment. Always consult a specialist before making health decisions.*"
    d_general_en = "\n\n*Editorial Disclosure: This content is for educational and informational purposes only. It does not constitute professional financial, legal, or medical advice. NovumWorld recommends consulting with a certified specialist.*"
    
    if niche in ["crypto", "funds", "realestate"]:
        disclaimer = d_finanzas_es if "es" in lang.lower() or "spanish" in lang.lower() else d_finanzas_en
    elif niche in ["fitness"]:
        disclaimer = d_salud_es if "es" in lang.lower() or "spanish" in lang.lower() else d_salud_en
    else:
        disclaimer = d_general_es if "es" in lang.lower() or "spanish" in lang.lower() else d_general_en
        
    return methodology + related + disclaimer + "\n"

def fix_file(f, niche, lang):
    p = frontmatter.load(f)
    print("Fixing:", f)
    f_text = generate_footer(niche, lang, p.get('slug', ''))
    p.content += f_text
    with open(f, 'wb') as file:
        frontmatter.dump(p, file)

fix_file('c:\\Users\\usuario\\Bloggs\\content\\es\\viral\\masterchef-dubai-polemica-fiscal.md', 'viral', 'es')
fix_file('c:\\Users\\usuario\\Bloggs\\content\\es\\youtube\\youtube-y-fifa-un-acuerdo-que-cambiara-la-forma-de-ver-el-mundial-2026.md', 'youtube', 'es')
