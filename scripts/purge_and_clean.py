import os
import glob
import re
import audit_v2

def run_purge_and_clean():
    content_path = os.path.join(os.getcwd(), 'content', '**', '*.md')
    files = glob.glob(content_path, recursive=True)

    script_pattern = re.compile(r'<script\s+type="application/ld\+json">.*?</script>', re.DOTALL | re.IGNORECASE)

    purged = 0
    survived = 0
    scripts_removed = 0

    import shutil
    draft_dir = os.path.join(os.getcwd(), 'content', 'drafts_to_fix')
    os.makedirs(draft_dir, exist_ok=True)

    for filepath in files:
        if any(x in filepath for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md']): 
            survived += 1
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            new_content, count = script_pattern.subn('', content)
            if count > 0:
                scripts_removed += 1
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        except Exception as e:
            print(f"Error procesando {filepath}: {e}")
            continue

        res = audit_v2.analyze_file(filepath)
        if res:
            try:
                dest_path = os.path.join(draft_dir, os.path.basename(filepath))
                shutil.move(filepath, dest_path)
                purged += 1
                print(f"Movido a drafts: {filepath}")
                print(f"   Motivos: {res.get('issues', [])}")
            except Exception as e:
                print(f"Error moviendo {filepath}: {e}")
        else:
            survived += 1

    with open('purge_results.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 40 + "\n")
        f.write(f"RESULTADOS DE LA PURGA DE ADSENSE\n")
        f.write(f"Archivos limpiados (Scripts LD+JSON removidos): {scripts_removed}\n")
        f.write(f"Artículos Purgados (Baja calidad/Flags): {purged}\n")
        f.write(f"Artículos Sobrevivientes (Aprobados): {survived}\n")
        f.write("=" * 40 + "\n")


if __name__ == "__main__":
    run_purge_and_clean()
