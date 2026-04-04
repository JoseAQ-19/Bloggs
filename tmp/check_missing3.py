import os
import frontmatter
import json

base_dir = "content"
img_base_dir = "static"

missing = []
total = 0
for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith(".md"):
            filepath = os.path.join(root, filename)
            total += 1
            try:
                post = frontmatter.load(filepath)
                
                # Some old posts might use 'image' or 'thumbnail' instead of 'featured_image'
                img_path = post.get('featured_image', post.get('image', ''))
                
                if img_path:
                    # Strip leading slash if any to join correctly with 'static'
                    # Or construct the absolute path properly
                    # standard hugo path: target is /images/foo.jpg which is static/images/foo.jpg
                    if img_path.startswith('/'):
                        actual_path = os.path.join(img_base_dir, img_path.lstrip('/'))
                    else:
                        actual_path = os.path.join(img_base_dir, "images", img_path)
                    
                    if not os.path.exists(actual_path):
                        missing.append({
                            "file": filepath.replace('\\', '/'), 
                            "frontmatter_path": img_path,
                            "actual_path_checked": actual_path
                        })
                else:
                    # no image path set at all!
                    missing.append({
                        "file": filepath.replace('\\', '/'), 
                        "frontmatter_path": "NONE",
                        "actual_path_checked": "NONE"
                    })
            except Exception as e:
                pass

with open("tmp/missing_results_real.json", "w", encoding="utf-8") as f:
    json.dump({"total": total, "missing": missing}, f, indent=2)
