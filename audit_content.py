import os
import glob
import re

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'filepath': filepath, 'error': f'Failed to read: {e}', 'score': 100}

    parts = content.split('---')
    if len(parts) < 3:
        return {'filepath': filepath, 'error': 'Broken Frontmatter', 'score': 100}

    body = '---'.join(parts[2:])
    lang_match = re.search(r'language:\s*(["\']?.*?["\']?)', parts[1])
    lang = lang_match.group(1).lower().strip('"\'').strip() if lang_match else 'en'
    
    issues = []
    seo_score = 10
    eeat_score = 10
    geo_score = 10
    value_score = 10
    
    if re.search(r'^#\s+', body, re.MULTILINE):
        issues.append("Contiene H1 en el cuerpo (penaliza SEO)")
        seo_score -= 5
        
    words = set(re.findall(r'\b[a-zA-Z]{2,}\b', body.lower()))
    if lang == 'es' and len(words.intersection({'the', 'and', 'with', 'that', 'this', 'for'})) >= 3:
         issues.append("Spanglish detectado (palabras en ingles en articulo ES)")
         value_score -= 8
         seo_score -= 5
    elif lang == 'en' and len(words.intersection({'el', 'la', 'con', 'para', 'que', 'los'})) >= 3:
         issues.append("Spanglish detectado (palabras en espanol en articulo EN)")
         value_score -= 8
         seo_score -= 5

    banned_es = ["vertiginoso mundo", "arma de doble filo", "promete revolucionar", "queda por ver", "en conclusion", "tl;dr", "descubre como", "magia"]
    banned_en = ["ever-evolving", "double-edged sword", "game-changer", "it remains to be seen", "in conclusion", "tl;dr", "discover how", "magic"]
    
    import unicodedata
    normalized_body = unicodedata.normalize('NFD', body).encode('ascii', 'ignore').decode('utf-8').lower()
    
    banned_found = [w for w in (banned_es if lang == 'es' else banned_en) if w in normalized_body]
    if banned_found:
        issues.append(f"Lenguaje corporativo/basura detectado: {', '.join(banned_found)}")
        value_score -= len(banned_found) * 3
        eeat_score -= len(banned_found) * 3

    ai_leaks = ["aqui tienes", "here is", "sure, here", "claro que si", "soy un modelo de inteligencia", "as an ai", "{{", "}}", "```json", "aqui tienes el articulo"]
    leaks_found = [w for w in ai_leaks if w in normalized_body]
    if leaks_found:
        issues.append(f"Fuga del prompt de IA o sintaxis de template descubierta: {', '.join(leaks_found)}")
        eeat_score -= 8
        value_score -= 8
        seo_score -= 5
        
    if '*' not in body and '-' not in body:
        issues.append("Muro de texto continuo sin vinetas (Cero formato [BLUF]/GEO)")
        geo_score -= 5
        
    paragraphs = body.split('\n\n')
    long_paragraphs = [p for p in paragraphs if p.count('.') > 4]
    if len(long_paragraphs) > 2:
        issues.append("Parrafos excesivamente largos detectados (>4 oraciones)")
        geo_score -= 3

    seo_score = max(1, seo_score)
    eeat_score = max(1, eeat_score)
    geo_score = max(1, geo_score)
    value_score = max(1, value_score)
    
    if issues and (seo_score <= 5 or eeat_score <= 5 or geo_score <= 5 or value_score <= 5):
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
        if '_index.md' in f: continue
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
