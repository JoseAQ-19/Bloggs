import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE, "content")

DISCLAIMER_EN = """
> [!IMPORTANT]
> **Editorial & YMYL Disclaimer:** The information presented in this article is for educational and informational purposes only. It does not constitute professional advice (medical, legal, financial, or technical). Always consult with a qualified expert before making decisions based on this content. NovumWorld assumes no liability for actions taken based on the information provided here.
"""

DISCLAIMER_ES = """
> [!IMPORTANT]
> **Aviso Editorial y YMYL:** La información presentada en este artículo tiene fines únicamente educativos e informativos. No constituye asesoramiento profesional (médico, legal, financiero o técnico). Consulte siempre con un experto caligicado antes de tomar decisiones basadas en este contenido. NovumWorld no asume ninguna responsabilidad por las acciones tomadas basadas en la información proporcionada aquí.
"""

def inject_disclaimer():
    all_md = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)
    count = 0

    for filepath in all_md:
        # Skip special pages if needed (privacy, terms, etc. already have their own or don't need it)
        filename = os.path.basename(filepath)
        if filename in ["privacy.md", "terms-of-service.md", "contact.md", "about.md"]:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Determine language
        is_spanish = "content\\es\\" in filepath or "content/es/" in filepath
        disclaimer = DISCLAIMER_ES if is_spanish else DISCLAIMER_EN

        # Check if already has a disclaimer (to avoid double injection)
        if "Editorial & YMYL Disclaimer" in content or "Aviso Editorial y YMYL" in content:
            continue

        # Find the end of frontmatter
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Inject after frontmatter
            header = parts[1]
            body = parts[2].strip()
            
            # Check if there is a featured image as the first thing in body
            # Pattern: ![alt text](/path/to/image.jpg)
            img_match = re.match(r'(!\[.*?\]\(.*?\))', body)
            
            if img_match:
                img_tag = img_match.group(1)
                rest_of_body = body[len(img_tag):].strip()
                new_content = f"---{header}---\n{img_tag}\n\n{disclaimer.strip()}\n\n{rest_of_body}"
            else:
                new_content = f"---{header}---\n\n{disclaimer.strip()}\n\n{body}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1

    print(f"✅ Injected disclaimers into {count} articles.")

if __name__ == "__main__":
    inject_disclaimer()
