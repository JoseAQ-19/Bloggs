
import os
import json
import re
import frontmatter
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from prompts_factory import PromptFactory
from llm_router import LLMRouter
from novum_visual import get_image
import glob
import json

# --- CONFIGURACIÓN & SETUP ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("❌ ERROR CRÍTICO: No se encontró GEMINI_API_KEY en .env")
    exit(1)

genai.configure(api_key=GEMINI_KEY)

# --- PROTOCOLO DE EXCELENCIA (CONSTANTES) ---

# 1. Negative Constraints (Lo que la IA tiene PROHIBIDO)
BANNED_PHRASES = [
    "Here is the rewritten article", "Aquí está el artículo reescrito",
    "I hope this helps", "Espero que esto ayude",
    "In conclusion", "En conclusión", 
    "Verdict:", "Veredicto:",
    "Introduction:", "Introducción:", # Queremos que el texto fluya, no etiquetas
    "Title:", "Título:"
]

# 2. System Prompt de Alta Ingeniería (Centralizado)
def get_pro_prompt(niche, lang):
    """Obtiene el prompt maestro desde la factoría central."""
    # Normalizar idioma para PromptFactory
    pf_lang = "es" if "spanish" in lang.lower() else "en"
    base_prompt = PromptFactory.get_system_prompt(niche, pf_lang)
    # Refuerzo para forzar JSON
    json_instruction = """
    
    ### OUTPUT FORMAT:
    You must return a VALID JSON object. Do NOT include markdown code blocks (```json).
    Structure:
    {
      "title": "Optimized SEO Title",
      "h1_title": "Visual H1 Title",
      "meta_description": "SEO description (150 chars)",
      "content_body": "Full body following 'Obra Maestra' rules (Executive Summary, no emojis, sources header, natural links)."
    }
    """
    return base_prompt + json_instruction

def detect_language_context(file_path):
    """Determina el idioma estricto basado en la carpeta."""
    if "/en/" in file_path: return "English (US)"
    if "/es/" in file_path: return "Spanish (Spain)"
    return "English" # Default

def validate_content(content, language):
    """Filtro de Calidad Automático (Linter)."""
    
    # 1. Check for Banned Phrases
    for phrase in BANNED_PHRASES:
        if phrase.lower() in content.lower():
            print(f"   ⚠️ ALERTA: Frase prohibida detectada '{phrase}'. Limpiando...")
            content = re.sub(phrase, "", content, flags=re.IGNORECASE)

    # 2. Language Validation (Heuristic)
    if language == "English (US)":
        if re.search(r"##\s*[¿¡]", content): # Spanish headers check
            print("   ⚠️ ALERTA CRÍTICA: Detectados headers en Español dentro de contenido Inglés.")
            return None # Reject content
            
    return content.strip()

def generate_article_pro(current_content, context_data, target_language, niche="ia"):
    """Genera el contenido usando LLMRouter (Capa Cero -> Fallback)."""
    
    # 1. Preparar Prompts
    system_prompt = get_pro_prompt(niche, target_language)
    user_prompt = f"""
    CONTEXT DATA:
    {context_data}

    CURRENT CONTENT (IF ANY):
    {current_content[:2000]}

    TASK: Rewrite and expand into a premium 'Obra Maestra' article in {target_language}.
    Follow all SYSTEM RULES strictly.
    """

    # 2. Definir Fallback (Gemini API directa)
    def fallback_gemini(p, s):
        print("      [FALLBACK] Usando Gemini Flash (Directo)...")
        try:
            model = genai.GenerativeModel(
                model_name="models/gemini-flash-latest",
                system_instruction=s,
                generation_config={
                    "response_mime_type": "application/json",
                    "max_output_tokens": 8192,
                    "temperature": 1.0
                }
            )
            response = model.generate_content(p)
            return response.text.strip()
        except Exception as e:
            import traceback
            print(f"      [ERROR FALLBACK] {e}")
            traceback.print_exc()
            return None

    # 3. Ejecutar vía Router
    try:
        raw_result = LLMRouter.route_call(user_prompt, system_prompt, fallback_gemini, model_type="reasoning")
        
        if not raw_result:
            return None
            
        # Limpieza de markdown redundante si el modelo no obedeció el JSON puro
        if "```json" in raw_result:
            raw_result = raw_result.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_result:
             raw_result = raw_result.split("```")[1].split("```")[0].strip()
        
        # Validar si es JSON
        try:
            return json.loads(raw_result)
        except:
            # Si falla el parseo, intentar una limpieza agresiva de caracteres no-JSON al inicio/final
            start = raw_result.find('{')
            end = raw_result.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(raw_result[start:end])
            raise
            
    except Exception as e:
        print(f"   ❌ Error en generación IA (Router): {e}")
        return None


import random

def generate_footer(niche, lang, current_slug=""):
    """Inyecta el Footer Blindado determinista."""
    # 1. Metodología
    meth_es = "\n\n## Metodología y Fuentes\nEste artículo fue analizado y validado por el equipo de investigadores de NovumWorld. Los datos provienen estrictamente de métricas actualizadas, regulaciones institucionales y canales de análisis autorizados para asegurar que el contenido cumpla con el estándar más alto de calidad y autoridad (E-E-A-T) de la industria."
    meth_en = "\n\n## Methodology and Sources\nThis article was analyzed and validated by the NovumWorld research team. The data strictly originates from updated metrics, institutional regulations, and authoritative analytical channels to ensure the content meets the industry's highest quality and authority standard (E-E-A-T)."
    methodology = meth_es if "es" in lang.lower() or "spanish" in lang.lower() else meth_en
    
    # 2. Artículos relacionados
    rel_es = "\n\n## Artículos Relacionados\n"
    rel_en = "\n\n## Related Articles\n"
    related_header = rel_es if "es" in lang.lower() or "spanish" in lang.lower() else rel_en
    
    folder_lang = "es" if "es" in lang.lower() or "spanish" in lang.lower() else "en"
    search_path = f"content/{folder_lang}/{niche}/*.md"
    all_files = glob.glob(search_path)
    
    candidates = []
    for f in all_files:
        if current_slug in f or "_index.md" in f:
            continue
        try:
            p = frontmatter.load(f)
            t = p.get('title')
            s = p.get('slug')
            if t and s:
                candidates.append((t, s))
        except:
            pass
            
    # Take up to 3 random or recent
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

def main_upgrade_engine(target_file_path):
    """Función principal para actualizar un archivo individual."""
    
    if not os.path.exists(target_file_path):
        print("Archivo no encontrado.")
        return

    print(f"🚀 Procesando: {os.path.basename(target_file_path)}")
    
    # 1. Detectar Contexto e Idioma
    lang = detect_language_context(target_file_path)
    
    # Detectar Nicho desde el path (Hijo de content/)
    parts = target_file_path.replace("\\", "/").split("/")
    niche = "ia"
    try:
        # Expected: content/es/fitness/post.md
        if "content" in parts:
            idx = parts.index("content")
            niche = parts[idx+2] 
    except:
        pass

    post = frontmatter.load(target_file_path)
    current_body = post.content
    
    # 2. Generar con nicho correcto
    result_json = generate_article_pro(current_body, post.get('title', 'Unknown Topic'), lang, niche=niche)
    
    if not result_json:
        print("   ❌ Fallo en generación. Saltando.")
        return

    # 3. Validar
    cleaned_body = validate_content(result_json['content_body'], lang)
    if cleaned_body:
        from utils import ContentCleaner
        cleaned_body = ContentCleaner.sanitize_body(cleaned_body)
        
    if not cleaned_body:
        print("   ❌ El contenido no pasó el filtro de calidad (Linter).")
        return

    
    # --- FOOTER BLINDADO ---
    footer_text = generate_footer(niche, lang, post.get('slug', ''))
    cleaned_body += footer_text
    
    # 4. Actualizar Metadatos Masterpiece
    post.content = cleaned_body
    post['title'] = result_json['title'] # SEO Title updated
    post['description'] = result_json['meta_description']
    post['quality_tier'] = "fenix_v3_pro" # Marca de calidad nueva
    post['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    # 5. Lógica de Imagen (Regenerar si no existe o es básica)
    img_path = post.get('featured_image', '')
    img_exists = False
    if img_path and img_path.startswith('/images/'):
         # Check if file exists in root static/images — lstrip images to match static/images/
         img_subpath = img_path.replace('/images/', '')
         full_img_path = os.path.join(os.getcwd(), 'static', 'images', img_subpath)
         if os.path.exists(full_img_path):
             img_exists = True

    if not img_exists:
        print(f"   🖼️ Regenerando imagen: {post.get('slug', 'unknown')}")
        new_img = get_image(post.get('title', 'Unknown Topic'), cleaned_body, post.get('slug', 'unknown'), category=niche)
        post['featured_image'] = new_img
        post['image'] = new_img # Compatibilidad layouts viejos
        print(f"   ✅ Nueva imagen: {new_img}")

    with open(target_file_path, 'wb') as f:
        frontmatter.dump(post, f)
    
    print(f"   ✅ [V3 PRO] Archivo actualizado y validado: {target_file_path}")

if __name__ == "__main__":
    # Ejemplo de uso manual: python scripts/content_engine_pro.py
    # Se puede modificar para iterar carpetas como remastered_legacy.py
    print("Content Engine Pro v3.0 Loaded. Import this module to use.")
