import os
import sys
sys.path.append('scripts')
from orchestrator import guardar_post

# Mock data
meta = {
    "titulo": "Prueba de Inyección Determinista",
    "slug": "prueba-inyeccion-vault"
}
contenido = "Este es un body de prueba que termina aquí con un punto y final."
lang = "es"
category = "crypto"

# Seed data/scout_vault.json
import json
os.makedirs("data", exist_ok=True)
with open("data/scout_vault.json", "w", encoding="utf-8") as f:
    json.dump({"prueba-inyeccion-vault": ["https://www.reuters.com/article1", "https://news.ycombinator.com/item?id=123"]}, f)

guardar_post(meta, contenido, lang, category)

filepath = f"content/es/crypto/{meta['slug']}.md"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        final_text = f.read()
    
    with open("test_result.txt", "w", encoding="utf-8") as f:
        if "## Metodología y fuentes" in final_text and "## Artículos relacionados" in final_text:
            f.write("SUCCESS: Bloques encontrados correctamente.")
        else:
            f.write(f"FAILURE: Bloques no encontrados. Contenido final: {final_text[-1000:]}")
else:
    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write("FAILURE: Archivo no creado.")

