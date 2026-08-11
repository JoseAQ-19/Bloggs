#!/usr/bin/env python3
"""
scripts/fix_all_missing_and_default_images.py
----------------------------------------------
Remediador integral de imágenes predeterminadas y faltantes en NovumWorld.
Escanea todos los artículos en content/ (EN y ES), identifica cuáles están
usando imágenes 'defaults/' o cuyos archivos locales no existen en static/images/,
y genera una nueva imagen WebP única por artículo usando el motor NovumVisualEngine.
"""

import os
import sys
import frontmatter
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'core'))

from novum_visual import get_image, generate_unique_visual_prompt

def remediate_images(categories=None):
    content_dirs = [
        os.path.join(BASE_DIR, 'content/en'),
        os.path.join(BASE_DIR, 'content/es')
    ]

    total_scanned = 0
    fixed_count = 0
    failed_count = 0

    for cdir in content_dirs:
        if not os.path.exists(cdir):
            continue

        for root, _, files in os.walk(cdir):
            for filename in files:
                if not filename.endswith('.md') or filename in ('_index.md', 'about.md', 'contact.md', 'privacy.md', 'terms-of-service.md'):
                    continue

                fpath = os.path.join(root, filename)
                try:
                    post = frontmatter.load(fpath)
                except Exception as e:
                    print(f"Error loading {fpath}: {e}")
                    continue

                slug = post.get('slug') or filename.replace('.md', '')
                category = post.get('categories') or post.get('category') or 'ia'
                if isinstance(category, list) and len(category) > 0:
                    category = str(category[0])
                category = str(category).lower()

                # Infer category from path if needed
                parts = fpath.replace('\\', '/').split('/')
                if 'content' in parts:
                    idx = parts.index('content')
                    if len(parts) > idx + 2 and parts[idx + 1] in ('es', 'en'):
                        category = parts[idx + 2].lower()

                if categories and category not in categories:
                    continue

                total_scanned += 1
                img = post.get('featured_image') or post.get('image') or ''
                title = post.get('title') or slug.replace('-', ' ').title()

                # Check if current image is default or missing
                is_default = 'defaults' in str(img) or 'default-' in str(img) or not img
                image_exists = False
                if img and not is_default:
                    clean_img = str(img).lstrip('/')
                    local_path = os.path.join(BASE_DIR, 'static', clean_img)
                    image_exists = os.path.exists(local_path) or str(img).startswith('http')

                if is_default or not image_exists:
                    print(f"[{fixed_count + 1}] Fix required for '{slug}' (Cat: {category}, Current: '{img}')")

                    try:
                        # Generate high quality WebP image reference
                        result = get_image(
                            title=title,
                            content=post.content or '',
                            slug=slug,
                            category=category
                        )

                        img_ref = result[0] if isinstance(result, tuple) else result
                        if img_ref and 'default' not in str(img_ref):
                            post['featured_image'] = img_ref
                            post['image'] = img_ref

                            # Keep body image synchronized
                            content = post.content or ''
                            if '![' in content and '](' in content:
                                import re
                                content = re.sub(r'!\[[^\]]*\]\([^)]+\)', f'![{title}]({img_ref})', content, count=1)
                                post.content = content

                            frontmatter.dump(post, fpath)
                            fixed_count += 1
                            print(f"   -> Successfully updated: {img_ref}")
                        else:
                            # La generación falló (APIs no disponibles o rate limit).
                            # NUNCA copiar el default de categoría bajo el nombre del slug:
                            # eso creaba "imágenes únicas" con bytes idénticos (placeholders
                            # enmascarados). Se reporta como fallo y se deja el frontmatter intacto.
                            failed_count += 1
                            print(f"   -> SKIPPED (generation unavailable, placeholder not masked): {slug}")
                    except Exception as ex:
                        failed_count += 1
                        print(f"   -> Exception fixing {slug}: {ex}")

    print(f"\n==========================================")
    print(f"Remediation Complete! Scanned: {total_scanned}, Fixed: {fixed_count}, Failed: {failed_count}")
    print(f"==========================================")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--categories', nargs='+', help='Categorías a filtrar (ej. fitness crypto)')
    args = parser.parse_args()
    
    cats = [c.lower() for c in args.categories] if args.categories else None
    remediate_images(categories=cats)
