import os
import frontmatter
from datetime import datetime, timedelta

CONTENT_ROOT = "content"
CATEGORIES = ["ia", "crypto", "fitness", "youtube", "viral", "tools"]

def parse_date(date_obj):
    """Normaliza la fecha a datetime object."""
    if isinstance(date_obj, datetime):
        return date_obj
    try:
        # Intentar formato ISO string
        return datetime.fromisoformat(str(date_obj))
    except:
        return None

def are_twins(date1, date2):
    """Devuelve True si las fechas son cercanas (< 30 min)."""
    if not date1 or not date2: return False
    diff = abs(date1 - date2)
    return diff < timedelta(minutes=30)

def link_siblings():
    print("🔗 INICIANDO OPERACIÓN TWIN LINK (ENLACE DE HERMANOS)...")
    
    linked_count = 0
    
    for category in CATEGORIES:
        path_en = os.path.join(CONTENT_ROOT, "en", category)
        path_es = os.path.join(CONTENT_ROOT, "es", category)
        
        if not os.path.exists(path_en) or not os.path.exists(path_es): continue
        
        posts_en = []
        posts_es = []
        
        # Cargar todos los posts EN
        for f in os.listdir(path_en):
            if f.endswith(".md") and not f.startswith("_"):
                p = frontmatter.load(os.path.join(path_en, f))
                posts_en.append({'file': f, 'path': os.path.join(path_en, f), 'date': parse_date(p.get('date')), 'post': p})

        # Cargar todos los posts ES
        for f in os.listdir(path_es):
            if f.endswith(".md") and not f.startswith("_"):
                p = frontmatter.load(os.path.join(path_es, f))
                posts_es.append({'file': f, 'path': os.path.join(path_es, f), 'date': parse_date(p.get('date')), 'post': p})
        
        print(f"\n📂 Categoría: {category.upper()} (EN: {len(posts_en)} | ES: {len(posts_es)})")
        
        # Emparejamiento
        for en_item in posts_en:
            best_match = None
            
            # Buscar hermano en ES por fecha cercana
            for es_item in posts_es:
                if are_twins(en_item['date'], es_item['date']):
                    best_match = es_item
                    break
            
            if best_match:
                # Generar Key Maestra (slug EN limpio)
                master_key = en_item['file'].replace('.md', '').replace('-en', '')
                
                # Inyectar Key en EN
                en_item['post']['translationKey'] = master_key
                with open(en_item['path'], 'wb') as f:
                    frontmatter.dump(en_item['post'], f)
                    
                # Inyectar Key en ES
                best_match['post']['translationKey'] = master_key
                with open(best_match['path'], 'wb') as f:
                    frontmatter.dump(best_match['post'], f)
                    
                print(f"   ✅ [LINKED] {en_item['file'][:30]}... <---> {best_match['file'][:30]}... | Key: {master_key}")
                linked_count += 1
                
                # Quitar de la lista ES para no re-emparejar (optimización simple)
                posts_es.remove(best_match)
            else:
                pass
                # print(f"   ⚠️ Huérfano EN: {en_item['file']}")

    print(f"\n🔗 OPERACIÓN FINALIZADA. {linked_count} parejas enlazadas.")

if __name__ == "__main__":
    link_siblings()
