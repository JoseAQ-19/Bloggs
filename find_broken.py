import os
import frontmatter
from novum_visual import get_image

def find_broken_banks():
    print("🔎 ESCANEO EXHAUSTIVO DE IMÁGENES ROTAS EN IA...")
    for filename in os.listdir("content/es/ia"):
        if not filename.endswith(".md"): continue
        path = os.path.join("content/es/ia", filename)
        
        post = frontmatter.load(path)
        img = post.get('featured_image', '')
        
        broken = False
        if not img: broken = True
        else:
            phys = os.path.join("static", img.lstrip('/'))
            if not os.path.exists(phys): broken = True
            
        if broken:
            print(f"   🚑 Roto encontrado: {filename}")
            # Fix
            title = post.get('title')
            slug = filename.replace('.md', '')
            new_img = get_image(title, slug, "ia")
            post['featured_image'] = new_img
            with open(path, 'wb') as f: frontmatter.dump(post, f)
            print("   ✅ Arreglado.")

if __name__ == "__main__":
    find_broken_banks()
