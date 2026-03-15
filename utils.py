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
        Usa conteo de llaves para manejar correctamente bloques JSON anidados (FAQPage, etc).
        """
        if not text:
            return text

        # 1. ELIMINAR bloques <script> de JSON-LD (Ahora gestionados por layouts/partials/schema.html)
        text = re.sub(r'<script type="application/ld\+json">.*?</script>', '\n\n', text, flags=re.DOTALL | re.IGNORECASE)

        # 2. ATAQUE NUCLEAR con conteo de llaves: eliminar bloques JSON que contengan @context o @type
        # Detecta el inicio de un bloque JSON suelto (línea que solo tiene "{")
        result_lines = []
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped == '{':
                # Recopilar el bloque completo contando llaves
                block_lines = [lines[i]]
                depth = 1
                j = i + 1
                while j < len(lines) and depth > 0:
                    depth += lines[j].count('{') - lines[j].count('}')
                    block_lines.append(lines[j])
                    j += 1
                block_text = '\n'.join(block_lines)
                # Solo eliminar si es JSON-LD (contiene @context o @type)
                if '@context' in block_text or ('"@type"' in block_text and '"@' in block_text):
                    # Saltar el bloque, reemplazar con línea vacía
                    result_lines.append('')
                    i = j
                    continue
                else:
                    result_lines.append(lines[i])
                    i += 1
            else:
                result_lines.append(lines[i])
                i += 1
        text = '\n'.join(result_lines)

        # 3. Eliminar posibles encabezados markdown de la IA sobre el JSON
        text = re.sub(r'(?i)\*\*JSON-LD:\*\*.*?\n', '', text)
        text = re.sub(r'(?i)### Metadatos SEO.*?\n', '', text)
        text = re.sub(r'(?i)\*\*(?:Data|FAQ) Schema\*\*\s*\n', '', text)

        # 4. Limpieza final de espacios duplicados
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
