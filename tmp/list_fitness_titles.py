import os
import glob
import re

def get_title(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Try finding title in YAML frontmatter
            match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

files = glob.glob('content/**/fitness/*.md', recursive=True)
results = []
for f in files:
    if os.path.basename(f) == '_index.md':
        continue
    title = get_title(f)
    if title:
        results.append((f, title, os.path.getmtime(f)))

# Sort by modification time descending
results.sort(key=lambda x: x[2], reverse=True)

for path, title, mtime in results:
    print(f"{path} | {title}")
