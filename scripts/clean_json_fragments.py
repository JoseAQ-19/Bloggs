#!/usr/bin/env python3
"""
Eliminador definitivo de bloques y fragmentos JSON-LD / @context en markdown.
"""

import os
import re
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

def remove_jsonld_fragments(content: str) -> str:
    lines = content.splitlines(keepends=True)
    out_lines = []
    in_json = False
    brace_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Si detectamos @context o @type o inicio de JSON schema
        if '"@context"' in line or '"@type"' in line and any(k in line for k in ["NewsArticle", "Article", "FAQPage", "WebPage", "BreadcrumbList"]):
            in_json = True
            # Si la línea anterior era solo '{' o similar y se añadió a out_lines, removerla
            if out_lines and out_lines[-1].strip() == '{':
                out_lines.pop()
            brace_depth += line.count('{') - line.count('}')
            continue

        if in_json:
            brace_depth += line.count('{') - line.count('}')
            # Comprobar si salimos del JSON
            if brace_depth <= 0 and ('}' in line or stripped.startswith('##') or stripped.startswith('---') or stripped.startswith('*')):
                in_json = False
                brace_depth = 0
                # Si la línea era solo '}', la descartamos
                if stripped == '}' or stripped == '},' or stripped == '</script>':
                    continue
                # Si la línea es contenido real como ## Related Articles, conservarla
                if stripped.startswith('##') or stripped.startswith('---') or stripped.startswith('*'):
                    out_lines.append(line)
            continue

        # Si encontramos líneas sueltas de JSON residual
        if stripped in ['</script>', '<script type="application/ld+json">', '<script type="application/ld+json">{}</script>']:
            continue

        out_lines.append(line)

    result = "".join(out_lines)
    # Limpiar saltos de línea repetidos
    result = re.sub(r'\n{3,}', '\n\n', result).strip() + '\n'
    return result

def main():
    modified = 0
    scanned = 0
    for root, _, files in os.walk(CONTENT_DIR):
        for f in files:
            if f.endswith(".md"):
                scanned += 1
                p = Path(root) / f
                content = p.read_text(encoding="utf-8")
                cleaned = remove_jsonld_fragments(content)
                if cleaned != content:
                    p.write_text(cleaned, encoding="utf-8")
                    modified += 1

    print(f"Limpieza de fragmentos completada:")
    print(f"- Escaneados: {scanned}")
    print(f"- Modificados: {modified}")

if __name__ == "__main__":
    main()
