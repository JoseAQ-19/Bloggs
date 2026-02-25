import os
import glob
import re
import json
import unicodedata

def normalize_text(text):
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'filepath': filepath, 'error': f'Failed to read: {e}', 'score': 100}

    parts = content.split('---')
    if len(parts) < 3:
        return {'filepath': filepath, 'error': 'Broken Frontmatter', 'score': 100}

    frontmatter = parts[1]
    body = '---'.join(parts[2:])
    
    lang_match = re.search(r'language:\s*(["\']?.*?["\']?)', frontmatter)
    lang = lang_match.group(1).lower().strip('"\'').strip() if lang_match else 'en'
    
    translation_key_match = re.search(r'translationKey:\s*(["\']?.*?["\']?)', frontmatter)
    tkey = translation_key_match.group(1).strip('"\'').strip() if translation_key_match else None
    
    issues = []
    seo_score = 10
    eeat_score = 10
    geo_score = 10
    value_score = 10
    
    # 1. METADATA & SEO
    if re.search(r'^#\s+', body, re.MULTILINE):
        issues.append("Contiene H1 en el cuerpo (penaliza SEO)")
        seo_score -= 5
    if tkey == "None" or tkey is None or tkey == "":
        issues.append("TranslationKey nulo o roto (metadatos rotos)")
        seo_score -= 5
        
    words = set(re.findall(r'\b[a-zA-Z]{2,}\b', body.lower()))
    if lang == 'es' and len(words.intersection({'the', 'and', 'with', 'that', 'this', 'for'})) >= 3:
         issues.append("Spanglish detectado (palabras en ingles en articulo ES)")
         value_score -= 5
         seo_score -= 5
    elif lang == 'en' and len(words.intersection({'el', 'la', 'con', 'para', 'que', 'los'})) >= 3:
         issues.append("Spanglish detectado (palabras en espanol en articulo EN)")
         value_score -= 5
         seo_score -= 5

    # 2. GEO (Robotic Headers)
    robotic_headers = ["nuestra lectura", "el caso de estudio", "the case study", "the consensus expert", "el consenso experto"]
    normalized_body = normalize_text(body)
    for head in robotic_headers:
        if normalize_text(head) in normalized_body:
            issues.append(f"Encabezado robotico detectado: {head}")
            geo_score -= 5
    
    if '*' not in body and '-' not in body:
        issues.append("Muro de texto continuo sin vinetas (Cero formato [BLUF]/GEO)")
        geo_score -= 5

    # 3. E-E-A-T (Prompt Leaks)
    ai_leaks = [
        "aqui tienes", "here is", "sure, here", "claro que si", "soy un modelo de inteligencia", "as an ai", "{{", "}}", "```json", "aqui tienes el articulo",
        "actua como", "tarea:", "role:", "task:", "mandatory rules"
    ]
    leaks_found = [w for w in ai_leaks if normalize_text(w) in normalized_body]
    if leaks_found:
        issues.append(f"Fuga del prompt de IA detectada: {', '.join(leaks_found)}")
        eeat_score -= 8
        value_score -= 8

    # 4. VALUE REAL (Corporate Fluff)
    banned_es = ["vertiginoso mundo", "arma de doble filo", "promete revolucionar", "queda por ver", "en conclusion", "tl;dr", "descubre como", "magia"]
    banned_en = ["ever-evolving", "double-edged sword", "game-changer", "it remains to be seen", "in conclusion", "tl;dr", "discover how", "magic"]
    
    banned_found = [w for w in (banned_es if lang == 'es' else banned_en) if normalize_text(w) in normalized_body]
    if banned_found:
        issues.append(f"Lenguaje corporativo/basura detectado: {', '.join(banned_found)}")
        value_score -= len(banned_found) * 3

    seo_score = max(1, seo_score)
    eeat_score = max(1, eeat_score)
    geo_score = max(1, geo_score)
    value_score = max(1, value_score)
    
    # Delete criteria
    should_delete = False
    if eeat_score < 7 or value_score < 7:
        should_delete = True
    if any("Spanglish" in i for i in issues):
        should_delete = True
    if any("robotico detectado" in i for i in issues):
        should_delete = True
    if any("TranslationKey" in i for i in issues):
        should_delete = True
    if any("Fuga del prompt" in i for i in issues):
        should_delete = True

    if should_delete:
        return {
            'filepath': filepath,
            'issues': issues,
            'seo': seo_score,
            'eeat': eeat_score,
            'geo': geo_score,
            'value': value_score
        }
    return None

def run():
    files = glob.glob(r'c:\Users\usuario\Desktop\Bloggs\content\**\*.md', recursive=True)
    death_row = []
    
    for f in files:
        if '_index.md' in f or 'about.md' in f or 'contact.md' in f or 'privacy.md' in f: continue
        res = analyze_file(f)
        if res:
            death_row.append(res)
            
    print("DEATH_ROW_COUNT:", len(death_row))
    for item in death_row:
        if 'error' in item:
            print(f"CRITICAL ERROR IN: {item.get('filepath', 'Unknown')} - {item['error']}")
        else:
            print(f"\nFILE: {item['filepath']}")
            print(f"SCORES -> SEO: {item['seo']}/10, E-E-A-T: {item['eeat']}/10, GEO: {item['geo']}/10, Value: {item['value']}/10")
            for i in item['issues']:
                print(f"  - {i}")

run()
