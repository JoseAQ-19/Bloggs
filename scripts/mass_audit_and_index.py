import os
import glob
import re
import time
import indexing_api

CONTENT_DIR = r'c:\Users\usuario\Desktop\Bloggs\content'

CYNICAL_WORDS = ['mentira', 'burbuja', 'stafa', 'realidad', 'secreto', 'oscuro', 'fracaso', 'trampa', 'humo', 'sobrevalorado', 'dictadura', 'zombi', 'apocalipsis', 'peligro', 'lie', 'bubble', 'hype', 'scam', 'reality', 'secret', 'dark', 'fail', 'trap', 'smoke', 'overrated', 'dictatorship', 'zombie', 'apocalypse', 'danger', 'worst', 'myth', 'lobotomy', 'bullshit', 'trainwreck', 'mentiras', 'engaño', 'engaños', 'mito', 'mitos']

def audit_article(filepath):
    if any(x in filepath.lower() for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md']):
        return None
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match: return None
    
    fm_text = match.group(1)
    body = content[match.end():]
    
    scores = {'SEO': 0, 'EEAT': 0, 'GEO': 0, 'VALUE': 0}
    reject_reason = ""
    
    # --- 1. SEO ---
    seo_score = 5
    if 'translationKey:' in fm_text and 'title:' in fm_text and 'description:' in fm_text:
        seo_score += 2
    h2_count = len(re.findall(r'^##\s', body, re.MULTILINE))
    h3_count = len(re.findall(r'^###\s', body, re.MULTILINE))
    if h2_count >= 2: seo_score += 2
    if h3_count >= 1: seo_score += 1
    
    # check broken links (already did, but penalize if any found)
    if '](http' in body and '[http' not in body:
        seo_score += 0 # just base
        
    scores['SEO'] = min(10, seo_score)
    
    # --- 2. E-E-A-T ---
    eeat_score = 5
    numbers = len(re.findall(r'\b\d+(\.\d+)?%?\b', body))
    if numbers > 20: eeat_score += 3
    elif numbers > 10: eeat_score += 2
    
    names = len(re.findall(r' [A-Z][a-z]+', body))
    if names > 40: eeat_score += 2
    elif names > 20: eeat_score += 1
    
    scores['EEAT'] = min(10, eeat_score)
    
    # --- 3. GEO ---
    geo_score = 5
    top_body = body[:1500]
    if re.search(r'(\n[-*]\s|\n\d+\.\s)', top_body):
        geo_score += 3 # BLUF format
        
    if re.search(r'(?i)##\s*(conclusi.n|en resumen|nuestra lectura|final thoughts)', body):
        geo_score -= 2 # Generic headers
    else:
        geo_score += 2
        
    scores['GEO'] = min(10, max(1, geo_score))
    
    # --- 4. REAL VALUE ---
    val_score = 5
    body_lower = body.lower()
    cynical_matches = sum(1 for w in CYNICAL_WORDS if w in body_lower)
    
    if cynical_matches > 5:
        val_score += 5
    elif cynical_matches > 2:
        val_score += 3
    elif cynical_matches > 0:
        val_score += 1
        
    # Penalty for AI phrases
    if re.search(r'(?i)(en conclusión|para resumir|es importante destacar|en resumen|in conclusion|to summarize|it is important to note)', body):
        val_score -= 3
        
    if val_score < 9:
        reject_reason = "Falta tono incisivo/datos contrarianos. Contenido demasiado genérico o neutro."
        
    scores['VALUE'] = min(10, max(1, val_score))
    
    avg_score = sum(scores.values()) / 4.0
    
    # Get Final URL
    url_match = re.search(r'url:\s*["\']?(.*?)["\']?\n', fm_text)
    if url_match:
        url_path = url_match.group(1).strip()
    else:
        lang = 'es' if '\\es\\' in filepath else ''
        filename = os.path.basename(filepath)
        category = os.path.basename(os.path.dirname(filepath))
        url_path = f"/{lang}/{category}/{filename.replace('.md', '')}/".replace('//', '/')
        
    final_url = f"https://novumworld.com{url_path}"
    title_match = re.search(r'title:\s*["\']?(.*?)["\']?\n', fm_text)
    title = title_match.group(1) if title_match else filename
    
    return {
        'url': final_url,
        'title': title,
        'scores': scores,
        'avg': avg_score,
        'reject_reason': reject_reason
    }

def main():
    files = glob.glob(os.path.join(CONTENT_DIR, '**', '*.md'), recursive=True)
    results = []
    
    for f in files:
        res = audit_article(f)
        if res:
            results.append(res)
            
    winners = [r for r in results if r['avg'] > 8.5 and r['scores']['VALUE'] >= 9]
    rejected = [r for r in results if r['avg'] <= 8.5 or r['scores']['VALUE'] < 9]
    
    with open(r'c:\Users\usuario\Desktop\Bloggs\audit_output_final.md', 'w', encoding='utf-8') as out:
        out.write("====================================\n")
        out.write("🛡️ PROTOCOLO FILTRO ANTI-SPAM 🛡️\n")
        out.write("====================================\n")
        out.write(f"Total Auditados: {len(results)}\n")
        out.write(f"Aprobados (Ganadores): {len(winners)}\n")
        out.write(f"Rechazados (Baja Calidad): {len(rejected)}\n")
        out.write("\n")
        
        out.write("--- ⚔️ RECHAZADOS DESTACADOS (Muestra de 3) ---\n")
        for r in rejected[:3]:
            out.write(f"URL: {r['url']}\n")
            out.write(f"Score Promedio: {r['avg']:.1f}/10 (Valor: {r['scores']['VALUE']}/10)\n")
            out.write(f"Feedback para Ralph: {r['reject_reason']}\n\n")
            
        out.write("\n--- 🚀 EJECUCIÓN METRALLETA SEO (Pings a Google) ---\n")
        if not winners:
            out.write("Ningún artículo alcanzó el nivel 10/10 necesario.\n")
            return
            
        success_count = 0
        for w in winners:
            out.write(f"Disparando a: {w['url']} (Score: {w['avg']:.1f}/10)\n")
            indexing_api.notify_google(w['url'])
            time.sleep(2) # Rate Limiting
            success_count += 1
            
        out.write(f"\n✅ Proceso completado. {success_count} artículos notificados prioritariamente a Google Search Console.\n")
    print("Log saved")

if __name__ == '__main__':
    main()
