import os
import re

def purge_meta_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter from body
    # Standard Hugo frontmatter is between --- and ---
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    
    if len(parts) < 3:
        # Not a standard Hugo file with frontmatter, skip or process as whole?
        # Safe to process as whole body.
        body = content
        header = ""
    else:
        header = f"---\n{parts[1]}---\n"
        body = parts[2]

    # Regex for JSON-LD script tags
    script_pattern = r'<script type="application/ld\+json">[\s\S]*?<\/script>'
    
    # Regex for json code blocks that might contain schema
    # (Checking for 'headline' or '@context' inside to be sure it's schema)
    json_block_pattern = r'```json[\s\S]*?headline[\s\S]*?```|```json[\s\S]*?@context[\s\S]*?```'

    cleaned_body = re.sub(script_pattern, '', body)
    cleaned_body = re.sub(json_block_pattern, '', cleaned_body)

    # Remove trailing/leading newlines to clean up
    cleaned_body = cleaned_body.strip()

    if cleaned_body != body.strip():
        new_content = header + cleaned_body + "\n"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    root_dir = 'content'
    count = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                if purge_meta_from_file(path):
                    count += 1
                    print(f"Purged: {path}")
    
    print(f"\nTotal files cleaned: {count}")

if __name__ == "__main__":
    main()
