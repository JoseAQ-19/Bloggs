#!/usr/bin/env python3
"""
Script exhaustivo de limpieza de JSON-LD y Scripts en Contenido Markdown.
Elimina:
1. Bloques <script...>...</script> de JSON-LD
2. Bloques de JSON desnudos {"@context": "https://schema.org", ...}
3. Etiquetas huérfanas </script> y <script...>
4. Secciones residuales del LLM de schema markup
5. Extrae FAQs del JSON-LD al frontmatter YAML si el artículo no las tiene.
"""

import os
import re
import sys
import json
import yaml
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

def clean_markdown_content(content: str) -> str:
    """Limpia todo residuo de scripts y JSON-LD del contenido markdown."""
    if not content.strip():
        return content

    # 1. Separar Frontmatter del Cuerpo
    fm_dict = None
    body = content
    has_fm = False

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            has_fm = True
            fm_raw = parts[1]
            body = parts[2]
            try:
                fm_dict = yaml.safe_load(fm_raw)
                if not isinstance(fm_dict, dict):
                    fm_dict = None
            except Exception:
                fm_dict = None

    # 2. Rescatar FAQs del cuerpo si existen antes de limpiar
    extracted_faqs = []
    
    # Buscar patrones JSON que contengan @context y FAQPage
    faq_json_matches = re.finditer(r'\{[^{}]*"@context"\s*:\s*"https?://schema\.org"[^{}]*"@type"\s*:\s*"FAQPage".*?\}\s*(?:</script>)?', body, re.DOTALL)
    for m in faq_json_matches:
        try:
            # Intentar limpiar </script> final para json.loads
            raw_json = m.group(0).replace('</script>', '').strip()
            # Si le faltan llaves de cierre, intentar arreglar
            data = json.loads(raw_json)
            if isinstance(data, dict) and "mainEntity" in data:
                for item in data["mainEntity"]:
                    q = item.get("name")
                    a = item.get("acceptedAnswer", {}).get("text") if isinstance(item.get("acceptedAnswer"), dict) else None
                    if q and a:
                        extracted_faqs.append({"question": q, "answer": a})
        except Exception:
            pass

    # 3. Eliminar cualquier bloque <script ...>...</script>
    body = re.sub(r'<script\b[^>]*>.*?</script>', '', body, flags=re.DOTALL | re.IGNORECASE)

    # 4. Eliminar bloques JSON desnudos que tengan "@context": "https://schema.org" o similar
    # Regex robusta para capturar desde { "@context"... hasta el balanceo o fin de bloque / </script>
    body = re.sub(r'\{\s*"@context"\s*:\s*"https?://schema\.org".*?\}\s*(?:</script>)?', '', body, flags=re.DOTALL | re.IGNORECASE)
    
    # 5. Eliminar cualquier etiqueta suelta <script...> o </script>
    body = re.sub(r'</?script\b[^>]*>', '', body, flags=re.IGNORECASE)

    # 6. Eliminar encabezados markdown residuales sobre el Schema del LLM
    body = re.sub(r'(?i)\*\*JSON-LD:\*\*.*?\n', '', body)
    body = re.sub(r'(?im)^#{2,3}\s*(?:Schema Markup|Metadatos SEO|Structured Data).*?\n', '', body)
    body = re.sub(r'(?i)\*\*(?:Data|FAQ) Schema\*\*\s*\n', '', body)

    # 7. Si rescatamos FAQs y el frontmatter no tiene faq:, agregarlas
    if extracted_faqs and fm_dict is not None and "faq" not in fm_dict:
        fm_dict["faq"] = extracted_faqs

    # 8. Reconstruir archivo
    body_clean = re.sub(r'\n{3,}', '\n\n', body).strip() + '\n'

    if has_fm and fm_dict is not None:
        new_fm = yaml.dump(fm_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return f"---\n{new_fm}---\n\n{body_clean}"
    elif has_fm:
        # Frontmatter existía pero no era dict válido, preservar raw
        return f"---{parts[1]}---\n\n{body_clean}"
    else:
        return body_clean

def main():
    print(f"Iniciando limpieza profunda de JSON-LD y Scripts en: {CONTENT_DIR}")
    scanned = 0
    modified = 0

    for root, _, files in os.walk(CONTENT_DIR):
        for f in files:
            if f.endswith(".md"):
                scanned += 1
                p = Path(root) / f
                try:
                    content = p.read_text(encoding="utf-8")
                    cleaned = clean_markdown_content(content)
                    if cleaned != content:
                        p.write_text(cleaned, encoding="utf-8")
                        modified += 1
                except Exception as e:
                    print(f"Error procesando {p}: {e}")

    print(f"\nLimpieza profunda completada:")
    print(f"- Archivos escaneados: {scanned}")
    print(f"- Archivos modificados: {modified}")

if __name__ == "__main__":
    main()
