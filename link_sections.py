import os
import frontmatter

CONTENT_ROOT = "content"
SECTIONS = ["ia", "crypto", "fitness", "youtube", "viral", "tools"]
LANGS = ["es", "en"]

def link_sections():
    print("🔗 ENLAZANDO SECCIONES (TRANSLATION KEYS)...")
    
    for section in SECTIONS:
        key = f"section-{section}"
        print(f"   📂 Procesando: {section} (Key: {key})")
        
        for lang in LANGS:
            path = os.path.join(CONTENT_ROOT, lang, section, "_index.md")
            
            # Si no existe, crearlo básico
            if not os.path.exists(path):
                print(f"      ⚠️ Creando _index faltante: {path}")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                title = section.upper() if section != "ia" else "IA & Tech"
                with open(path, "w") as f:
                    f.write(f"---\ntitle: \"{title}\"\nlayout: \"list\"\nurl: \"/{section}/\"\n---\n")
            
            try:
                post = frontmatter.load(path)
                
                # Inyectar Key
                if post.get('translationKey') != key:
                    post['translationKey'] = key
                    with open(path, 'wb') as f:
                        frontmatter.dump(post, f)
                    print(f"      ✅ Key inyectada en {lang}")
                else:
                    # print(f"      🆗 Key ya existe en {lang}")
                    pass
                    
            except Exception as e:
                print(f"      ❌ Error en {path}: {e}")

if __name__ == "__main__":
    link_sections()
