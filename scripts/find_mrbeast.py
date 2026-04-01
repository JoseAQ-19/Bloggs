import os
import frontmatter
import glob

def find_mrbeast_articles():
    content_dir = r"C:\Users\usuario\Desktop\Bloggs\content"
    articles = []
    
    # Walk through lang/category
    for lang in ['es', 'en']:
        lang_path = os.path.join(content_dir, lang)
        if not os.path.exists(lang_path): continue
        
        for category in os.listdir(lang_path):
            cat_path = os.path.join(lang_path, category)
            if not os.path.isdir(cat_path): continue
            
            for fpath in glob.glob(os.path.join(cat_path, "*.md")):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)
                        content = post.content
                        if "MrBeast" in content or "Mr Beast" in content or "MrBeast" in post.get('title', ''):
                            slug = os.path.basename(fpath).replace('.md', '')
                            # Hugo URL structure: https://novumworld.com/en/category/slug/
                            url = f"https://novumworld.com/{lang}/{category}/{slug}/"
                            articles.append({
                                "title": post.get('title', 'No Title'),
                                "url": url,
                                "path": fpath
                            })
                except Exception as e:
                    print(f"Error reading {fpath}: {e}")
                    
    return articles

if __name__ == "__main__":
    results = find_mrbeast_articles()
    print(f"Encontrados {len(results)} artículos sobre MrBeast:\n")
    for a in results:
        print(f"- **Título:** {a['title']}")
        print(f"  **URL:** {a['url']}")
        print("-" * 20)
