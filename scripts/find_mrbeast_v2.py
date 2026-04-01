import os
import frontmatter
import glob
import json

def find_mrbeast_articles():
    content_dir = r"C:\Users\usuario\Desktop\Bloggs\content"
    articles = []
    
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
                        title = post.get('title', 'No Title')
                        if "MrBeast" in content or "Mr Beast" in content or "MrBeast" in title:
                            slug = os.path.basename(fpath).replace('.md', '')
                            url = f"https://novumworld.com/{lang}/{category}/{slug}/"
                            articles.append({
                                "title": title,
                                "url": url,
                                "lang": lang,
                                "category": category,
                                "word_count": len(content.split()),
                                "path": fpath
                            })
                except Exception as e:
                    pass
                    
    return articles

if __name__ == "__main__":
    results = find_mrbeast_articles()
    with open("mrbeast_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Total found: {len(results)}")
