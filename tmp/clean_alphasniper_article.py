import os

path = 'content/es/viral/alphasniper-plex-jarama-lamborghini-porsche.md'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ensure we are working with the truncated version or the full one
# If we have <script tags, remove them.
# The user wants "Artículos Relacionados" at the end.

clean_lines = []
for line in lines:
    if '<script' in line or '</script>' in line or '"@context"' in line:
        continue
    # Simple check to skip the rest of JSON if it's already started
    if '@type' in line or '"headline"' in line:
        continue
    clean_lines.append(line)

# Trim trailing whitespace/newlines
while clean_lines and not clean_lines[-1].strip():
    clean_lines.pop()

# Add Related Articles if missing
related_header = "### Artículos Relacionados\n"
if related_header not in clean_lines:
    clean_lines.append("\n" + related_header)
    clean_lines.append("- [YouTube: El Imperio Prohibido Donde el 64% de Tus Hijos Ya Están Cautivos](/es/youtube/youtube-destrona-disney-rey-medios-digital/)\n")
    clean_lines.append("- [¿Comida Rápida? La Crítica DEVASTADORA Al Estilo MrBeast Que Sacude YouTube.](/es/youtube/mrbeast-formula-viral-youtube/)\n")

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
