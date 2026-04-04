import os
import re
import sys

def go():
    errors = []
    root_dir = r"c:\Users\usuario\Bloggs\content"
    
    # 5. Pillar: Legal files existence
    legals = [
        "en/about.md", "en/privacy.md", "en/terms-of-service.md",
        "es/about.md", "es/privacy.md", "es/terms-of-service.md"
    ]
    for rel_l in legals:
        if not os.path.exists(os.path.join(root_dir, rel_l)):
            errors.append(f"FAIL: Legal file missing: {rel_l}")
            
    # Compile regexes
    es_bleed = re.compile(r'\b(el|la|los|las| un | una | con | para )\b', re.IGNORECASE)
    en_bleed = re.compile(r'\b(the|and|this|that|with)\b', re.IGNORECASE)
    
    ai_traces = [
        "(TL;DR)", "En conclusión", "En resumen", "Este artículo explora",
        "In conclusion", "In summary", "This article explores", "TL;DR"
    ]
    
    ymyl_categories = ["fitness", "salud", "crypto", "finance", "funds", "realestate"]
    
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, root_dir).replace('\\', '/')
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
            if len(parts) < 3:
                errors.append(f"FAIL: Corrupt frontmatter in {relpath}")
                continue
                
            header = parts[1]
            body = parts[2].strip()
            # remove frontmatter from bleed check to avoid false positives in metadata
            
            # Pillar 1: Bleed
            if relpath.startswith("en/"):
                # check for spanish bleed
                # remove typical markdown links and image tags before bleed check
                text_clean = re.sub(r'!\[.*?\]\(.*?\)', '', body)
                text_clean = re.sub(r'\[.*?\]\(.*?\)', '', text_clean)
                if es_bleed.search(text_clean):
                    found = es_bleed.search(text_clean).group()
                    errors.append(f"FAIL: Spanish bleed found in EN file {relpath}: '{found}'")
            elif relpath.startswith("es/"):
                text_clean = re.sub(r'!\[.*?\]\(.*?\)', '', body)
                text_clean = re.sub(r'\[.*?\]\(.*?\)', '', text_clean)
                if en_bleed.search(text_clean):
                    found = en_bleed.search(text_clean).group()
                    errors.append(f"FAIL: English bleed found in ES file {relpath}: '{found}'")

            # Pillar 2: Duplications Check
            methodology_es = len(re.findall(r'(?i)## Metodología y Fuentes', body))
            methodology_en = len(re.findall(r'(?i)## Methodology and Sources', body))
            if methodology_es > 1 or methodology_en > 1:
                errors.append(f"FAIL: Double methodology footer in {relpath}")
                
            disclaimer_count = len(re.findall(r'(?i)(descargo de responsabilidad|editorial disclosure|health disclosure|financial disclosure)', body))
            if disclaimer_count > 1:
                errors.append(f"FAIL: Double disclaimer in {relpath}")

            # Pillar 3: AI Traces and Spam
            for t in ai_traces:
                if t.lower() in body.lower():
                    errors.append(f"FAIL: AI trace '{t}' found in {relpath}")
            
            if len(body) > 0 and body[-1] not in '.!?"\'':
                # Sometimes images or links could be at the end.
                if not (body.endswith(')') or body.endswith('>')):
                    errors.append(f"FAIL: Truncated content (no ending punctuation) in {relpath}: ends with {body[-5:]}")

            # Pillar 4: Internal linking
            urls = link_pattern.findall(body)
            for text, url in urls:
                if url.strip() == '#' or url.strip() in ['/en/', '/es/', '/en', '/es']:
                    errors.append(f"FAIL: Empty or generic link '{url}' in {relpath}")
                
                # Check 404 for injected links
                # Usually internal links start with /en/ or /es/
                if url.startswith('/en/') or url.startswith('/es/'):
                    # clean anchors
                    clean_url = url.split('#')[0]
                    # path mapping
                    if clean_url in ['/en/', '/es/']: continue 
                    # strip trailing slash
                    clean_url = clean_url.rstrip('/')
                    target_md = os.path.join(root_dir, clean_url.strip('/') + '.md')
                    target_index = os.path.join(root_dir, clean_url.strip('/'), '_index.md')
                    
                    if not (os.path.exists(target_md) or os.path.exists(target_index)):
                        errors.append(f"FAIL: Broken internal link '{url}' in {relpath}")
                        
            # Pillar 5: YMYL Disclaimer
            cat_match = re.search(r'categories:\s*\[(.*?)\]', header)
            if cat_match:
                categories = cat_match.group(1).lower()
                is_ymyl = any(y in categories for y in ymyl_categories)
                if is_ymyl:
                    has_disclaimer = bool(re.search(r'(?i)(descargo de responsabilidad|editorial disclosure|health disclosure|financial disclosure)', body))
                    if not has_disclaimer:
                        errors.append(f"FAIL: YMYL category but missing disclaimer in {relpath}")

    return "\n".join(errors) if errors else "GO"

result = go()
open('tmp/audit_out.txt', 'w', encoding='utf-8').write(result)
print(repr(result))
