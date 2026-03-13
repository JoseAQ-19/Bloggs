import os
import glob

files = glob.glob('content/**/viral/*.md', recursive=True)
files_with_time = [(f, os.path.getmtime(f)) for f in files]
files_with_time.sort(key=lambda x: x[1], reverse=True)

for f, t in files_with_time[:5]:
    print(f"{f} | {t}")
