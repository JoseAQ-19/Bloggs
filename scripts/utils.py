import os
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
        Parser CRÍTICO: Amputa fugas de frontmatter (yaml/json) y líneas de metadatos
        que el LLM haya vomitado dentro del cuerpo del texto, evitando doble frontmatter.
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
        skip_mode = False
        meta_keys = ['title:', 'slug:', 'translationKey:', 'description:', 'categories:', 'date:', 'language:']
        
        for line in lines:
            stripped = line.strip()
            # If line is exactly --- and we recently saw meta, we might be inside a leaked block,
            # but usually it's just raw text.
            if any(stripped.startswith(mk) for mk in meta_keys) and len(stripped) < 200:
                continue # Omitir esta línea de metadato filtrada
            # Delete markdown codeblocks if they are just wrapping the text
            if stripped == '```' or stripped.startswith('```markdown'):
                continue
            clean_lines.append(line)
            
        # 4. Unir y limpiar
        clean_text = '\n'.join(clean_lines)
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        return clean_text.strip()

