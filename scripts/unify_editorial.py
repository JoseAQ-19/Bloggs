import os
import glob
import re

def polish_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Rename "Executive Summary (TL;DR)" to more human names
    if '/es/' in filepath:
        content = content.replace('## Resumen Ejecutivo (TL;DR)', '## En Breve')
    else:
        content = content.replace('## Executive Summary (TL;DR)', '## Key Insights')

    # 2. Fix Double Images in the same section
    # Search for Markdown images ![...] (path)
    img_pattern = r'!\[.*?\]\(.*?\)'
    imgs = re.findall(img_pattern, content)
    
    if len(imgs) > 1:
        # If we have multiple images with the SAME path, remove the second one
        seen_paths = set()
        new_content_lines = []
        for line in content.split('\n'):
            line_imgs = re.findall(img_pattern, line)
            keep_line = True
            for img in line_imgs:
                path = re.search(r'\((.*?)\)', img).group(1)
                if path in seen_paths:
                    # Duplicate found! We remove it from the line
                    line = line.replace(img, '').strip()
                    if not line or line == '*': # If line is just a bullet point, remove it
                        keep_line = False
                else:
                    seen_paths.add(path)
            if keep_line:
                new_content_lines.append(line)
        content = '\n'.join(new_content_lines)

    # 3. Clean up the "TL;DR" bullet points if they are empty or broken
    content = content.replace('* \n', '')
    
    # 4. Standardize the YMYL Disclaimer to [!TIP] or something elegant
    # Actually User liked the cursive one but wanted things to not look robotic.
    # I'll change "YMYL Disclaimer" to "Aviso Editorial" (ES) or "Editorial Disclosure" (EN)
    content = content.replace('*YMYL Disclaimer:', '*Aviso Editorial:*')
    content = content.replace('*Aviso YMYL:', '*Aviso Editorial:*')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

if __name__ == "__main__":
    articles = glob.glob('content/**/*.md', recursive=True)
    count = 0
    for art in articles:
        if '_index.md' in art: continue
        if any(x in art for x in ['contact', 'about', 'privacy', 'terms']): continue
        try:
            if polish_article(art):
                count += 1
        except Exception as e:
            print(f"Error polishing {art}: {e}")
    print(f"FIN: Pulidos {count} artículos.")
