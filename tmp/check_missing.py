import os
import glob
import frontmatter

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
                        missing.append((filepath, img_path))
            except Exception as e:
                pass

print(f"Total MD checked: {total}")
print(f"Missing images: {len(missing)}")
for m in missing[:20]:
    print(f"File: {m[0]} -> Image: {m[1]}")
