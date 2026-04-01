import os
import frontmatter
from novum_visual import get_image

FILES = [
    "content/crypto/why-is-venice-token-trending-today-in-crypto-en.md",
    "content/crypto/why-is-venice-token-trending-today-in-crypto.md",
    "content/youtube/nba-all-star-2026-estrategia-digital.md",
    "content/youtube/nba-gathers-200-plus-creators-for-all-star-weekend-in-los-angeles-variety-en.md",
    "content/youtube/nba-gathers-200-plus-creators-for-all-star-weekend-in-los-angeles-variety.md"
]

def quick_fix():
    print("🚑 Quick Fix para NBA y Venice...")
    for f in FILES:
        if not os.path.exists(f): 
            print(f"Skipping {f}")
            continue
            
        post = frontmatter.load(f)
        
        # Check imagen
        img = post.get('featured_image', '')
        # Si no tiene imagen o es placeholder, regenerar
        if not img or "placehold" in img:
            print(f"   🔧 Reparando: {os.path.basename(f)}")
            title = post.get('title')
            slug = os.path.basename(f).replace('.md', '')
            # Categoria deducida
            cat = 'crypto' if 'crypto' in f else 'youtube'
            
            new_img = get_image(title, slug, cat)
            post['featured_image'] = new_img
            
            with open(f, 'wb') as file:
                frontmatter.dump(post, file)

if __name__ == "__main__":
    quick_fix()
