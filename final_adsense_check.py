import os
import re
import frontmatter

def final_adsense_check():
    print("🕵️‍♂️ INICIANDO AUDITORÍA FINAL ADSENSE...")
    
    # 1. VOLUMEN
    total_posts = 0
    h1_fails = 0
    thin_content = 0
    
    for root, dirs, files in os.walk("content"):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            total_posts += 1
            path = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(path)
                content = post.content.strip()
                
                # Check H1
                if re.search(r'^\s*#\s+.*', content, re.MULTILINE):
                    # Ignorar si es una página legal, a veces usan H1
                    if filename not in ["about.md", "contact.md", "privacy.md"]:
                        h1_fails += 1
                        # print(f"   ❌ H1 Detectado en: {filename}")
                
                # Check Thin Content
                if len(content.split()) < 300:
                    thin_content += 1
                    # print(f"   ❌ Thin Content ({len(content.split())}w): {filename}")
                    
            except: pass
            
    print(f"\n📚 VOLUMEN DE CONTENIDO:")
    print(f"   Total Artículos: {total_posts}")
    print(f"   H1 Duplicados: {h1_fails}")
    print(f"   Thin Content (<300w): {thin_content}")

    # 2. PÁGINAS LEGALES
    legal_pages = ["about.md", "contact.md", "privacy.md"]
    print(f"\n⚖️ PÁGINAS LEGALES:")
    for page in legal_pages:
        path = f"content/{page}"
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ {page} (Existe, {size} bytes)")
        else:
            print(f"   ❌ {page} (NO EXISTE - RECHAZO SEGURO)")

if __name__ == "__main__":
    final_adsense_check()
