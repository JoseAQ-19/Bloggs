
import os
import re
import uuid
import yaml
import glob
from datetime import datetime, timedelta

CONTENT_ES = "content/es"
CONTENT_EN = "content/en"

def load_frontmatter(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, None, None
    
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        fm_text = match.group(1)
        body = match.group(2)
        try:
            fm = yaml.safe_load(fm_text)
            return fm, body, fm_text
        except yaml.YAMLError:
            return None, None, None
    return None, None, None

def save_frontmatter(filepath, fm, body):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(fm, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        f.write("---\n")
        f.write(body)

def parse_date(date_obj):
    if isinstance(date_obj, str):
        try:
            return datetime.fromisoformat(date_obj)
        except ValueError:
            return None
    return date_obj

def get_candidates_en():
    candidates = [] # list of (datetime, filepath)
    for f in glob.glob(f"{CONTENT_EN}/**/*.md", recursive=True):
        if "_index.md" in f: continue
        fm, _, _ = load_frontmatter(f)
        if fm and 'date' in fm:
            dt = parse_date(fm['date'])
            if dt:
                candidates.append((dt, f))
    return candidates

def find_sibling_fuzzy(es_date, candidates_en):
    # Buscar el más cercano en un radio de 5 minutos
    best_match = None
    min_diff = timedelta(minutes=5)
    
    for en_date, en_path in candidates_en:
        diff = abs(es_date - en_date)
        if diff < min_diff:
            min_diff = diff
            best_match = en_path
            
    return best_match

def main():
    print("🔗 INICIANDO VINCULACIÓN DIFUSA (Tiempo Flexible)...")
    
    candidates_en = get_candidates_en()
    print(f"📚 Candidatos EN disponibles: {len(candidates_en)}")
    
    linked_count = 0
    es_files = glob.glob(f"{CONTENT_ES}/**/*.md", recursive=True)
    
    for es_path in es_files:
        if "_index.md" in es_path: continue
        
        fm_es, body_es, _ = load_frontmatter(es_path)
        if not fm_es or 'date' not in fm_es: continue
        
        es_date = parse_date(fm_es['date'])
        if not es_date: continue
        
        # Buscar hermano
        sibling_path = find_sibling_fuzzy(es_date, candidates_en)
        
        if sibling_path:
            # Encontrado!
            # Generar UUID
            new_key = str(uuid.uuid4())
            
            # Verificar si ya tienen key (y si es la misma)
            linked_already = False
            # ... (lógica simple: sobrescribir si es necesario)
            
            fm_es['translationKey'] = new_key
            save_frontmatter(es_path, fm_es, body_es)
            
            fm_en, body_en, _ = load_frontmatter(sibling_path)
            if fm_en:
                fm_en['translationKey'] = new_key
                save_frontmatter(sibling_path, fm_en, body_en)
                
            print(f"✅ Pareja Detectada (Diff: {abs(es_date - parse_date(fm_en['date']))}):\n   🇪🇸 {os.path.basename(es_path)}\n   🇺🇸 {os.path.basename(sibling_path)}")
            linked_count += 1
            
            # Quitar de candidatos para no repetir (opcional, pero seguro)
            # candidates_en = [c for c in candidates_en if c[1] != sibling_path]

    print(f"\n🎉 ¡EUREKA! {linked_count} pares vinculados temporalmente.")

if __name__ == "__main__":
    main()
