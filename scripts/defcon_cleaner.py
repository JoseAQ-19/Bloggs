import os
import re

# Defcon Cleaner Script
# Purpose: Purge AI meta-comments and fix bilingual title mismatches

CONTENT_DIR = "/Users/manolo/Bloggs/content"
PURGE_PATTERNS = [
    r"## Verdict.*",
    r"## Veredicto.*",
    r"## The Verdict.*",
    r"## El Veredicto.*",
    r"The original article, while insightful.*",
    r"El artículo original, aunque perspicaz.*",
    r"Here's a rewritten article.*",
    r"Aquí hay un artículo reescrito.*",
    r"Google HCU compliance.*",
    r"Cumplimiento de Google HCU.*",
    r"This rewritten version.*",
    r"Esta versión reescrita.*",
    r"Nota de la IA.*",
    r"AI Note.*"
]

# Known translations to apply immediately (simulating LLM)
TRANSLATIONS = {
    # ES to EN (for files in content/en/)
    "¿Democracia Digital? La Mayor Estafa del Siglo XXI": "Digital Democracy? The Biggest Scam of the 21st Century",
    "Geopolítica 2026: El Año en que Dejamos de Fingir": "Geopolitics 2026: The Year We Stopped Pretending",
    "Groenlandia: El Nuevo Jaque Mate Geopolítico que Hunde a Silicon Valley": "Greenland: The New Geopolitical Checkmate Sinking Silicon Valley",
    "Tecnoutopía Fallida: El Sueño Digital Se Convierte en Pesadilla Neoliberal": "Failed Technoutopia: The Digital Dream Becomes a Neoliberal Nightmare",
    "El Futuro es Distópico y Ya Está Aquí": "The Future Is Dystopian And It Is Already Here",
    "El Año en que la Realidad Virtual Derrotó al Mundo Real": "The Year Virtual Reality Defeated the Real World",
    
    # EN to ES (for files in content/es/)
    "Why is Venice Token trending today in crypto? Analysis": "¿Por qué el Token Venice es tendencia hoy en cripto? Análisis",
}

def clean_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    filename = os.path.basename(file_path)
    
    # 1. Purge AI Meta-comments
    # We look for the patterns. If found, we truncate everything from that point on.
    # We will use the earliest match to be safe.
    earliest_bloat_index = len(content)
    bloat_found = False
    
    for pattern in PURGE_PATTERNS:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            if match.start() < earliest_bloat_index:
                earliest_bloat_index = match.start()
                bloat_found = True
    
    if bloat_found:
        # Check if we are cutting off too much (sanity check), e.g. if it's at the very beginning
        if earliest_bloat_index > 100: 
            content = content[:earliest_bloat_index].strip()
            # Ensure it ends with a newline
            content += "\n"
            print(f"[PURGED] Removed AI footer in {filename}")
    
    # 2. Fix Bilingual Titles
    # Extract Frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        title_match = re.search(r"title: (.*)", frontmatter)
        
        if title_match:
            current_title_raw = title_match.group(1)
            # Handle quotes in title
            current_title = current_title_raw.strip('"\'')
            
            new_title = None
            
            # Check context
            is_en_dir = "/content/en/" in file_path
            is_es_dir = "/content/es/" in file_path
            
            # Apply known translations
            if current_title in TRANSLATIONS:
                target_trans = TRANSLATIONS[current_title]
                # Verify direction
                if is_en_dir and target_trans not in TRANSLATIONS: # Assuming English titles are not keys in our specific dict for ES->EN map? 
                    # Actually, just check if the known translation fits the folder language
                    # Simple heuristic: EN titles usually don't have '¿'
                    if is_en_dir and "¿" in current_title:
                         new_title = target_trans
                    elif is_en_dir and any(x in current_title for x in ["El ", "La ", "Los ", "Las ", " en ", " y "]):
                         new_title = target_trans
                    elif is_es_dir and "Why " in current_title:
                         new_title = target_trans
                    
                    # Force apply if it's in the map and clearly wrong
                    if is_en_dir and current_title == "Geopolítica 2026: El Año en que Dejamos de Fingir": new_title = target_trans
                    if is_en_dir and current_title == "Groenlandia: El Nuevo Jaque Mate Geopolítico que Hunde a Silicon Valley": new_title = target_trans
                    if is_en_dir and current_title == "Tecnoutopía Fallida: El Sueño Digital Se Convierte en Pesadilla Neoliberal": new_title = target_trans
                    if is_en_dir and current_title == "El Futuro es Distópico y Ya Está Aquí": new_title = target_trans
                    if is_en_dir and current_title == "¿Democracia Digital? La Mayor Estafa del Siglo XXI": new_title = target_trans
                    if is_es_dir and current_title == "Why is Venice Token trending today in crypto? Analysis": new_title = target_trans

            if new_title:
                # Replace title in content
                # We need to be careful to replace only the title line in frontmatter
                # Escape special chars for regex replacement if needed
                safe_current_title = re.escape(current_title_raw)
                # content = re.sub(f"title: {safe_current_title}", f"title: '{new_title}'", content, count=1)
                # safer replacement logic:
                pattern_title = r"(title:\s*)(.*)"
                def replace_title(match):
                    if match.group(2).strip('"\'') == current_title:
                        return f"title: '{new_title}'"
                    return match.group(0)
                
                content = re.sub(pattern_title, replace_title, content, count=1)
                print(f"[TITLE FIXED] '{current_title}' -> '{new_title}' in {filename}")

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    print("Starting DEFCON 1 Cleanup...")
    files_processed = 0
    files_changed = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                files_processed += 1
                if clean_file(file_path):
                    files_changed += 1
    
    print(f"DEFCON 1 Complete. Processed {files_processed} files. Modified {files_changed} files.")

if __name__ == "__main__":
    main()
