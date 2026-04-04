import os
import glob
import frontmatter
import json

base_dir = "content"
img_dir = "static/images"

existing_images = set(os.listdir(img_dir))

missing = []
total = 0
for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(".md"):
            filepath = os.path.join(root, filename)
            total += 1
            try:
                post = frontmatter.load(filepath)
                img_path = post.get('featured_image', '')
                if img_path:
                    # Extracts filename like 'something.jpg'
                    img_filename = img_path.replace('/images/', '').strip('/')
                    if img_filename not in existing_images:
                        missing.append({"file": filepath.replace('\\', '/'), "image": img_path})
            except Exception as e:
                pass

with open("tmp/missing_results.json", "w", encoding="utf-8") as f:
    json.dump({"total": total, "missing": missing}, f, indent=2)
