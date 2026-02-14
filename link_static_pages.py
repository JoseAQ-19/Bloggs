import os
import frontmatter

CONTENT_ROOT = "content"
STATIC_PAGES = ["about.md", "contact.md", "privacy.md"]

def link_static():
    print("🔗 ENLAZANDO PÁGINAS ESTÁTICAS...")
    
    for page in STATIC_PAGES:
        key = page.replace(".md", "")
        
        for lang in ["es", "en"]:
            path = os.path.join(CONTENT_ROOT, lang, page)
            if os.path.exists(path):
                post = frontmatter.load(path)
                post['translationKey'] = key
                with open(path, 'wb') as f:
                    frontmatter.dump(post, f)
                print(f"   ✅ {page} ({lang}) -> Key: {key}")

if __name__ == "__main__":
    link_static()
