import os
import glob
from datetime import datetime

files = glob.glob('content/**/viral/*.md', recursive=True)
files_with_time = [(f, os.path.getmtime(f)) for f in files]
files_with_time.sort(key=lambda x: x[1], reverse=True)

for f, t in files_with_time[:5]:
    dt = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{f} [{dt}]")
