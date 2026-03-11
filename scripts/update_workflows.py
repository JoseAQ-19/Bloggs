import glob
import os

workflows = glob.glob('.github/workflows/*.yml')
updated = 0
for wf in workflows:
    with open(wf, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'GROQ_API_KEY:' in content and 'NVIDIA_API_KEY:' not in content:
        # Avoid issues with variables
        target = 'GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}'
        replacement = 'GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}\n          NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}'
        content = content.replace(target, replacement)
        with open(wf, 'w', encoding='utf-8') as f:
            f.write(content)
        updated += 1
print(f'Updated {updated} workflows with NVIDIA_API_KEY')
