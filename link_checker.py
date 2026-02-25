"""
LINK CHECKER: Verifica URLs externas en archivos .md
Elimina enlaces rotos (404/500) manteniendo el texto ancla.
"""
import os, re, glob, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BLOGGS = r"c:\Users\usuario\Desktop\Bloggs"
TIMEOUT = 8
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def check_url(url):
    """Returns True if URL is reachable, False if broken."""
    try:
        r = requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code < 400:
            return True
        # HEAD might fail, try GET
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True, stream=True)
        return r.status_code < 400
    except:
        return False

def process_file(filepath):
    """Check all markdown links in a file. Remove broken ones, keep anchor text."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return filepath, 0, 0, []

    # Find all markdown links: [text](url)
    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    links = link_pattern.findall(content)
    
    if not links:
        return filepath, 0, 0, []
    
    broken = []
    checked = 0
    
    for anchor, url in links:
        checked += 1
        if not check_url(url):
            broken.append((anchor, url))
    
    if broken:
        for anchor, url in broken:
            # Replace [anchor](broken_url) with just anchor text (bold)
            content = content.replace(f'[{anchor}]({url})', f'**{anchor}**')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return filepath, checked, len(broken), broken

def main():
    files = glob.glob(os.path.join(BLOGGS, 'content', '**', '*.md'), recursive=True)
    articles = [f for f in files if '_index.md' not in f and 'about.md' not in f and 'contact.md' not in f and 'privacy.md' not in f]
    
    print(f"Checking {len(articles)} articles for broken links...")
    print("=" * 60)
    
    total_checked = 0
    total_broken = 0
    files_fixed = 0
    
    for article in articles:
        rel = os.path.relpath(article, BLOGGS)
        filepath, checked, broken_count, broken_list = process_file(article)
        total_checked += checked
        total_broken += broken_count
        
        if broken_count > 0:
            files_fixed += 1
            print(f"\n[FIXED] {rel} ({broken_count} broken links removed)")
            for anchor, url in broken_list:
                print(f"  404: {url}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL URLs checked: {total_checked}")
    print(f"TOTAL broken links removed: {total_broken}")
    print(f"TOTAL files fixed: {files_fixed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
