import os
import glob
import re
import frontmatter

# Regex Emojis
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u26ff]|[\u2700-\u27bf]', flags=re.UNICODE)

# Disclaimers variation patterns
DISCLAIMER_PATTERNS = [
    r'\*Aviso Editorial:.*?\*',
    r'\*Editorial Disclosure:.*?\*',
    r'⚠️.*?DISCLAIMER.*?',
    r'\[!IMPORTANT\].*?Aviso Editorial.*?',
    r'\[!IMPORTANT\].*?Editorial Disclosure.*?',
    r'### Aviso YMYL:.*?',
    r'^Es importante destacar que el contenido de este artículo tiene un carácter educativo.*?',
    r'\*YMYL Disclaimer:.*?\*',
    r'\*Aviso YMYL:.*?\*'
]

STATS = {"files": 0, "emojis": 0, "leaks": 0, "disclaimers_purged": 0, "headers_fixed": 0}

def surgical_clean(content, lang):
    new_content = content
    
    # 1. Purge Emojis
    orig = new_content
    new_content = EMOJI_PATTERN.sub('', new_content)
    if new_content != orig: STATS["emojis"] += 1

    # 2. Purge Metadata Leaks
    leaks = [r'^title:.*$', r'^slug:.*$', r'^description:.*$', r'^translationKey:.*$', r'^categories:.*$', r'^language:.*$']
    for p in leaks:
        new_content = re.sub(p, '', new_content, flags=re.MULTILINE | re.IGNORECASE)
    
    # 3. Purge ALL Disclaimers (Aggressive Line-by-Line)
    lines = new_content.split('\n')
    cleaned_lines = []
    skip_keywords = ['aviso editorial', 'editorial disclosure', 'ymyl', 'especialista', 'professional advice', 'asesoramiento', 'información educativa', 'informational purposes only', 'consult a certified']
    
    for line in lines:
        if any(kw in line.lower() for kw in skip_keywords):
            # Skip this line entirely
            continue
        cleaned_lines.append(line)
    
    new_content = '\n'.join(cleaned_lines)

    # 4. Humanize Headers (More variations)
    replacements = {
        r'## Resumen Ejecutivo \(TL;DR\)': '## Key Insights',
        r'## Resumen Ejecutivo': '## Key Insights',
        r'## Executive Summary \(TL;DR\)': '## Key Insights',
        r'## Executive Summary': '## Key Insights',
        r'📊 Key Insights / En Breve:': '## Key Insights',
        r'## Metodología y Fuentes / Methodology & Sources': '## Methodology and Sources',
        r'## Metodología y Fuentes': '## Methodology and Sources',
        r'## Metodología': '## Methodology and Sources',
        r'## Methodology': '## Methodology and Sources'
    }

    for old, new in replacements.items():
        if re.search(old, new_content):
            new_content = re.sub(old, new, new_content)
            STATS["headers_fixed"] += 1

    # 5. Injection of SINGLE Unified Disclaimer
    # Define disclaimer
    if lang == 'es':
        disclaimer = "\n\n*Aviso Editorial: La información de este artículo es puramente educativa y no constituye asesoramiento financiero, legal o médico profesional. NovumWorld recomienda consultar con un especialista certificado antes de realizar cualquier inversión o cambio en su régimen de salud.*\n\n"
    else:
        disclaimer = "\n\n*Editorial Disclosure: This content is for educational purposes only and does not constitute professional financial, legal, or medical advice. NovumWorld recommends consulting with a certified specialist before making any investment decisions or health changes.*\n\n"

    # Insert before Methodology if exists, else at end
    methodology_patterns = [r'## Methodology', r'## Metodología', r'## Metodologia']
    found_m = False
    for mp in methodology_patterns:
        match = re.search(mp, new_content, flags=re.IGNORECASE)
        if match:
            start = match.start()
            # Clean up space before methodology
            body = new_content[:start].strip()
            footer = new_content[start:]
            new_content = body + disclaimer + footer
            found_m = True
            break
            
    if not found_m:
        new_content = new_content.strip() + disclaimer
        
    return new_content

def process():
    files = glob.glob('content/**/*.md', recursive=True)
    for f_path in files:
        if '_index.md' in f_path or any(x in f_path for x in ['contact', 'privacy', 'about', 'terms']):
            continue
            
        STATS["files"] += 1
        with open(f_path, 'r', encoding='utf-8') as f:
            try:
                post = frontmatter.load(f)
            except:
                continue
        
        lang = post.get('language', 'en')
        post.content = surgical_clean(post.content, lang)
        
        # Extra protection: ensure double line breaks between H2s
        post.content = re.sub(r'\n(## )', r'\n\n\1', post.content)
        post.content = re.sub(r'\n\n\n+', r'\n\n', post.content)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

if __name__ == "__main__":
    process()
    print(f"✅ Procesados {STATS['files']} archivos.")
    print(f"✨ Emojis: {STATS['emojis']} | Cabeceras: {STATS['headers_fixed']}")
