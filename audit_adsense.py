import os, re

def read_sample_files():
    encodings = ['utf-8', 'utf-16', 'utf-16-le', 'cp1252']
    for enc in encodings:
        try:
            with open('.sample.txt', 'r', encoding=enc) as f:
                return [line.strip().replace('\x00', '') for line in f if line.strip()]
        except:
            continue
    return []

files = read_sample_files()
if not files:
    print(".sample.txt not found or unreadable.")
    exit(1)

def has_emoji(text):
    # Simplistic emoji check using unicode ranges
    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"   # flags (iOS)
        "+", flags=re.UNICODE)
    return bool(emoji_pattern.search(text))

reports = {}

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parts = content.split('---')
        if len(parts) >= 3:
            fm_text = parts[1]
            body = '---'.join(parts[2:])
        else:
            fm_text = content
            body = content

        issues = []
        
        # 1. SEO
        h1s = re.findall(r'^#\s+(.*)', body, flags=re.MULTILINE)
        if len(h1s) > 0:
            issues.append(f"Double H1 in body: found {len(h1s)} H1s")
            
        # Check emojis in H2/H3
        h2h3s = re.findall(r'^(#{2,3})\s+(.*)', body, flags=re.MULTILINE)
        for level, text in h2h3s:
            if has_emoji(text):
                issues.append(f"Emoji found in header ({level}): {text.strip()}")
                
        # Frontmatter leak in body
        if re.search(r'\b(title:|slug:|date:|draft:)\s+', body, re.IGNORECASE):
            issues.append("Frontmatter leak detected in body")

        # 2. E-E-A-T
        clean_fm = fm_text.replace('"', '').replace("'", "")
        if 'author: NovumWorld Editorial Team' not in clean_fm:
            issues.append("Invalid author, not NovumWorld Editorial Team")
            
        is_ymyl = any(word in filepath.lower() for word in ['finance', 'crypto', 'funds', 'health', 'fitness', 'salud'])
        if is_ymyl:
            if not any(kw in body.lower() for kw in ['aviso editorial', 'editorial disclosure', 'descargo de responsabilidad', 'disclaimer']):
                issues.append("Missing YMYL disclaimer")

        # 3. Architecture
        if not any(kw in body.lower() for kw in ['resumen ejecutivo', 'executive summary', 'tl;dr']):
            issues.append("Missing TL;DR or Executive Summary block")
            
        if not any(kw in body.lower() for kw in ['metodología y fuentes', 'methodology and sources']):
            issues.append("Missing Methodology and Sources section")
            
        # 4. Integrity
        stripped_body = body.strip()
        if stripped_body and not re.search(r'[.!?\>\*]$', stripped_body):
            issues.append("Possible truncated article (does not end with valid punctuation/tag)")
            
        reports[filepath] = issues
    except Exception as e:
        reports[filepath] = [f"Error processing: {str(e)}"]

print("==================== AUDIT REPORT ====================")
for k, v in reports.items():
    if v:
        print(f"[FAIL] {k}")
        for i in v:
            print(f"  - {i}")
    else:
        print(f"[PASS] {k}")

print("\nSUMMARY:")
total = len(reports)
failed = sum(1 for v in reports.values() if v)
print(f"Total Audited: {total}")
print(f"Passed: {total - failed}")
print(f"Failed: {failed}")
