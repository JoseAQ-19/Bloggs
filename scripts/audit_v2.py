import sys
import os
import glob
import re
import json
import unicodedata

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
    lang_match = re.search(r'language:\s*["\']?([^\s"\'\n]+)', frontmatter)
    lang = lang_match.group(1).lower().strip() if lang_match else 'en'
    
    translation_key_match = re.search(r'translationKey:\s*["\']?([^\s"\'\n]+)', frontmatter)
    tkey = translation_key_match.group(1).strip() if translation_key_match else None
    
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

SECTION_ALIASES = {
    "ia-saas": "ia",
    "ia_saas": "ia",
    "biohacking": "fitness",
    "creators": "youtube"
}

def run(section=None, lang=None, export_json=None, fix_file=None):
    if fix_file:
        try:
            from core.daily_optimizer import DailyOptimizer
            optimizer = DailyOptimizer()
            res = optimizer.optimize_article(fix_file)
            print(f"✅ Archivo optimizado: {fix_file} -> {res.get('changes', [])}")
            return
        except Exception as e:
            print(f"❌ Error optimizando {fix_file}: {e}")
            return

    content_path = os.path.join(os.getcwd(), 'content', '**', '*.md')
    files = glob.glob(content_path, recursive=True)
    death_row = []
    
    sec_norm = SECTION_ALIASES.get(section.lower().strip(), section.lower().strip()) if section else None

    for f in files:
        if any(x in f for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md']): continue
        
        # Filter by lang if specified
        if lang:
            l_clean = lang.lower().strip()
            if f"content{os.sep}{l_clean}" not in f and f"content/{l_clean}" not in f:
                continue
                
        # Filter by section if specified
        if sec_norm:
            if f"{os.sep}{sec_norm}{os.sep}" not in f and f"/{sec_norm}/" not in f:
                continue

        res = analyze_file(f)
        if res: death_row.append(res)
            
    print(f"📊 Auditoría completada ({sec_norm or 'all'} / {lang or 'all'}). Artículos en Death Row: {len(death_row)}")
    for item in death_row:
        print(f"\n❌ ARCHIVO: {item['filepath']}")
        if 'error' in item:
            print(f"   ERROR -> {item['error']}")
        else:
            print(f"   SCORES -> SEO: {item.get('seo', 0)}, E-E-A-T: {item.get('eeat', 0)}, GEO: {item.get('geo', 0)}, Value: {item.get('value', 0)}")
            for i in item.get('issues', []): print(f"     - {i}")

    if export_json:
        os.makedirs(os.path.dirname(os.path.abspath(export_json)), exist_ok=True)
        articles_data = []
        for item in death_row:
            min_score = min(item.get('seo', 10), item.get('eeat', 10), item.get('geo', 10), item.get('value', 10)) * 10
            articles_data.append({
                "path": item["filepath"],
                "score": min_score,
                "issues": item.get("issues", [])
            })
        with open(export_json, "w", encoding="utf-8") as f:
            json.dump({"articles": articles_data}, f, indent=2, ensure_ascii=False)
        print(f"📁 Reporte exportado a {export_json} ({len(articles_data)} candidatos)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', '--section', dest='section', type=str, default=None)
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None)
    parser.add_argument('--export-json', dest='export_json', type=str, default=None)
    parser.add_argument('--fix-file', dest='fix_file', type=str, default=None)
    args = parser.parse_args()
    run(args.section, args.lang, args.export_json, args.fix_file)

