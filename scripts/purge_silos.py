import os
import shutil
import frontmatter

CONTENT_ROOT = "content"
LANGS = ["es", "en"]

def detect_real_language(post):
    # 1. Frontmatter
    lang_fm = post.get('language')
    if lang_fm == 'es': return 'es'
    if lang_fm == 'en': return 'en'
    
    # 2. Heurística de Contenido/Título
    text = (post.get('title', '') + " " + post.content[:200]).lower()
    english_score = text.count(' the ') + text.count(' and ') + text.count(' is ')
    spanish_score = text.count(' el ') + text.count(' y ') + text.count(' es ')
    
    if english_score > spanish_score: return 'en'
    return 'es'

def purge_silos():
    print("🧹 INICIANDO PURGA DE SILOS (CROSS-LANGUAGE LEAKS)...")
    
    moves = 0
    deletes = 0
    
    # Escanear carpetas de idioma
    for current_lang in LANGS:
        lang_dir = os.path.join(CONTENT_ROOT, current_lang)
        if not os.path.exists(lang_dir): continue
        
        for root, dirs, files in os.walk(lang_dir):
            for filename in files:
                if not filename.endswith(".md") or filename.startswith("_index"): continue
                
                filepath = os.path.join(root, filename)
                
                try:
                    post = frontmatter.load(filepath)
                    real_lang = detect_real_language(post)
                    
                    # Si el idioma detectado NO coincide con la carpeta actual
                    if real_lang != current_lang:
                        # Calcular destino correcto
                        # Reemplazar /es/ por /en/ o viceversa en la ruta
                        dest_path = filepath.replace(f"/{current_lang}/", f"/{real_lang}/")
                        
                        print(f"🚩 INTRUSO DETECTADO: {filename}")
                        print(f"   - Ubicación: {current_lang.upper()}")
                        print(f"   - Idioma Real: {real_lang.upper()}")
                        
                        # Mover o Borrar si duplicado
                        if os.path.exists(dest_path):
                            print(f"   🗑️ Destino ya existe (Duplicado). Borrando intruso.")
                            os.remove(filepath)
                            deletes += 1
                        else:
                            # Asegurar carpeta destino
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            
                            # Actualizar frontmatter para que coincida (por si acaso estaba mal etiquetado)
                            post['language'] = real_lang
                            with open(filepath, 'wb') as f:
                                frontmatter.dump(post, f)
                                
                            shutil.move(filepath, dest_path)
                            print(f"   📦 MOVIDO a: {dest_path}")
                            moves += 1
                            
                except Exception as e:
                    print(f"❌ Error leyendo {filename}: {e}")

    print(f"\n✨ PURGA FINALIZADA.")
    print(f"   Movidos: {moves}")
    print(f"   Borrados: {deletes}")

if __name__ == "__main__":
    purge_silos()
