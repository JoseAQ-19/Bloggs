import os
for root, dirs, files in os.walk('content'):
    for file in files:
        if file.endswith('.md'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and not content[-1] in '.!?\"\'':
                        # Check if last line is a reference link or thematic break or author tag
                        lines = content.splitlines()
                        if not lines: continue
                        last_line = lines[-1]
                        if not last_line.endswith('---') and not last_line.endswith(')') and not last_line.endswith('**'):
                             print(f'[ERR] {path}')
            except Exception:
                pass
