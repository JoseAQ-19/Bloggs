import os
import re
import glob

def check_links():
    content_dir = "content"
    md_files = glob.glob(os.path.join(content_dir, "**", "*.md"), recursive=True)
    print(f"Total MD files found: {len(md_files)}")
    
    # Sort by modification time
    md_files.sort(key=os.path.getmtime, reverse=True)
    
    missing_links = []
    for fpath in md_files:
        if os.path.basename(fpath).startswith("_index"): continue
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            # print(f"Error reading {fpath}: {e}")
            continue
            
        links = re.findall(r'(?<!\!)\[[^\]]+\]\((https?://[^\)]+)\)', content)
        
        if len(links) < 3:
            missing_links.append((fpath, len(links)))
            if len(missing_links) >= 100: break
            
    print(f"Count of files with < 3 links: {len(missing_links)}")
    for path, count in missing_links[:30]:
        print(f"[{count}] {path}")

if __name__ == "__main__":
    check_links()
