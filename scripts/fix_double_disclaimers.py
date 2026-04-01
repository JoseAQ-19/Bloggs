import os
import glob
import re

def fix_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Identify the OLD Disclaimer patterns to remove
    # Pattern 1: ⚠️ IMPORTANTE DISCLAIMER: ... to the end of the line or paragraph
    old_disclaimer_pattern = r'#*\s*⚠️\s+\*\*IMPORTANTE DISCLAIMER:\*\*.*?(?=\n\n|\Z)'
    # Pattern 2: *This article is for informational purposes only...*
    generic_disclaimer_pattern = r'\*This article is for informational purposes only.*?\*'
    
    # Remove them (including surrounding separators)
    content = re.sub(old_disclaimer_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(generic_disclaimer_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)

    # 2. Clean up "broken" new disclaimers (the ones starting with #*)
    # They should be just *Aviso YMYL:*
    content = re.sub(r'#+\s*\*Aviso YMYL:', '*Aviso YMYL:', content)
    content = re.sub(r'#+\s*\*YMYL Disclaimer:', '*YMYL Disclaimer:', content)

    # 3. Handle specific double separators
    content = re.sub(r'---\s+---', '---', content)
    
    # 4. Final Polish: Ensure ONLY ONE disclaimer exists at the very end
    # We remove any existing Aviso YMYL / YMYL Disclaimer and re-inject it systematically
    # before the Methodology or Related Articles.
    
    # Pattern to match our OWN new disclaimer
    new_disclaimer_regex = r'\*(Aviso YMYL|YMYL Disclaimer):.*?\*'
    
    match = re.search(new_disclaimer_regex, content)
    disclaimer_text = match.group(0) if match else None
    
    if not disclaimer_text:
        # Fallback to a standard one based on language
        if '/es/' in filepath:
            disclaimer_text = "*Aviso YMYL: La información de este artículo es educativa y no constituye asesoramiento profesional. Consulte a un especialista antes de tomar decisiones financieras o de salud.*"
        else:
            disclaimer_text = "*YMYL Disclaimer: This article is for informational purposes only and does not constitute professional advice. Always consult a certified specialist before making financial or health-related decisions.*"

    # Remove all instances of the new disclaimer first
    content = re.sub(new_disclaimer_regex, '', content)

    # Clean up trailing whitespace and dashes
    content = content.strip()
    content = re.sub(r'\n---\n$', '', content)
    
    # Now, find the strategic spot: Before Methodology or End
    if "## Metodología y Fuentes" in content:
        content = content.replace("## Metodología y Fuentes", f"{disclaimer_text}\n\n## Metodología y Fuentes")
    elif "## Methodology and Sources" in content:
        content = content.replace("## Methodology and Sources", f"{disclaimer_text}\n\n## Methodology and Sources")
    elif "## Related Articles" in content:
         content = content.replace("## Related Articles", f"{disclaimer_text}\n\n## Related Articles")
    else:
        content = content + f"\n\n---\n\n{disclaimer_text}"

    # Clean redundant newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

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
            if fix_article(art):
                count += 1
        except Exception as e:
            print(f"Error fixed {art}: {e}")
    print(f"FIN: Procesados {count} artículos.")
