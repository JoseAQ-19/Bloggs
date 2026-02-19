import os
import frontmatter

CONTENT_ROOT = "content"
LEGAL_PAGES = {
    "about.md": {"weight": 70},
    "privacy.md": {"weight": 80},
    "contact.md": {"weight": 90}
}

def fix_legal_menus():
    print("⚖️ PROTOCOLO COMPLIANCE: Reparando Páginas Legales...")
    
    count = 0
    for lang in ["es", "en"]:
        for page, config in LEGAL_PAGES.items():
            path = os.path.join(CONTENT_ROOT, lang, page)
            
            if not os.path.exists(path):
                print(f"   ⚠️ Falta archivo: {path}")
                # Podría crearlo, pero la orden es auditar/fix Frontmatter. Asumo que existen por el paso anterior.
                continue
            
            try:
                post = frontmatter.load(path)
                changed = False
                
                # Fix Draft
                if post.get('draft') is True:
                    post['draft'] = False
                    changed = True
                    
                # Fix Menu
                if 'menu' not in post or post['menu'] != 'main':
                    post['menu'] = 'main'
                    post['weight'] = config['weight']
                    changed = True
                    
                if changed:
                    with open(path, 'wb') as f:
                        frontmatter.dump(post, f)
                    print(f"   ✅ [FIX] {lang}/{page} -> menu: main, draft: false")
                    count += 1
                else:
                    print(f"   🆗 {lang}/{page} OK")
                    
            except Exception as e:
                print(f"   ❌ Error en {path}: {e}")

    print(f"\n⚖️ Compliance completado: {count} archivos actualizados.")

if __name__ == "__main__":
    fix_legal_menus()
