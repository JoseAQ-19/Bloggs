import glob
import re

fixed_count = 0
for filepath in glob.glob("content/**/*.md", recursive=True):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    modified = False
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if '<script type="application/ld+json">' in line and '</script>' not in line:
            # Check if line ends with JSON object
            line = line.rstrip() + "</script>"
            modified = True
            fixed_count += 1
        new_lines.append(line)

    if modified:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(new_lines) + "\n")
        print(f"Fixed: {filepath}")

print(f"Total fixed files: {fixed_count}")
