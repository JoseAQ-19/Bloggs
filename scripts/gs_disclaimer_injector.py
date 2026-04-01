import os
import re
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE, "content")

# Categorías que REQUIRE disclaimers según el usuario
DISCLAIMER_NICHES = ["realestate", "funds", "crypto"]

DISCLAIMER_EN = """
---

> [!IMPORTANT]
> **Editorial & YMYL Disclaimer:** The information presented in this article is for educational and informational purposes only. It does not constitute professional advice (medical, legal, financial, or technical). Always consult with a qualified expert before making decisions based on this content. NovumWorld assumes no liability for actions taken based on the information provided here.
"""

DISCLAIMER_ES = """
---

> [!IMPORTANT]
> **Aviso Editorial y YMYL:** La información presentada en este artículo tiene fines únicamente educativos e informativos. No constituye asesoramiento profesional (médico, legal, financiero o técnico). Consulte siempre con un experto calificado antes de tomar decisiones basadas en este contenido. NovumWorld no asume ninguna responsabilidad por las acciones tomadas basadas en la información proporcionada aquí.
"""

def clean_old_disclaimer(content):
    """Elimina disclaimers existentes del principio u otras partes para evitar duplicados."""
    lines = content.split('\n')
    new_lines = []
    skip = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detectar el inicio del bloque de disclaimer
        if "> [!IMPORTANT]" in line and i + 1 < len(lines) and ("Editorial & YMYL Disclaimer" in lines[i+1] or "Aviso Editorial y YMYL" in lines[i+1]):
            skip = True
            i += 1
            continue
        
        if skip:
            # Continuar skipeando líneas que empiezan con > o líneas vacías entre el bloque
            if line.strip().startswith(">") or line.strip() == "":
                i += 1
                continue
            else:
                skip = False
                # Si la línea actual es el separador ---, también lo quitamos si estaba pegado al disclaimer
                if line.strip() == "---":
                    i += 1
                    continue
        
        new_lines.append(line)
        i += 1
    
    return "\n".join(new_lines).strip()

def inject_disclaimer():
    all_md = glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True)
    count_injected = 0
    count_removed = 0

    for filepath in all_md:
        # Normalizar ruta
        norm_path = filepath.replace("\\", "/")
        filename = os.path.basename(filepath)
        
        if filename in ["privacy.md", "terms-of-service.md", "contact.md", "about.md"]:
            continue

        # Identificar nicho
        # Esperamos algo como .../content/es/niche/file.md
        niche = ""
        parts = norm_path.split("/")
        try:
            if "content" in parts:
                c_idx = parts.index("content")
                # parts[c_idx+1] es 'es' or 'en'
                if len(parts) > c_idx + 2:
                    niche = parts[c_idx+2]
        except:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Limpiar previos
        has_old = "Editorial & YMYL Disclaimer" in content or "Aviso Editorial y YMYL" in content
        new_content = content
        if has_old:
            new_content = clean_old_disclaimer(content)
            count_removed += 1

        # Si el nicho no está en la lista blanca, guardar versión limpia si cambió
        if niche not in DISCLAIMER_NICHES:
            if has_old:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            continue

        # Si está en la lista blanca, añadir al FINAL
        is_spanish = "/es/" in norm_path
        disclaimer = DISCLAIMER_ES if is_spanish else DISCLAIMER_EN
        
        final_text = new_content.strip() + "\n" + disclaimer.strip() + "\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_text)
        count_injected += 1

    print(f"DONE: Injected {count_injected} at END. Removed/Cleaned {count_removed} others.")

if __name__ == "__main__":
    inject_disclaimer()
