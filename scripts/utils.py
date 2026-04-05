import os
import json
import requests
import re
import unicodedata
import time
import random
import urllib.parse
from pathlib import Path

class SlugManager:
    @staticmethod
    def generate(text):
        """Genera un slug SEO-friendly determinista."""
        if not text: return f"post-{int(time.time())}"
        slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        slug = slug.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]

    @staticmethod
    def sanitize(text):
        """Limpia basura de IA (Option 1, Title:, etc)."""
        if not text: return "Untitled"
        # Eliminar prefijos de lista o meta-texto
        text = re.sub(r'^(Option \d+|Opción \d+|Title:|Título:|Subject:|Suggestion:)\s*[:\-\.]?\s*', '', text, flags=re.IGNORECASE)
        # Eliminar asteriscos markdown y comillas
        text = text.replace('*', '').strip().strip('"').strip("'")
        return text

class ImageManager:
    STATIC_DIR = "static/images/uploads"
    DEFAULT_DIR = "static/images/defaults"

    @staticmethod
    def download_image(url, filename_base):
        """
        Descarga una imagen de una URL y la guarda localmente con un nombre SEO.
        """
        if not url: return ""

        try:
            os.makedirs(ImageManager.STATIC_DIR, exist_ok=True)
            safe_name = SlugManager.generate(filename_base)
            filename = f"{safe_name}.jpg"
            local_path = os.path.join(ImageManager.STATIC_DIR, filename)

            # Timeout forzado para evitar procesos zombie
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return f"/images/uploads/{filename}"
            else:
                return ""
        except Exception:
            return ""

import glob
class LinkManager:
    @staticmethod
    def get_latest_internal_links(lang="es", category=None, limit=5):
        """Obtiene los últimos artículos publicados para enlazado interno (Siloed)."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if category:
            search_pattern = os.path.join(base_dir, "content", lang, category, "*.md")
        else:
            search_pattern = os.path.join(base_dir, "content", lang, "**", "*.md")
            
        files = glob.glob(search_pattern, recursive=True)
        
        # Fallback if category has no enough files
        if category and len(files) < limit:
            fallback_pattern = os.path.join(base_dir, "content", lang, "**", "*.md")
            files += [f for f in glob.glob(fallback_pattern, recursive=True) if f not in files]
            
        files.sort(key=os.path.getmtime, reverse=True)
        
        links = []
        for fpath in files:
            if len(links) >= limit:
                break
            if os.path.basename(fpath).startswith("_index"): 
                continue
                
            title = ""
            slug = ""
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read(1000) # Only read start of file
                    m = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
                    if m: title = m.group(1).strip()
                    m_slug = re.search(r'^slug:\s*"?([^"\n]+)"?', content, re.MULTILINE)
                    if m_slug: slug = m_slug.group(1).strip()
                    else: slug = os.path.basename(fpath).replace(".md", "")
            except Exception:
                continue
                
            if title and slug:
                # Determinar categoría real para el link
                rel_path = os.path.relpath(fpath, os.path.join(base_dir, "content", lang))
                parts = rel_path.replace('\\', '/').split('/')
                
                final_cat = parts[0] if len(parts) >= 2 else ""
                url = f"/{lang}/{final_cat}/{slug}/" if final_cat else f"/{lang}/{slug}/"
                links.append({"title": title, "url": url})
                    
        return links

class ContentCleaner:
    @staticmethod
    def ruthless_clean(text):
        """
        Purger de metadatos JSON crudos y artefactos de IA.
        Garantiza que NINGÚN JSON se filtre en el body del artículo a menos que esté en un <script>.
        Maneja JSONs anidados mediante balanceo de llaves.
        """
        if not text:
            return text

        # 1. PRESERVAR bloques <script> de JSON-LD y limpiar artefactos markdown alrededor
        # Ya no eliminamos los tags, permitimos que el LLM pase el Schema SEO válido.
        text = re.sub(r'(?i)```html\n?(<script type="application/ld\+json">.*?</script>)\n?```', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'(?i)```json\n?(\{.*?"@context".*?\})\n?```', r'<script type="application/ld+json">\n\1\n</script>', text, flags=re.DOTALL)

        # 3. Eliminar posibles encabezados markdown de la IA sobre el JSON
        text = re.sub(r'(?i)\*\*JSON-LD:\*\*.*?\n', '', text)
        text = re.sub(r'(?i)### Metadatos SEO.*?\n', '', text)
        text = re.sub(r'(?i)\*\*(?:Data|FAQ) Schema\*\*\s*\n', '', text)

        # 4. Limpieza final de espacios duplicados
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    @staticmethod
    def sanitize_body(text):
        """
        Parser CRÍTICO: Amputa fugas de frontmatter (yaml/json), líneas de metadatos
        y cualquier intento del LLM de escribir las secciones finales reservadas
        (Metodología/Fuentes + Artículos relacionados). Python SIEMPRE manda.
        """
        if not text:
            return text

        # 1. Eliminar cualquier bloque ```yaml ... ``` o ```json ... ``` que pueda ser frontmatter
        text = re.sub(r'(?i)```(?:yaml|json|markdown)\s*\n.*?(?:title:|slug:|translationKey:).*?```', '', text, flags=re.DOTALL)

        # 2. Eliminar bloque --- ... --- si aparece al principio del contenido
        text = re.sub(r'^---\s*?\n.*?\n---\s*?\n', '', text, flags=re.DOTALL)

        # 3. Remover fugas crudas de metadatos sueltos.
        # Identificamos líneas que empiecen con metadatos de Hugo.
        lines = text.split('\n')
        clean_lines = []
        meta_keys = ['title:', 'slug:', 'translationKey:', 'description:', 'categories:', 'date:', 'language:']

        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(mk) for mk in meta_keys) and len(stripped) < 200:
                # Omitir esta línea de metadato filtrada
                continue
            # Delete markdown codeblocks if they are just wrapping the text
            if stripped == '```' or stripped.startswith('```markdown'):
                continue
            clean_lines.append(line)

        clean_text = '\n'.join(clean_lines)

        # 4. Mutilar cualquier intento del LLM de escribir las secciones de
        #    "Metodología y Fuentes" / "Methodology and Sources" o
        #    "Artículos relacionados" / "Related Articles". A partir del primer
        #    marcador conocido, sólo conservamos el cuerpo previo; el footer
        #    oficial se inyecta de forma determinista más adelante.
        footer_split_markers = [
            r"##\s+Metodolog[ií]a y Fuentes",
            r"##\s+Methodology and Sources",
            r"##\s+Fuentes",
            r"##\s+Sources",
            r"##\s+Art[íi]culos relacionados",
            r"##\s+Related Articles",
        ]

        for pattern in footer_split_markers:
            m = re.search(pattern, clean_text, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                clean_text = clean_text[:m.start()].rstrip()
                break

        # 5. Limpieza final de saltos de línea
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        return clean_text.strip()


def inject_adsterra_native_block(body: str, lang: str, fallback_to_first_h2: bool = False) -> str:
    """Inyecta el shortcode {{< adsterra_native >}} tras Resumen Ejecutivo / Executive Summary.

    - Busca el primer encabezado TL;DR (## Resumen Ejecutivo / ## Executive Summary).
    - Inserta el shortcode justo antes del siguiente encabezado de nivel 2+.
    - Si no encuentra patrón claro, devuelve el cuerpo original sin modificar.
      Opcionalmente, si ``fallback_to_first_h2`` es True, inyecta el bloque
      justo antes del primer encabezado H2/H3 encontrado en el cuerpo
      (útil para Blueprints con bloque BLUF sin encabezado TL;DR).
    """
    if not body:
        return body

    header = "## Resumen Ejecutivo" if lang == "es" else "## Executive Summary"
    idx = body.find(header)

    if idx != -1:
        start = idx + len(header)
        rest = body[start:]

        m = re.search(r"^##\s+.+$|^###\s+.+$", rest, flags=re.MULTILINE)
        if not m:
            return body

        insert_pos = start + m.start()
        shortcode = "\n\n{{< adsterra_native >}}\n\n"
        return body[:insert_pos] + shortcode + body[insert_pos:]

    if not fallback_to_first_h2:
        return body

    # Fallback para contenidos sin encabezado explícito de Resumen Ejecutivo
    m = re.search(r"^##\s+.+$|^###\s+.+$", body, flags=re.MULTILINE)
    if not m:
        return body

    insert_pos = m.start()
    shortcode = "\n\n{{< adsterra_native >}}\n\n"
    return body[:insert_pos] + shortcode + body[insert_pos:]


def generate_methodology_and_related_footer(
    slug,
    lang,
    category,
    body_text,
    scout_urls=None,
    content_dir=None,
):
    """Genera el footer estándar "Metodología y Fuentes" + "Artículos relacionados".

    - Usa ``scout_urls`` si se proporcionan; en caso contrario, lee
      ``data/scout_vault.json`` para el ``slug`` dado.
    - Busca artículos relacionados dentro de ``content_dir`` o, por defecto,
      en ``content/{lang}/{category}``.
    - Ignora y sobreescribe cualquier intento previo del LLM de escribir
      estas secciones: el cuerpo debe llegar ya mutilado por ``sanitize_body``
      y el footer oficial se añade SIEMPRE desde aquí.
    """
    if not body_text:
        return ""

    parts = []

    # 1. Metodología y Fuentes (urls verificadas)
    urls = []
    if scout_urls is not None:
        urls = list(scout_urls)
    else:
        vault_file = "data/scout_vault.json"
        if os.path.exists(vault_file):
            try:
                with open(vault_file, "r", encoding="utf-8") as f:
                    vault_data = json.load(f) or {}
                    urls = vault_data.get(slug, []) or []
            except Exception:
                urls = []

    if urls:
        methodology_title = "## Metodología y Fuentes" if lang == "es" else "## Methodology and Sources"
        methodology_block = f"\n\n{methodology_title}\n"
        for u in urls[:5]:
            try:
                domain = urllib.parse.urlparse(u).netloc.replace("www.", "")
            except Exception:
                domain = u
            methodology_block += f"- [{domain}]({u})\n"
        parts.append(methodology_block)

    # 2. Artículos relacionados internos
    base_dir = content_dir or os.path.join("content", lang, category)
    pattern = os.path.join(base_dir, "*.md")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:30]
    candidates = []

    for fpath in files:
        cur_slug = os.path.basename(fpath).replace(".md", "")
        if cur_slug == slug or cur_slug == "_index":
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content_start = f.read(500)
            m = re.search(r'^title:\s*"?([^"\n]+)"?', content_start, re.MULTILINE)
            if not m:
                continue
            f_title = m.group(1).strip().strip('"').strip("'")
            candidates.append((f_title, cur_slug))
        except Exception:
            continue

    if candidates:
        random.shuffle(candidates)
        sampled = candidates[:3]
        if sampled:
            related_title = "## Artículos relacionados" if lang == "es" else "## Related Articles"
            related_block = f"\n\n{related_title}\n"
            for f_title, cur_slug in sampled:
                if lang == "es":
                    rel_path = f"/es/{category}/{cur_slug}/"
                else:
                    # EN está montado en raíz /{category}/{slug}/
                    rel_path = f"/{category}/{cur_slug}/"
                related_block += f"- [{f_title}]({rel_path})\n"
            parts.append(related_block)

    if not parts:
        return ""

    return "".join(parts)


