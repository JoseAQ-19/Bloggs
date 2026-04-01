import os
import glob
import re
import json
import unicodedata

# Pre-normalización global para optimizar el rendimiento del Auditor
ROBOTIC_HEADERS_RAW = ["nuestra lectura", "el caso de estudio", "the case study", "the consensus expert", "el consenso experto"]

def normalize_text(text):
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas."""
    if not text: return ""
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()

# Caché de headers normalizados para evitar re-procesar en cada archivo
NORMALIZED_ROBOTIC = [normalize_text(h) for h in ROBOTIC_HEADERS_RAW]

def analyze_file(filepath):
    try:
        # Optimización DoS: Solo leer los primeros 10KB para el Frontmatter
        with open(filepath, 'r', encoding='utf-8') as f:
            head = f.read(10240) 
            f.seek(0)
            content = f.read() 
    except Exception as e:
        return {'filepath': filepath, 'error': f'Failed to read: {e}', 'score': 100}

    parts = content.split('---')
    if len(parts) < 3:
        return {'filepath': filepath, 'error': 'Broken Frontmatter', 'score': 100}

    frontmatter = parts[1]
    body = '---'.join(parts[2:])
    
    # Extraer metadatos con Regex seguras
    lang_match = re.search(r'language:\s*(["\']?.*?["\']?)', frontmatter)
    lang = lang_match.group(1).lower().strip('"\'').strip() if lang_match else 'en'
    
    translation_key_match = re.search(r'translationKey:\s*(["\']?.*?["\']?)', frontmatter)
    tkey = translation_key_match.group(1).strip('"\'').strip() if translation_key_match else None
    
    issues = []
    seo_score, eeat_score, geo_score, value_score = 10, 10, 10, 10
    
    # 1. METADATA & SEO
    if re.search(r'^#\s+', body, re.MULTILINE):
        issues.append("Contiene H1 en el cuerpo (penaliza SEO)")
        seo_score -= 5
    if not tkey or tkey.lower() == "none":
        issues.append("TranslationKey nulo o roto (metadatos rotos)")
        seo_score -= 5
        
    # 2. DETECTOR DE SPANGLISH (Optimizado con Whitelist Técnica)
    words = set(re.findall(r'\b[a-zA-Z]{2,}\b', body.lower()))
    technical_whitelist = {'api', 'llm', 'ai', 'saas', 'software', 'app', 'web', 'tools', 'code', 'prompt'}
    words = words - technical_whitelist
    
    if lang == 'es' and len(words.intersection({'the', 'and', 'with', 'that', 'this', 'for'})) >= 4:
         issues.append("Spanglish detectado (lenguaje mixto en articulo ES)")
         value_score -= 5; seo_score -= 5
    elif lang == 'en' and len(words.intersection({'el', 'la', 'con', 'para', 'que', 'los'})) >= 4:
         issues.append("Spanglish detectado (lenguaje mixto en articulo EN)")
         value_score -= 5; seo_score -= 5

    # 3. GEO & ROBOTIC HEADERS (Uso de caché normalizada)
    normalized_body = normalize_text(body)
    for i, h_norm in enumerate(NORMALIZED_ROBOTIC):
        if h_norm in normalized_body:
            issues.append(f"Encabezado robotico detectado: {ROBOTIC_HEADERS_RAW[i]}")
            geo_score -= 5
    
    if '*' not in body and '-' not in body:
        issues.append("Muro de texto continuo sin vinetas (Cero formato [BLUF])")
        geo_score -= 5

    # 4. E-E-A-T & AI LEAKS
    ai_leaks = ["aqui tienes", "here is", "sure, here", "claro que si", "soy un modelo de inteligencia", "as an ai", "{{", "}}", "```json"]
    leaks_found = [w for w in ai_leaks if normalize_text(w) in normalized_body]
    if leaks_found:
        issues.append(f"Fuga del prompt de IA detectada: {', '.join(leaks_found)}")
        eeat_score -= 8; value_score -= 8

    # 5. VALUE REAL (Corporate Fluff / Banned Words)
    banned_es = ["vertiginoso mundo", "arma de doble filo", "promete revolucionar", "queda por ver", "en conclusion", "tl;dr", "magia"]
    banned_en = ["ever-evolving", "double-edged sword", "game-changer", "it remains to be seen", "in conclusion", "tl;dr", "magic"]
    
    current_banned = banned_es if lang == 'es' else banned_en
    banned_found = [w for w in current_banned if normalize_text(w) in normalized_body]
    if banned_found:
        issues.append(f"Lenguaje basura detectado: {', '.join(banned_found)}")
        value_score -= len(banned_found) * 3

    # Normalización de Scores
    seo_score = max(1, seo_score); eeat_score = max(1, eeat_score)
    geo_score = max(1, geo_score); value_score = max(1, value_score)
    
    # Criterios de Borrado Automático (Death Row)
    should_delete = (eeat_score < 7 or value_score < 7 or 
                     any(x in " ".join(issues) for x in ["Spanglish", "robotico", "TranslationKey", "Fuga"]))

    if should_delete:
        return {
            'filepath': filepath, 'issues': issues,
            'seo': seo_score, 'eeat': eeat_score, 'geo': geo_score, 'value': value_score
        }
    return None

def run():
    # Detectar entorno Bloggs (compatibilidad Windows/Linux)
    content_path = os.path.join(os.getcwd(), 'content', '**', '*.md')
    files = glob.glob(content_path, recursive=True)
    death_row = []
    
    for f in files:
        if any(x in f for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md']): continue
        res = analyze_file(f)
        if res: death_row.append(res)
            
    print(f"📊 Auditoría completada. Artículos en Death Row: {len(death_row)}")
    for item in death_row:
        print(f"\n❌ ARCHIVO: {item['filepath']}")
        print(f"   SCORES -> SEO: {item['seo']}, E-E-A-T: {item['eeat']}, GEO: {item['geo']}, Value: {item['value']}")
        for i in item['issues']: print(f"     - {i}")

if __name__ == "__main__":
    run()
