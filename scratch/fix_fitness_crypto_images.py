import os
import sys
import frontmatter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'core'))

def scan_all():
    content_dirs = [
        os.path.join(BASE_DIR, 'content/en'),
        os.path.join(BASE_DIR, 'content/es')
    ]
    
    affected_files = []

    for cdir in content_dirs:
        if not os.path.exists(cdir):
            continue
        for cat in os.listdir(cdir):
            cat_dir = os.path.join(cdir, cat)
            if not os.path.isdir(cat_dir):
                continue
            for root, _, files in os.walk(cat_dir):
                for f in files:
                    if not f.endswith('.md') or f == '_index.md':
                        continue
                    fpath = os.path.join(root, f)
                    post = frontmatter.load(fpath)
                    
                    img = post.get('featured_image') or post.get('image') or ''
                    title = post.get('title') or ''
                    slug = post.get('slug') or f.replace('.md', '')
                    
                    is_default = 'defaults' in str(img) or 'default-' in str(img) or not img
                    
                    image_exists = False
                    if img and not is_default:
                        clean_img = str(img).lstrip('/')
                        local_path = os.path.join(BASE_DIR, 'static', clean_img)
                        # Also check if it's a leaf bundle local image
                        leaf_path = os.path.join(root, clean_img)
                        image_exists = os.path.exists(local_path) or os.path.exists(leaf_path) or str(img).startswith('http')
                    
                    if is_default or not image_exists:
                        affected_files.append({
                            'path': fpath,
                            'title': title,
                            'slug': slug,
                            'category': cat,
                            'current_img': img,
                            'reason': 'default_image' if is_default else 'missing_file'
                        })

    print(f"Total affected files across all categories: {len(affected_files)}")
    for item in affected_files[:25]:
        print(f" - [{item['category']}] {item['slug']} (Reason: {item['reason']}, Current: {item['current_img']})")
    
    return affected_files

if __name__ == '__main__':
    scan_all()
