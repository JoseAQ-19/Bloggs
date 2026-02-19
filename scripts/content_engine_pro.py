
import os
import json
import re
import frontmatter
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

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

# 2. System Prompt de Alta Ingeniería (Estructura JSON forzosa)
SYSTEM_PROMPT = """
ACT AS: Senior Editor & Niche Subject Matter Expert (E-E-A-T focused).
OBJECTIVE: Write a high-value, deep-dive article based on the provided topic and context.

CRITICAL RULES:
1. **NO META-TALK**: Never say "Here is the article" or "I have rewritten...". Just output the content.
2. **NO LABELING**: Do not use "Introduction", "Body", "Conclusion", "Verdict" as headers. Use descriptive, engaging H2/H3 headers.
3. **LANGUAGE LOCK**: You MUST write in {language}. (EN = English, ES = Spanish). Do not mix languages in headers.
4. **VALUE FIRST**: Avoid fluff. Use data, quotes, and specific examples.
5. **FORMAT**: Return ONLY a valid JSON object.

JSON SCHEMA:
{{
  "title": "Optimized SEO Title in {language}",
  "h1_title": "Engaging Viral H1 Title in {language}",
  "meta_description": "SEO description (150-160 chars) in {language}",
  "content_body": "The full markdown article content. detailed, strict markdown. Use **bold** for emphasis. No H1 (it goes in frontmatter). Start with a strong Hook."
}}
"""

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

def generate_article_pro(current_content, context_data, target_language):
    """Genera el contenido usando Gemini 2.0 Flash con output JSON."""
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json"} # FORCE JSON
    )

    user_message = f"""
    TOPIC/CONTEXT: {context_data}
    ----
    CURRENT DRAFT (For reference): 
    {current_content[:1000]}...
    ----
    TASK: Rewrite and expand into a premium article in {target_language}.
    """

    full_prompt = SYSTEM_PROMPT.format(language=target_language)
    
    try:
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [full_prompt + "\n" + user_message]}
            ]
        )
        
        return json.loads(response.text)
    except Exception as e:
        print(f"   ❌ Error en generación IA: {e}")
        return None

def main_upgrade_engine(target_file_path):
    """Función principal para actualizar un archivo individual."""
    
    if not os.path.exists(target_file_path):
        print("Archivo no encontrado.")
        return

    print(f"🚀 Procesando: {os.path.basename(target_file_path)}")
    
    # 1. Detectar Contexto
    lang = detect_language_context(target_file_path)
    post = frontmatter.load(target_file_path)
    current_body = post.content
    
    # 2. Generar
    # (En un caso real, aquí conectaríamos con EXA para el context_data. 
    # Por ahora usamos el contenido actual como contexto semilla)
    result_json = generate_article_pro(current_body, post.get('title', 'Unknown Topic'), lang)
    
    if not result_json:
        print("   ❌ Fallo en generación. Saltando.")
        return

    # 3. Validar
    cleaned_body = validate_content(result_json['content_body'], lang)
    if not cleaned_body:
        print("   ❌ El contenido no pasó el filtro de calidad (Linter).")
        return

    # 4. Guardar (Atomic Write)
    post.content = cleaned_body
    post['title'] = result_json['title'] # SEO Title updated
    post['description'] = result_json['meta_description']
    post['quality_tier'] = "fenix_v3_pro" # Marca de calidad nueva
    post['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    
    with open(target_file_path, 'wb') as f:
        frontmatter.dump(post, f)
    
    print(f"   ✅ [V3 PRO] Archivo actualizado y validado: {target_file_path}")

if __name__ == "__main__":
    # Ejemplo de uso manual: python scripts/content_engine_pro.py
    # Se puede modificar para iterar carpetas como remastered_legacy.py
    print("Content Engine Pro v3.0 Loaded. Import this module to use.")
