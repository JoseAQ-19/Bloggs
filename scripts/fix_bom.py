import glob
for f in glob.glob('.github/workflows/*.yml'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("node-version: '20'", "node-version: '22'")
    if content.startswith('\ufeff'):
        content = content[1:]
    with open(f, 'w', encoding='utf-8', newline='') as file:
        file.write(content)
