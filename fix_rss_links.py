"""
fix_rss_links.py — Elimina enlaces de Google News RSS redirect de todos los artículos.

Strategy:
 - Option A: Try to resolve the redirect to get the real URL.
 - Option B: If resolution fails, remove the link and keep only the anchor text.
"""
import os
import re
import glob
import requests
import time

CONTENT_DIRS = [
    os.path.join(os.getcwd(), 'content', 'en'),
    os.path.join(os.getcwd(), 'content', 'es'),
]

# Pattern: [anchor text](https://news.google.com/rss/articles/...)
LINK_PATTERN = re.compile(
    r'\[([^\]]*)\]\(https?://news\.google\.com/rss/articles/[^\)]+\)'
)

# Pattern: bare URL (not inside markdown link)
BARE_URL_PATTERN = re.compile(
    r'(?<!\()(https?://news\.google\.com/rss/articles/\S+?)(?=[\s\)\],;]|$)'
)

resolved_cache = {}
stats = {
    'files_scanned': 0,
    'files_modified': 0,
    'links_resolved': 0,
    'links_removed': 0,
    'links_failed': 0,
}


def resolve_redirect(url):
    """Try to follow the Google News redirect to the real URL."""
    if url in resolved_cache:
        return resolved_cache[url]
    
    try:
        # Follow redirects with a short timeout
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=5,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NovumBot/1.0)'}
        )
        final_url = resp.url
        
        # Check if we actually got to a real destination (not still google)
        if 'news.google.com' not in final_url and resp.status_code < 400:
            resolved_cache[url] = final_url
            return final_url
    except Exception:
        pass
    
    # Try GET as fallback (some redirects only work with GET)
    try:
        resp = requests.get(
            url,
            allow_redirects=True,
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            stream=True  # Don't download full body
        )
        final_url = resp.url
        resp.close()

        if 'news.google.com' not in final_url and resp.status_code < 400:
            resolved_cache[url] = final_url
            return final_url
    except Exception:
        pass
    
    resolved_cache[url] = None
    return None


def replace_markdown_link(match):
    """Replace a markdown link with either resolved URL or plain text."""
    anchor_text = match.group(1).strip()
    full_match = match.group(0)
    
    # Extract URL from the match
    url_match = re.search(r'\((https?://news\.google\.com/rss/articles/[^\)]+)\)', full_match)
    if not url_match:
        return full_match
    
    original_url = url_match.group(1)
    
    # Try to resolve
    real_url = resolve_redirect(original_url)
    
    if real_url:
        stats['links_resolved'] += 1
        return f'[{anchor_text}]({real_url})'
    else:
        stats['links_removed'] += 1
        # Keep anchor text as bold reference, remove the broken link
        if anchor_text:
            return f'**{anchor_text}**'
        return ''


def replace_bare_url(match):
    """Replace a bare Google RSS URL."""
    original_url = match.group(0).rstrip('*').rstrip('"').rstrip(',')
    
    real_url = resolve_redirect(original_url)
    if real_url:
        stats['links_resolved'] += 1
        return real_url
    else:
        stats['links_removed'] += 1
        return ''


def process_file(filepath):
    """Process a single markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False
    
    if 'news.google.com/rss/articles' not in content:
        return False
    
    # Replace markdown links first
    new_content = LINK_PATTERN.sub(replace_markdown_link, content)
    
    # Replace any remaining bare URLs
    new_content = BARE_URL_PATTERN.sub(replace_bare_url, new_content)
    
    # Clean up artifacts: empty parentheses, double spaces, empty bold
    new_content = re.sub(r'\(\s*\)', '', new_content)
    new_content = re.sub(r'\*\*\s*\*\*', '', new_content)
    new_content = re.sub(r'  +', ' ', new_content)
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    print("=" * 60)
    print("FIX RSS LINKS - Eliminando enlaces de Google News RSS")
    print("=" * 60)
    
    # First pass: try Option A (resolve redirects) for a small batch
    # If Google blocks us, fall back to Option B (remove links)
    print("\n[1/2] Testing redirect resolution...")
    test_url = "https://news.google.com/rss/articles/CBMiiwFBVV95cUxOMU9lNFZDc2lUTFc2WFFjZXJwQi1kRXdIUGF1dDN0NjRmUWY3WkhZOUdjR1dYRDRoUnJ5bmpLU0FfNU95V19tcDRYZXNsR3kxMVJ0UE5NNVNEVlFpd2hhM2J6ejZNM09BMEV2dmh3cVl2R3dudEZnc3VtWEVLb083YXYxTERIeTNHaWxB?oc=5"
    result = resolve_redirect(test_url)
    if result:
        print(f"  Resolution works! Test URL resolved to: {result[:80]}...")
        print("  Using Option A (resolve + replace) with Option B fallback")
    else:
        print("  Google is blocking redirects. Using Option B (remove links, keep text)")
    
    print("\n[2/2] Processing all content files...")
    
    all_files = []
    for content_dir in CONTENT_DIRS:
        all_files.extend(glob.glob(os.path.join(content_dir, '**', '*.md'), recursive=True))
    
    for filepath in all_files:
        stats['files_scanned'] += 1
        if process_file(filepath):
            stats['files_modified'] += 1
            print(f"  FIXED: {os.path.basename(filepath)}")
    
    print("\n" + "=" * 60)
    print("RESULTADOS:")
    print(f"  Archivos escaneados:   {stats['files_scanned']}")
    print(f"  Archivos modificados:  {stats['files_modified']}")
    print(f"  Links resueltos (A):   {stats['links_resolved']}")
    print(f"  Links eliminados (B):  {stats['links_removed']}")
    print("=" * 60)
    
    # Verify zero remaining
    remaining = 0
    for filepath in all_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if 'news.google.com/rss/articles' in f.read():
                    remaining += 1
                    print(f"  WARNING: Still has RSS links: {os.path.basename(filepath)}")
        except Exception:
            pass
    
    if remaining == 0:
        print("\nVERIFICACION: CERO enlaces news.google.com en produccion!")
    else:
        print(f"\nALERTA: {remaining} archivos aun tienen enlaces RSS!")


if __name__ == "__main__":
    main()
