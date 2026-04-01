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
    
    # Revert checkout from v5 to v4
    content = re.sub(r'uses:\s*actions/checkout@v5', r'uses: actions/checkout@v4', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files.append(os.path.basename(filepath))

print(f"Modificados {len(modified_files)} archivos reversando checkout a v4.")
