import os
import re
import shutil
from pathlib import Path

def ruthless_clean():
    base_dir = Path("content")
    print(f"🚀 Iniciando Ruthless Clean en {base_dir.absolute()}...")

    stats = {"cleaned": 0, "moved": 0, "errors": 0}

    # Patterns
    # 1. H1 in body (usually start of content after frontmatter)
    re_h1 = re.compile(r"^#\s+.*$", re.MULTILINE)
    
    # 2. Metadata leaks (title:, slug:, etc.)
    re_leaks = re.compile(r"^(title|slug|description|date|categories|tags|featured_image|language|quality_tier|translationKey):\s+.*$", re.MULTILINE | re.IGNORECASE)

    # 3. Double Methodology/Insights
    re_method_bug = re.compile(r"##\s+Methodology and Sources and Sources", re.IGNORECASE)
    re_insights_dup = re.compile(r"(##\s+Key Insights\n+){2,}", re.IGNORECASE)

    # 4. Double Disclaimers (Editorial Disclosure / Aviso Editorial)
    re_disclaimer = re.compile(r"\*(?:Editorial Disclosure|Aviso Editorial):.*?\*", re.IGNORECASE | re.DOTALL)

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".md") or file == "_index.md":
                continue

            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    v_content = f.read()

                # Split Frontmatter
                parts = v_content.split("---", 2)
                if len(parts) < 3:
                    continue

                frontmatter = parts[1]
                body = parts[2]
                modified = False

                # --- CLEAN BODY ---
                
                # Remove H1
                if re_h1.search(body):
                    body = re_h1.sub("", body)
                    modified = True

                # Remove leaks
                if re_leaks.search(body):
                    body = re_leaks.sub("", body)
                    modified = True

                # Fix methodology bug
                lang_match = re.search(r"language:\s*(en|es)", frontmatter)
                lang = lang_match.group(1) if lang_match else "en"
                
                if re_method_bug.search(body):
                    replacement = "## Methodology and Sources" if lang == "en" else "## Metodología y Fuentes"
                    body = re_method_bug.sub(replacement, body)
                    modified = True

                # Deduplicate Key Insights & Normalize to TL;DR
                tldr_header = "## Resumen Ejecutivo" if lang == "es" else "## Executive Summary"
                # Replace Key Insights, Principales Claves, or redundant TL;DR variations
                re_tldr_variants = re.compile(r"##\s*(?:Key Insights|Principales Claves|Executive Summary)\s*\n", re.IGNORECASE)
                if re_tldr_variants.search(body):
                    body = re_tldr_variants.sub(tldr_header + "\n", body)
                    modified = True

                # Deduplicate Disclaimers
                all_disclaimers = re_disclaimer.findall(body)
                if len(all_disclaimers) > 1:
                    # Keep only the last one (closest to the end)
                    body = re_disclaimer.sub("", body).strip()
                    body = body + "\n\n" + all_disclaimers[-1]
                    modified = True

                # --- MOVE ZOMBIES ---
                # Check path consistency
                current_folder = file_path.parent.name # e.g. 'crypto', 'ia'
                # Check if it's in an 'en' or 'es' root
                is_en = "/en/" in str(file_path.as_posix())
                is_es = "/es/" in str(file_path.as_posix())

                target_lang = lang # from frontmatter
                
                # If frontmatter says 'en' but it's in '/es/' path, or vice versa
                mismatch = (target_lang == "en" and is_es) or (target_lang == "es" and is_en)
                
                if mismatch:
                    # Move logic
                    new_root = str(file_path.as_posix()).replace(f"/{'es' if is_es else 'en'}/", f"/{target_lang}/")
                    new_path = Path(new_root)
                    os.makedirs(new_path.parent, exist_ok=True)
                    
                    # Save cleaned content to NEW path
                    with open(new_path, "w", encoding="utf-8") as f:
                        f.write(f"---{frontmatter}---{body}")
                    
                    # Remove OLD file
                    os.remove(file_path)
                    print(f"📦 Movido: {file} -> {target_lang}")
                    stats["moved"] += 1
                    continue # Skip normal save

                if modified:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"---{frontmatter}---{body}")
                    stats["cleaned"] += 1

            except Exception as e:
                print(f"❌ Error en {file}: {e}")
                stats["errors"] += 1

    print("\n✅ LIMPIEZA COMPLETADA")
    print(f"✨ Limpiados: {stats['cleaned']}")
    print(f"📦 Movidos: {stats['moved']}")
    print(f"⚠️ Errores: {stats['errors']}")

if __name__ == "__main__":
    ruthless_clean()
