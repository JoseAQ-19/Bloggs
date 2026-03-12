import sys
import os
import glob
import re

# Add the project root to sys.path
sys.path.append(os.getcwd())

from utils import LinkManager

def test_links():
    lang = "es"
    print(f"--- Debugging LinkManager for lang={lang} ---")
    
    # Check current directory
    print(f"Current Directory: {os.getcwd()}")
    
    # Check if content/es exists
    es_dir = os.path.join(os.getcwd(), "content", lang)
    if os.path.exists(es_dir):
        print(f"Directory {es_dir} exists")
    else:
        print(f"Directory {es_dir} NOT found")

    links = LinkManager.get_latest_internal_links(lang=lang, limit=5)
    print(f"Found {len(links)} links")
    for l in links:
        print(f"- {l['title']}: {l['url']}")

    # Check a specific file for regex match
    test_file = os.path.join(es_dir, "about.md")
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read(1000)
            print(f"Content start: {content[:100]}")
            m = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
            if m:
                print(f"MATCH: {m.group(1)}")
            else:
                print("NO MATCH for title regex")

if __name__ == "__main__":
    test_links()
