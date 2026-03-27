import glob
import re
import os

print('Iniciando upgrade a GITHUB_TOKEN y Permisos en 32 Workflows...')
workflows = glob.glob('.github/workflows/*.yml')
count = 0

for wf in workflows:
    with open(wf, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add id-token: write to permissions if not exists
    if 'id-token: write' not in content:
        content = re.sub(r'(permissions:\s*\n\s+contents:\s*write)', r'\1\n  id-token: write', content)

    # 2. Swap the manual secrets for GITHUB_TOKEN
    content = re.sub(r'(\n\s*)MODELS_TOKEN_CEU:.*', '', content)
    content = re.sub(r'(\n\s*)TOKEN_MODELS:.*', '', content)

    # Insert GITHUB_TOKEN immediately after GEMINI_API_KEY if not already there
    if 'GITHUB_TOKEN:' not in content:
        content = re.sub(r'(GEMINI_API_KEY:\s*\$\{\{\s*secrets\.GEMINI_API_KEY\s*\}\})', r'\1\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}', content)

    with open(wf, 'w', encoding='utf-8') as f:
        f.write(content)
    
    count += 1
    print(f'Migrated: {os.path.basename(wf)}')

print(f'{count} workflows actualizados correctamente.')
