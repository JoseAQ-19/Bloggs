#!/usr/bin/env python3
"""Auditor "Sheriff" para posts .md.

Escanea los .md recientes bajo content/ y valida:
- Presencia y posición de {{< adsterra_native >}}
- Presencia de secciones de footer (Metodología/Fuentes + Artículos relacionados)
- Enlaces externos contra los vaults de URLs verificados (scout_vault/source_links).

Uso básico:
  python scripts/audit_posts.py --limit 40 --lang es
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from urllib.parse import urlparse


# Configurar stdout/stderr para UTF-8 en Windows y evitar errores de "charmap"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


RE_AD = re.compile(r"\{\{<\s*adsterra_native\s*>\}\}")
RE_H2_H3 = re.compile(r"^(##|###)\s+.+$", re.MULTILINE)
RE_HEADER_TLDR_ES = "## Resumen Ejecutivo"
RE_HEADER_TLDR_EN = "## Executive Summary"
RE_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
RE_RAW_URL = re.compile(r"https?://[^\s)\]\"'<>]+")
RE_JSON_LD_SCRIPT = re.compile(
    r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>.*?</script>",
    re.IGNORECASE | re.DOTALL,
)

STRUCTURAL_WHITELIST_DOMAINS = {
    "schema.org",
    "www.schema.org",
}


def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def extract_frontmatter(text):
    """Devuelve (frontmatter_str, body_str)."""
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    end += len("\n---")
    return text[4:end - len("\n---")], text[end + 1 :]


def get_lang_from_path(path, fm):
    m = re.search(r"^language:\s*\"?([^\"\n]+)\"?", fm, re.MULTILINE)
    if m:
        return m.group(1).strip()
    parts = Path(path).parts
    try:
        idx = parts.index("content")
        if len(parts) > idx + 1:
            return parts[idx + 1]
    except ValueError:
        pass
    return "es"


def get_slug_from_frontmatter(path, fm):
    m = re.search(r"^slug:\s*\"?([^\"\n]+)\"?", fm, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return Path(path).stem


def is_static_page(path):
    filename = Path(path).name.lower()
    if filename in {"about.md", "contact.md", "contacto.md", "privacy.md", "terms-of-service.md"}:
        return True
    # Raíz content/es/*.md o content/en/*.md sin subcarpeta
    parts = Path(path).parts
    try:
        idx = parts.index("content")
        return len(parts) == idx + 3  # content / lang / filename
    except ValueError:
        return False


def check_ad_position(body, lang):
    errors = []

    m_ad = RE_AD.search(body)
    if not m_ad:
        errors.append("falta anuncio Adsterra")
        return errors

    ad_start = m_ad.start()

    header = RE_HEADER_TLDR_ES if lang == "es" else RE_HEADER_TLDR_EN
    idx_header = body.find(header)

    if idx_header != -1:
        # Caso core/funds: ad entre TL;DR y primer H2/H3 posterior
        after = body[idx_header + len(header) :]
        m_next = RE_H2_H3.search(after)
        if not m_next:
            errors.append("no se encontró H2/H3 tras el Resumen Ejecutivo")
            return errors
        h2_pos = idx_header + len(header) + m_next.start()
        if not (idx_header < ad_start < h2_pos):
            errors.append("anuncio fuera de posición (debe ir tras el Resumen Ejecutivo y antes del siguiente H2/H3)")
        return errors

    # Fallback (blueprints): ad antes del primer H2/H3 global
    m_first = RE_H2_H3.search(body)
    if not m_first:
        # No hay H2/H3; aceptamos presencia del anuncio sin validar posición
        return errors
    if not ad_start < m_first.start():
        errors.append("anuncio fuera de posición (blueprint: debe ir antes del primer H2/H3)")
    return errors


def check_footer_sections(body, lang):
    errors = []
    if lang == "es":
        m1 = "## Metodología y Fuentes"
        m2 = "## Artículos relacionados"
    else:
        m1 = "## Methodology and Sources"
        m2 = "## Related Articles"

    i1 = body.find(m1)
    i2 = body.find(m2)
    if i1 == -1 or i2 == -1:
        missing = []
        if i1 == -1:
            missing.append("Metodología/Methodology")
        if i2 == -1:
            missing.append("Artículos relacionados/Related Articles")
        errors.append("footer incompleto (faltan: " + ", ".join(missing) + ")")
    elif i1 > i2:
        errors.append("footer desordenado (Metodología debe ir antes que Artículos relacionados)")
    return errors


def collect_allowed_urls(slug, lang, scout_vault, source_links_es, source_links_en):
    urls = set()
    urls.update(scout_vault.get(slug, []))
    if lang == "es":
        urls.update(source_links_es.get(slug, []))
    else:
        urls.update(source_links_en.get(slug, []))
    # Normalizar quitando puntuación final común
    cleaned = set()
    strip_chars = ".,;:!?)\"']"
    for u in urls:
        cleaned.add(u.rstrip(strip_chars))
    return cleaned


def _strip_json_ld_scripts(body):
    """Elimina bloques <script type="application/ld+json"> ... </script> antes de extraer URLs."""
    return RE_JSON_LD_SCRIPT.sub("", body)


def extract_external_links(body):
    body = _strip_json_ld_scripts(body)
    urls = set()
    for _anchor, url in RE_LINK.findall(body):
        urls.add(url)
    for url in RE_RAW_URL.findall(body):
        urls.add(url)
    externals = set()
    strip_chars = ".,;:!?)\"']"
    for url in urls:
        if url.startswith("/"):
            continue
        if "novumworld.com" in url:
            continue
        base = url.split("?", 1)[0].split("#", 1)[0]
        parsed = urlparse(base)
        if parsed.netloc.lower() in STRUCTURAL_WHITELIST_DOMAINS:
            continue
        if base.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        externals.add(url.rstrip(strip_chars))
    return externals


def audit_file(path, scout_vault, source_links_es, source_links_en):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return [f"error leyendo archivo: {e}"]

    fm, body = extract_frontmatter(text)
    lang = get_lang_from_path(path, fm)
    slug = get_slug_from_frontmatter(path, fm)

    # Saltar páginas estáticas
    if is_static_page(path):
        return []

    errors = []
    errors.extend(check_ad_position(body, lang))
    errors.extend(check_footer_sections(body, lang))

    allowed = collect_allowed_urls(slug, lang, scout_vault, source_links_es, source_links_en)
    used = extract_external_links(body)

    invented = [u for u in sorted(used) if u not in allowed]
    if invented:
        errors.append(
            "links inventados/no en vault ({}): {}".format(
                len(invented), ", ".join(invented)
            )
        )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Audita posts .md recientes (ads, footer, enlaces)")
    parser.add_argument("--limit", type=int, default=40, help="Número máximo de archivos recientes a auditar")
    parser.add_argument("--lang", choices=["es", "en", "all"], default="all", help="Filtrar por idioma (según ruta content/es|en)")
    parser.add_argument("--file", help="Ruta a un archivo .md específico a auditar")
    args = parser.parse_args()

    scout_vault = load_json("data/scout_vault.json")
    source_es = load_json("data/source_links_es.json")
    source_en = load_json("data/source_links_en.json")

    # Modo archivo único
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ ERROR: No se encontró el archivo '{args.file}'.")
            sys.exit(1)

        errors = audit_file(str(path), scout_vault, source_es, source_en)
        rel = path.as_posix()
        if errors:
            print(f"❌ ERROR  {rel}")
            for e in errors:
                print(f"   - {e}")
            print("\nResumen:")
            print("   Total archivos auditados: 1")
            print("   OK: 0")
            print("   Con errores: 1")
            sys.exit(1)
        else:
            print(f"✅ OK     {rel}")
            print("\nResumen:")
            print("   Total archivos auditados: 1")
            print("   OK: 1")
            print("   Con errores: 0")
            return

    root = Path("content")
    if not root.exists():
        print("❌ ERROR: No se encontró el directorio 'content/'.")
        sys.exit(1)

    all_md = [p for p in root.rglob("*.md")]
    if args.lang != "all":
        all_md = [p for p in all_md if f"{os.sep}{args.lang}{os.sep}" in str(p)]

    all_md.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    targets = all_md[: args.limit]

    total = 0
    failed = 0

    for path in targets:
        rel = path.as_posix()
        total += 1
        errors = audit_file(str(path), scout_vault, source_es, source_en)
        if errors:
            failed += 1
            print(f"❌ ERROR  {rel}")
            for e in errors:
                print(f"   - {e}")
        else:
            print(f"✅ OK     {rel}")

    print("\nResumen:")
    print(f"   Total archivos auditados: {total}")
    print(f"   OK: {total - failed}")
    print(f"   Con errores: {failed}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
