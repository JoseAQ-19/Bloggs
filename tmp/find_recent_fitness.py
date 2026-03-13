import os
import glob

files = glob.glob('content/**/fitness/*.md', recursive=True)
files_with_time = []
for f in files:
    if os.path.basename(f) == '_index.md':
        continue
    files_with_time.append((f, os.path.getmtime(f)))

files_with_time.sort(key=lambda x: x[1], reverse=True)

for f, t in files_with_time[:2]:
    print(f)
