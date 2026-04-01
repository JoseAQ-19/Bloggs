import os
import glob
import re

def audit_truncation():
    content_dir = "content"
    truncated_files = []
    
    # Path to search for markdown files
    md_files = glob.glob(os.path.join(content_dir, "**", "*.md"), recursive=True)
    
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Case 1: Body ends abruptly
                # Extract body (stuff after frontmatter)
                parts = content.split('---')
                if len(parts) >= 3:
                    body = parts[2].strip()
                    if not body:
                        continue
                    
                    # Typical AI truncation: ends with "..."
                    if body.endswith("...") or body.endswith("…"):
                         truncated_files.append((file_path, "Ends with ellipsis"))
                         continue
                         
                    # Check for incomplete sentences (ends with a punctuation mark)
                    # We look at the last 10 characters
                    last_chars = body[-10:].strip()
                    if not re.search(r'[.!?»"”\)]$', last_chars):
                        truncated_files.append((file_path, f"Incomplete ending: '...{last_chars}'"))
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    print("\n--- REPORT: TRUNCATED ARTICLES ---")
    if not truncated_files:
        print("[OK] No articles with evident truncation detected.")
    else:
        for f, reason in truncated_files:
            print(f"[ERR] {f} -> {reason}")
    print("----------------------------------\n")

if __name__ == "__main__":
    audit_truncation()
