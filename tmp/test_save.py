import sys
import os
import json
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

import main
from utils import LinkManager

def test_save():
    meta = {
        "titulo": "Test Articulo Ralph v3.5",
        "slug": "test-articulo-ralph-v3-5"
    }
    contenido = "## Introduccion\nEste es un articulo de prueba para verificar el motor de Ralph.\n\n## Desarrollo\nAqui va el contenido principal sin paja introductoria."
    lang = "es"
    category = "youtube"
    
    # Mock NICHES if needed, but it should be available in main
    if 'youtube' not in main.NICHES:
        main.NICHES['youtube'] = {"name": "YouTube Creator"}

    print("--- Testing guardar_post ---")
    main.guardar_post(meta, contenido, lang, category, translation_key="test-key-123")
    
    filepath = f"content/{lang}/{category}/{meta['slug']}.md"
    if os.path.exists(filepath):
        print(f"✅ File created: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = "".join(lines)
            
            # Check for JSON-LD
            if '<script type="application/ld+json">' in content:
                print("✅ JSON-LD found")
            else:
                print("❌ JSON-LD NOT found")
                
            # Check for Internal Links
            if "### Artículos Relacionados" in content:
                print("✅ Related Articles section found")
            else:
                print("❌ Related Articles section NOT found")
                
            # Check for NewsArticle type
            if '"@type": "NewsArticle"' in content:
                print("✅ Schema @type: NewsArticle found")
            else:
                print("❌ Schema @type: NewsArticle NOT found")
                
            # print(content[-500:]) # Show the end of the file
    else:
        print(f"❌ File NOT created: {filepath}")

if __name__ == "__main__":
    test_save()
