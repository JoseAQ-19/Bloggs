import os
import re
import json

def audit_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None

    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return {"file": filepath, "error": "Missing frontmatter"}

    header = parts[1]
    body = parts[2].strip()

    metadata_leaks = re.findall(r'^(title:|slug:|description:|translationKey:)', body, re.MULTILINE | re.IGNORECASE)
    
    category_match = re.search(r'categories:\s*\["(.*?)"\]', header)
    if not category_match:
        category_match = re.search(r'categories:\s*-\s*(.*)', header)
    category = category_match.group(1) if category_match else "unknown"
    
    is_ymyl = category.strip() in ['crypto', 'funds', 'fitness', 'realestate']
    has_disclaimer = any(x in body.lower() for x in ["disclaimer", "aviso", "especialista", "profesional", "advice", "consult"]) if is_ymyl else True

    has_tldr = any(x in body for x in ["(TL;DR)", "Executive Summary", "Resumen Ejecutivo"])
    has_methodology = any(x in body for x in ["Metodología", "Methodology", "Fuentes", "Sources"])
    
    is_truncated = body.endswith('...') or body.endswith('..') or (len(body) > 0 and body.strip()[-1] not in '.!?"\'')
    
    length = len(body.split())
    
    issues = []
    if metadata_leaks: issues.append("Metadata leak")
    if is_ymyl and not has_disclaimer: issues.append("Missing Disclaimer")
    if not has_tldr: issues.append("Missing TL;DR")
    if not has_methodology: issues.append("Missing Methodology")
    if is_truncated: issues.append("Truncated")
    if length < 800: issues.append(f"Thin ({length} words)")

    if issues:
        return {"file": filepath, "issues": issues, "category": category}
    return None

def main():
    root_dir = 'content'
    failed_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md') and not any(x in file for x in ['about', 'contact', 'privacy', 'terms', '_index']):
                res = audit_file(os.path.join(root, file))
                if res:
                    failed_files.append(res)

    with open('ALL_FAILED_ARTICLES.json', 'w', encoding='utf-8') as f:
        json.dump(failed_files, f, indent=2)
    
    print(f"AUDIT COMPLETE: Found {len(failed_files)} articles with issues.")
    for f in failed_files[:10]:
        print(f"- {f['file']}: {', '.join(f['issues'])}")

if __name__ == "__main__":
    main()
