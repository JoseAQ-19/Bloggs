import os
import re
import glob
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

CONTENT_DIR = r'c:\Users\usuario\Desktop\Bloggs\content'
STATIC_DIR = r'c:\Users\usuario\Desktop\Bloggs\static'

CACHE = {}

def check_external(url):
    if url in CACHE:
        return CACHE[url]
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.head(url, timeout=3, headers=headers, allow_redirects=True)
        if r.status_code >= 400:
            r2 = requests.get(url, timeout=3, headers=headers, allow_redirects=True, stream=True)
            res = r2.status_code < 400
        else:
            res = True
    except:
        res = False
    CACHE[url] = res
    return res

def check_internal(url, lang):
    clean_url = url.split('#')[0].split('?')[0]
    if not clean_url: return True
    if clean_url.startswith('/images/'):
        return os.path.exists(os.path.join(STATIC_DIR, clean_url.replace('/', os.sep).lstrip(os.sep)))
    
    parts = [p for p in clean_url.split('/') if p]
    if not parts: return True
    if parts[0] not in ['es', 'en']:
        parts.insert(0, lang)
    if len(parts) >= 2:
        potential_md = os.path.join(CONTENT_DIR, parts[0], parts[1], f"{parts[-1]}.md")
        if os.path.exists(potential_md):
            return True
        potential_dir = os.path.join(CONTENT_DIR, *parts)
        if os.path.isdir(potential_dir):
            return True
    return False

def audit_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    lang = 'es' if '\\es\\' in filepath else 'en'
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    links = link_pattern.findall(content)
    broken = []
    
    for anchor, url in links:
        is_valid = True
        if url.startswith('http'):
            # Skip if we already checked external earlier and it took forever, or just do it
            is_valid = check_external(url)
        elif url.startswith('/') or url.startswith('#'):
            if not url.startswith('#'):
                is_valid = check_internal(url, lang)
        
        if not is_valid:
            broken.append((anchor, url))
            
    return filepath, broken, original

def main():
    files = glob.glob(os.path.join(CONTENT_DIR, '**', '*.md'), recursive=True)
    broken_count = 0
    futures = []
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for f in files:
            futures.append(executor.submit(audit_file, f))
            
        for future in as_completed(futures):
            # Try/catch
            try:
                filepath, broken, original = future.result()
                if broken:
                    content = original
                    for anchor, url in broken:
                        print(f"BROKEN [{url}] in {filepath}")
                        content = content.replace(f'[{anchor}]({url})', f'**{anchor}**')
                        broken_count += 1
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception as e:
                pass
                
    print(f"\nFinal Broken Output: {broken_count}")

if __name__ == '__main__':
    main()
