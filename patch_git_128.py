import os
import glob
import re

workflow_dir = '.github/workflows'
files = glob.glob(os.path.join(workflow_dir, '*.yml'))

modified_files = []

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # Matches: git add content/es/youtube/ data/ static/images/ data/.*
    # Replaces with: git add content/es/youtube/ data/ static/images/ || true
    # This prevents exit code 128 from data/.* and also from non-existent folders
    
    content = re.sub(
        r'git add (content/[a-zA-Z0-9_/-]+) data/ static/images/ data/\.\*',
        r'git add \1 data/ static/images/ || true',
        content
    )
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files.append(os.path.basename(filepath))

print(f"Modificados {len(modified_files)} archivos parcheando Git exit code 128.")
