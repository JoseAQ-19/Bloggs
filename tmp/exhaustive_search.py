import os
import glob
import re

def get_title(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

all_md = glob.glob('**/*.md', recursive=True)
for f in all_md:
    title = get_title(f)
    if title and ("Azken" in title or "Shamrock" in title or "Waco" in title):
        print(f"FOUND: {f} | {title}")

# Also check for filenames
for f in all_md:
    if "azken" in f.lower() or "shamrock" in f.lower():
        print(f"FILE MATCH: {f}")
