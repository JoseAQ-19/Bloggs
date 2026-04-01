import os
import re
import random

def audit_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return {"error": "Missing frontmatter"}

    header = parts[1]
    body = parts[2].strip()

    # SEO Checks
    metadata_leaks = re.findall(r'^(title:|slug:|description:|translationKey:)', body, re.MULTILINE | re.IGNORECASE)
    double_h1 = re.findall(r'^# ', body, re.MULTILINE)
    
    # Emojis in headers (detecting common emoji ranges)
    emoji_pattern = r'[\U00010000-\U0010ffff]' # Simple emoji range
    headers_with_emojis = re.findall(r'^##+ .*[^\x00-\x7F]+', body, re.MULTILINE) 
    # More specific emoji check for H2/H3
    header_emojis = []
    for line in body.split('\n'):
        if line.startswith('##'):
             if any(ord(c) > 0x2000 for c in line): # Basic check for symbols/emojis
                 header_emojis.append(line)

    # E-E-A-T / YMYL
    category = re.search(r'categories:\s*\["(.*?)"\]', header)
    category = category.group(1) if category else "unknown"
    
    is_ymyl = category in ['crypto', 'funds', 'fitness', 'realestate']
    has_disclaimer = False
    if is_ymyl:
        # Check for common keywords in our disclaimers
        has_disclaimer = "inversión" in body.lower() or "investment" in body.lower() or "médico" in body.lower() or "doctor" in body.lower() or "suit" in body.lower()

    # GEO
    has_tldr = "Resumen Ejecutivo" in body or "Executive Summary" in body or "(TL;DR)" in body
    has_methodology = "Metodología y Fuentes" in body or "Methodology & Sources" in body
    
    # Integrity
    is_truncated = body.endswith('...') or body.endswith('..') or not body.strip()[-1] in '.!?"\''
    
    # Check for robotic/spanglish (very basic)
    robotic_phrases = ["panorama", "vertiginoso", "doble filo", "solo el tiempo dirá", "remains to be seen"]
    found_cliches = [p for p in robotic_phrases if p in body.lower()]

    return {
        "file": filepath,
        "niche": category,
        "metadata_leaks": metadata_leaks,
        "double_h1": double_h1,
        "header_emojis": header_emojis,
        "ymyl_disclaimer": has_disclaimer if is_ymyl else "N/A",
        "tldr": has_tldr,
        "methodology": has_methodology,
        "truncated": is_truncated,
        "cliches": found_cliches,
        "length": len(body.split())
    }

def main():
    root_dir = 'content'
    all_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md') and not any(x in file for x in ['about', 'contact', 'privacy', 'terms', '_index']):
                all_files.append(os.path.join(root, file))

    sample = random.sample(all_files, min(20, len(all_files)))
    results = []
    for f in sample:
        results.append(audit_file(f))

    # Print Report
    print("# AUDIT REPORT - AD SENSE READINESS\n")
    for r in results:
        status = "✅ OK"
        issues = []
        if r.get("error"):
            status = "❌ FAIL"
            issues.append(r["error"])
        else:
            if r["metadata_leaks"]: issues.append(f"Metadata leak: {r['metadata_leaks']}")
            if r["double_h1"]: issues.append("Double H1")
            if r["header_emojis"]: issues.append(f"Emojis in headers: {len(r['header_emojis'])}")
            if r["ymyl_disclaimer"] == False: issues.append("Missing YMYL Disclaimer")
            if not r["tldr"]: issues.append("Missing TL;DR")
            if not r["methodology"]: issues.append("Missing Methodology")
            if r["truncated"]: issues.append("Truncated Content")
            if r["cliches"]: issues.append(f"Has Cliches: {r['cliches']}")
            if r["length"] < 1000: issues.append(f"Thin content ({r['length']} words)")
            
            if issues: status = "⚠️ WARNING" if len(issues) < 3 else "❌ REJECT"

        print(f"{status} | {r['file']} ({r['niche']})")
        if issues:
            for i in issues:
                print(f"   - {i}")

if __name__ == "__main__":
    main()
