import glob, os, re

errors = []

all_files = glob.glob('content/**/*.md', recursive=True)
for fp in all_files:
    relpath = fp.replace(chr(92), '/')
    with open(fp, 'r', encoding='utf-8') as f:
         content = f.read()

    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
         continue
    body = parts[2].strip()

    ai_traces = ['(TL;DR)', 'En conclusión', 'En conclusion', 'En resumen', 'This article explores', 'Este articulo explora']
    for t in ai_traces:
        if t.lower() in body.lower():
            errors.append(f'FAIL_AI_TRACE: {t} in {relpath}')

    methodology_en_count = len(re.findall(r'(?i)Methodology and Sources', body))
    if methodology_en_count > 1:
        errors.append(f'FAIL_DOUBLE_METH_EN: {relpath}')
    methodology_es_count = len(re.findall(r'(?i)Metodología y Fuentes', body))
    if methodology_es_count > 1:
        errors.append(f'FAIL_DOUBLE_METH_ES: {relpath}')

    disclaimer_count = len(re.findall(r'(?i)\*(?:Editorial Disclosure|Aviso Editorial)', body))
    if disclaimer_count > 1:
        errors.append(f'FAIL_DOUBLE_DISC: {relpath}')

    if re.search(r'\]\(\s*/(?:en|es)/?\s*\)', body):
        errors.append(f'FAIL_GENERIC_LINK: {relpath}')

    if re.search(r'\]\(\s*#\s*\)', body):
        errors.append(f'FAIL_EMPTY_LINK: {relpath}')

    clean_body = body
    for marker in ['## Metodología', '## Methodology', '## Artículos Relacionados', '## Related Articles', '---']:
        if marker in clean_body:
            clean_body = clean_body.split(marker)[0].strip()
            
    clean_body = re.sub(r'(?i)\n*\*(?:Editorial Disclosure|Aviso Editorial).*?\*$', '', clean_body, flags=re.DOTALL).strip()
    
    if clean_body:
        last_char = clean_body[-1]
        valid_terminals = ['.', '!', '?', '>', '*', ']', '_', '}', '|', '"', "'", ')', '`', '>']
        if last_char not in valid_terminals:
            # Check if it ends in a markdown link/image or html tag <something>
            if not clean_body.endswith(')') and not clean_body.endswith('```'):
                if last_char.isalnum() or last_char in [',', ';', ':']:
                    errors.append(f'FAIL_TRUNCATED: ends with {repr(last_char)} in {relpath}')

    if '/en/' in relpath:
        if 'en breve' in body.lower() or 'en resumen' in body.lower():
            errors.append(f'FAIL_SPANISH_BLEED: {relpath}')
    if '/es/' in relpath:
        if 'in brief' in body.lower() or 'in summary' in body.lower() or 'related articles' in body.lower():
             errors.append(f'FAIL_ENGLISH_BLEED: {relpath}')

with open('tmp/verify3.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(errors))
print(f'Errors found: {len(errors)}')
