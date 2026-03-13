import os
import glob
import re

files = glob.glob('content/es/fitness/*.md')
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as h:
            content = h.read()
            m = re.search(r'title: (.*)\n', content)
            title = m.group(1).strip('"\'') if m else "NO TITLE"
            print(f"{os.path.basename(f)}: {title}")
    except:
        pass
