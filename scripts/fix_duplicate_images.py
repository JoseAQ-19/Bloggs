#!/usr/bin/env python3
"""
scripts/fix_duplicate_images.py - Detector y Remediador en Lote de Imágenes Duplicadas.

Analiza todos los artículos Markdown en la carpeta de contenido (content/posts o content/),
identifica imágenes duplicadas (> 1 uso) y regenera imágenes WebP únicas por artículo
con prompts contextuales y semillas determinísticas derivadas del slug.

USO:
    python scripts/fix_duplicate_images.py --dry-run
    python scripts/fix_duplicate_images.py
    python scripts/fix_duplicate_images.py --content-dir content/es
"""

import os
import sys
import argparse
import hashlib
import re
from collections import defaultdict
import frontmatter

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Asegurar importación de módulos en core/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'core'))


from novum_visual import get_image, generate_unique_visual_prompt


def _resolve_local_image(img_ref: str, bundle_dir=None) -> str:
    """Resuelve una referencia de imagen del frontmatter a un archivo local, si existe."""
    if not img_ref or img_ref.startswith("http"):
        return ""
    if img_ref.startswith("/images/"):
        return os.path.join(BASE_DIR, "static", img_ref.lstrip("/"))
    if bundle_dir and not os.path.isabs(img_ref):
        return os.path.join(bundle_dir, img_ref)
    return ""


def _hash_file(path: str) -> str:
    """MD5 del contenido del archivo, o cadena vacía si no se puede leer."""
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
    except Exception:
        pass
    return ""


def extract_category(filepath: str, post: frontmatter.Post) -> str:
    """Extrae la categoría del frontmatter o de la estructura de carpetas."""
    cats = post.get('categories') or post.get('category')
    if cats:
        if isinstance(cats, list) and len(cats) > 0:
            return str(cats[0]).lower()
        elif isinstance(cats, str):
            return cats.lower()
    
    # Inferir desde ruta: content/es/crypto/... -> crypto
    parts = filepath.replace('\\', '/').split('/')
    if "content" in parts:
        idx = parts.index("content")
        # Estructura típica: content/{lang}/{category}/... o content/{category}/...
        if len(parts) > idx + 2 and parts[idx + 1] in ("es", "en"):
            return parts[idx + 2].lower()
        elif len(parts) > idx + 1:
            return parts[idx + 1].lower()
            
    return "ia"


def extract_image_field(post: frontmatter.Post) -> str:
    """Extrae la ruta o URL de la imagen destacada definida en el frontmatter."""
    img = post.get('image') or post.get('featured_image') or post.get('thumbnail') or ""
    if isinstance(img, str):
        return img.strip()
    elif isinstance(img, dict):
        return str(img.get('url', '')).strip()
    return ""


_MARKDOWN_IMAGE_RE = re.compile(
    r'(!\[[^\]]*\]\()(?P<destination><[^>]+>|[^)\s]+)'
    r'(?P<title>\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?\)'
)


def sync_featured_image_in_body(post: frontmatter.Post, image_ref: str) -> None:
    """Keep the first article image aligned with the featured image reference."""
    content = post.content or ""
    match = _MARKDOWN_IMAGE_RE.search(content)
    if match:
        title = match.group("title") or ""
        replacement = f"{match.group(1)}{image_ref}{title})"
        post.content = content[:match.start()] + replacement + content[match.end():]
        return

    title = str(post.get("title") or "Featured image")
    post.content = f"![{title}]({image_ref})\n\n{content.lstrip()}"


def scan_for_duplicates(content_dir: str, categories=None):
    """
    Escanea todos los archivos Markdown en content_dir.

    La agrupación es por CONTENIDO del archivo de imagen (hash MD5), no solo por
    la cadena del frontmatter: el bug de regresión copiaba el default de categoría
    bajo nombres únicos por slug, invisible a una agrupación por ruta.

    Retorna:
      - duplicate_groups: dict[image_key, list[post_info]] para imágenes repetidas > 1 vez.
      - total_scanned: int
    """
    image_to_posts = defaultdict(list)
    total_scanned = 0

    for root, _, files in os.walk(content_dir):
        for filename in files:
            if not filename.endswith(".md"):
                continue
            if filename in ("_index.md", "about.md", "contact.md", "contacto.md", "privacy.md", "terms-of-service.md"):
                continue

            filepath = os.path.join(root, filename)

            try:
                post = frontmatter.load(filepath)
                img_path = extract_image_field(post)

                slug = post.get('slug')
                if not slug:
                    if filename == "index.md":
                        slug = os.path.basename(root)
                    else:
                        slug = os.path.splitext(filename)[0]

                title = post.get('title', 'Sin Título')
                desc = post.get('description', '')
                if not desc:
                    desc = post.content[:300] if post.content else title

                category = extract_category(filepath, post)
                if categories and category not in categories:
                    continue

                total_scanned += 1
                bundle_dir = root if filename == "index.md" else None

                post_info = {
                    'filepath': filepath,
                    'filename': filename,
                    'is_leaf_bundle': filename == "index.md",
                    'bundle_dir': bundle_dir,
                    'slug': slug,
                    'title': title,
                    'desc': desc,
                    'category': category,
                    'current_image': img_path,
                    'post_obj': post
                }

                if not img_path:
                    # Sin imagen se agrupa como vacía para ser tratada como duplicada/falta
                    image_to_posts["__MISSING_IMAGE__"].append(post_info)
                    continue

                # Clave de agrupación: hash del contenido si el archivo existe;
                # si no, la propia referencia (mantiene detección clásica por ruta).
                local_file = _resolve_local_image(img_path, bundle_dir)
                content_hash = _hash_file(local_file)
                group_key = f"hash:{content_hash}" if content_hash else img_path
                post_info['image_hash'] = content_hash
                image_to_posts[group_key].append(post_info)

            except Exception as e:
                print(f"⚠️ Error leyendo {filepath}: {e}")

    # Filtrar solo las imágenes que se repiten más de 1 vez
    duplicate_groups = {}
    for key, posts in image_to_posts.items():
        if len(posts) <= 1:
            continue
        # Clave legible: la referencia compartida si todos la comparten, si no, el hash.
        refs = {p['current_image'] for p in posts}
        canonical = posts[0]['current_image'] if len(refs) == 1 else key
        duplicate_groups[canonical] = posts
    return duplicate_groups, total_scanned


def remediate_duplicate_images(duplicate_groups: dict, dry_run: bool = False):
    """
    Ejecuta el proceso de auditoría (--dry-run) o remediación de imágenes duplicadas.
    """
    affected_posts = []
    for img_path, posts in duplicate_groups.items():
        affected_posts.extend(posts)

    total_affected = len(affected_posts)
    num_groups = len(duplicate_groups)

    print("==================================================")
    print(" 🔍 REPORTE DE IMÁGENES DUPLICADAS DE NOVUMWORLD")
    print("==================================================")
    print(f"📊 Grupos de imágenes duplicadas: {num_groups}")
    print(f"📄 Total de artículos afectados:   {total_affected}\n")

    if total_affected == 0:
        print("✅ ¡No se detectaron imágenes duplicadas en el blog!")
        return

    if dry_run:
        print("🔍 [MODO DRY-RUN] Mostrando artículos con imágenes duplicadas (Sin modificar disco):\n")
        for img_path, posts in duplicate_groups.items():
            print(f"🖼️  Imagen Duplicada: '{img_path}' ({len(posts)} artículos):")
            for p in posts:
                print(f"   - [{p['slug']}] {p['title']} ({p['filepath']})")
            print()
        print("💡 Para corregir automáticamente estas imágenes, ejecuta:")
        print("   python scripts/fix_duplicate_images.py")
        return

    print("🚀 Iniciando regeneración de imágenes únicas...\n")
    processed = 0
    still_placeholder = 0

    # Hashes de las plantillas por defecto para detectar placeholders enmascarados
    default_hashes = set()
    defaults_dir = os.path.join(BASE_DIR, "static", "images", "defaults")
    if os.path.isdir(defaults_dir):
        for f in os.listdir(defaults_dir):
            h = _hash_file(os.path.join(defaults_dir, f))
            if h:
                default_hashes.add(h)

    for p in affected_posts:
        processed += 1
        slug = p['slug']
        title = p['title']
        desc = p['desc']
        category = p['category']
        filepath = p['filepath']
        is_leaf_bundle = p['is_leaf_bundle']
        bundle_dir = p['bundle_dir']
        post = p['post_obj']

        # 3. Generar y guardar la imagen WebP optimizada
        img_ref, w, h = get_image(
            title=title,
            content=desc,
            slug=slug,
            category=category,
            bundle_dir=bundle_dir
        )

        # 4. Actualizar Frontmatter YAML del post
        post['image'] = img_ref
        post['featured_image'] = img_ref
        sync_featured_image_in_body(post, img_ref)

        # Aviso (no bloqueante): detectar si el resultado sigue siendo un placeholder
        new_file = _resolve_local_image(img_ref, bundle_dir)
        if 'default' in str(img_ref) or _hash_file(new_file) in default_hashes:
            still_placeholder += 1
            print(f"   ⚠️ '{slug}' sigue con placeholder (APIs de imagen no disponibles). "
                  f"Configura NVIDIA_API_KEY/TOGETHER_API_KEY/HUGGINGFACE_API_KEY y reejecuta.")

        try:
            with open(filepath, 'wb') as f:
                frontmatter.dump(post, f)
            print(f"[{processed}/{total_affected}] Actualizado: {slug} -> {img_ref}")
        except Exception as e:
            print(f"❌ Error guardando {filepath}: {e}")

    print(f"\n🏁 Remediación completada. {processed}/{total_affected} artículos actualizados con éxito.")
    if still_placeholder:
        print(f"⚠️ {still_placeholder} artículos quedaron con placeholder compartido (faltan claves de API de imagen).")


def main():
    parser = argparse.ArgumentParser(description="Detector y remediador de imágenes duplicadas.")
    parser.add_argument(
        "--content-dir",
        default="",
        help="Directorio de contenido a escanear (ej. content/posts o content/). Por defecto escanea content/posts si existe, o content/."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Reporta los duplicados sin modificar archivos en disco."
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=None,
        help="Filtra categorías a remediar (ej. --categories fitness crypto)."
    )
    args = parser.parse_args()

    categories = [c.lower() for c in args.categories] if args.categories else None

    target_dir = args.content_dir
    if not target_dir:
        candidate_posts = os.path.join("content", "posts")
        if os.path.exists(candidate_posts):
            target_dir = candidate_posts
        else:
            target_dir = "content"

    if not os.path.exists(target_dir):
        print(f"❌ El directorio '{target_dir}' no existe.")
        sys.exit(1)

    print(f"📂 Escaneando directorio: '{target_dir}'...")
    duplicate_groups, total_scanned = scan_for_duplicates(target_dir, categories=categories)
    print(f"🔎 Total artículos analizados: {total_scanned}")

    remediate_duplicate_images(duplicate_groups, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
