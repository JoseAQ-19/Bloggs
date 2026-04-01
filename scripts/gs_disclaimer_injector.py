import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE, "..", "content") # Adjusted to properly point to content dir

# Categorías que REQUIRE disclaimers según el usuario
DISCLAIMER_NICHES = ["realestate", "funds", "crypto", "fitness"]

DISCLAIMER_EN = "\n*YMYL Disclaimer: This article is for informational purposes only and does not constitute professional advice. Always consult a certified specialist before making financial or health-related decisions.*\n"
DISCLAIMER_ES = "\n*Aviso YMYL: La información de este artículo es educativa y no constituye asesoramiento profesional. Consulte a un especialista antes de tomar decisiones financieras o de salud.*\n"

def clean_old_disclaimer(content):
    """Elimina disclaimers existentes del principio u otras partes para evitar duplicados."""
    lines = content.split('\n')
    new_lines = []
    skip = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect big block disclaimer
        if "> [!IMPORTANT]" in line and i + 1 < len(lines) and ("Editorial & YMYL Disclaimer" in lines[i+1] or "Aviso Editorial y YMYL" in lines[i+1]):
            skip = True
            i += 1
            continue
        
        if skip:
            if line.strip().startswith(">") or line.strip() == "":
                i += 1
                continue
            else:
                skip = False
                if line.strip() == "---":
                    i += 1
                    continue
        
        # Remove already existing subtle disclaimers to avoid duplicates
        if "*YMYL Disclaimer:" in line or "*Aviso YMYL:" in line:
            i += 1
            continue
            
        new_lines.append(line)
        i += 1
    
    return "\n".join(new_lines).strip()

def insert_disclaimer_at_end(content, disclaimer):
    # Determine the best place to insert the disclaimer.
    # Look for trailing sections like Methodology, Sources, Related Articles.
    target_headers = [
        r"(##\s*Metodología\b.*)",
        r"(##\s*Fuentes\b.*)",
        r"(##\s*Artículos Relacionados\b.*)",
        r"(##\s*Methodology\b.*)",
        r"(##\s*Sources\b.*)",
        r"(##\s*Related Articles\b.*)"
    ]
    
    # Check if any target header exists
    for header in target_headers:
        match = re.search(header, content, flags=re.IGNORECASE)
        if match:
            # Insert before the header
            return content[:match.start()] + disclaimer + "\n\n" + content[match.start():]
            
    # If no matching header, just append to the end
    return content.strip() + "\n\n" + disclaimer

def inject_disclaimer():
    all_md = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)
    count_injected = 0
    count_removed = 0

    for filepath in all_md:
        norm_path = filepath.replace("\\", "/")
        filename = os.path.basename(filepath)
        
        if filename in ["privacy.md", "terms-of-service.md", "contact.md", "about.md"]:
            continue

        niche = ""
        parts = norm_path.split("/")
        try:
            if "content" in parts:
                c_idx = parts.index("content")
                if len(parts) > c_idx + 2:
                    niche = parts[c_idx+2]
        except:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        has_old = "Editorial & YMYL Disclaimer" in content or "Aviso Editorial y YMYL" in content or "*YMYL Disclaimer:" in content or "*Aviso YMYL:" in content
        
        new_content = content
        if has_old:
            new_content = clean_old_disclaimer(content)
            count_removed += 1

        if niche not in DISCLAIMER_NICHES:
            if has_old:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            continue

        is_spanish = "/es/" in norm_path
        disclaimer = DISCLAIMER_ES if is_spanish else DISCLAIMER_EN
        
        final_text = insert_disclaimer_at_end(new_content, disclaimer.strip())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_text)
        count_injected += 1

    print(f"DONE: Injected/Refreshed {count_injected} subtle disclaimers at END. Removed/Cleaned {count_removed} others.")

if __name__ == "__main__":
    inject_disclaimer()
