import os
import re
import glob

def check_links():
    content_dir = "content"
    md_files = glob.glob(os.path.join(content_dir, "**", "*.md"), recursive=True)
    
    missing_links = []
    for fpath in md_files:
        if os.path.basename(fpath).startswith("_index"): continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Contar links markdown [text](url)
        # Pero excluir imagenes ![]() y links internos que empiezan con /es/ o /en/
        links = re.findall(r'(?<!\!)\[[^\]]+\]\((https?://[^\)]+)\)', content)
        
        if len(links) < 3:
            missing_links.append((fpath, len(links)))
            
    print(f"Total files checked: {len(md_files)}")
    print(f"Files with less than 3 external links: {len(missing_links)}")
    for path, count in missing_links[:10]:
        print(f" - {path} ({count} links)")
    if len(missing_links) > 10:
        print(f" ... and {len(missing_links) - 10} more.")

if __name__ == "__main__":
    check_links()
