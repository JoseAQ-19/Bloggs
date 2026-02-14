
import os
import re

# Operation Rosetta: Final Bilingual Fix
# Scans English content for Spanish relics in Headers and Titles

CONTENT_DIR_EN = "/Users/manolo/Bloggs/content/en"

# A specific dictionary for known issues detected in the audit
# This is safer than blind automated translation
TRANSLATIONS = {
    # File: el-ano-en-que-la-realidad-virtual-derroto-al-mund.md
    "Año de Realidad Virtual: ¿Éxito Español o Espejismo Global?": "Year of Virtual Reality: Spanish Success or Global Mirage?",
    "Realidad Aumentada en España: Un Oasis en el Desierto Global": "Augmented Reality in Spain: An Oasis in the Global Desert",
    "Análisis Crítico: ¿Disparidad o Divergencia Temporal?": "Critical Analysis: Disparity or Temporal Divergence?",
    "¿Por qué España prospera mientras Meta tropieza?": "Why does Spain thrive while Meta stumbles?",
    "Agilidad y Adaptabilidad": "Agility and Adaptability",
    "Apoyo Gubernamental y Europeo": "Government and European Support",
    "El Veredicto: Un Futuro Divergente para la Realidad Extendida": "The Verdict: A Divergent Future for Extended Reality",

    # File: la-elites-digitales-amos-del-mundo-o-nuevos-parasi.md
    "La Élites Digitales: ¿Amos del Mundo o Nuevos Parásitos?": "Digital Elites: Masters of the World or New Parasites?", # Title
    "¿Élites Digitales: Arquitectos del Futuro o Nuevos Parásitos de la Sociedad?": "Digital Elites: Architects of the Future or New Parasites of Society?", # H2
    
    # File: demogracia-digital... (if any leftovers)
    "¿Democracia Digital? La Mayor Estafa del Siglo XXI": "Digital Democracy? The Biggest Scam of the 21st Century",

    # File: groenlandia...
    "Groenlandia: El Nuevo Jaque Mate Geopolítico que Hunde a Silicon Valley": "Greenland: The New Geopolitical Checkmate Sinking Silicon Valley",

    # File: tecnoutopia...
    "Tecnoutopía Fallida: El Sueño Digital Se Convierte en Pesadilla Neoliberal": "Failed Technoutopia: The Digital Dream Becomes a Neoliberal Nightmare",
    
    # File: donbe-estan-mis-coches-voladores...
    "¿Dónde Están Mis Coches Voladores? La Estafa Futurista": "Where Are My Flying Cars? The Futurist Scam",
    
    # File: el-futuro-es-ahora...
    "El Futuro es AHORA: Las 7 Tendencias que los Gobiernos Quieren Ocultar": "The Future is NOW: The 7 Trends Governments Want to Hide",
    
     # File: la-ia-te-miente...
    "La IA Te Miente: Por Qué la 'Personalidad' Artificial es una Trampa Psicológica": "AI Lies to You: Why Artificial 'Personality' Is a Psychological Trap",

    # File: la-ia-viene-a-quitarte...
    "La IA Viene a Quitarte el Almuerzo (Y No Se Disculpará)": "AI Is Coming for Your Lunch (And It Won't Apologize)",
    
}

def rosetta_fix(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    filename = os.path.basename(file_path)
    
    # 1. Frontmatter Title Fix
    # 2. Markdown Header Fix (lines starting with #)
    # 3. Bold text fix (lines starting with ** or containing **)
    
    # We will use simple string replacement for maximum safety on these specific strings
    for es_phrase, en_phrase in TRANSLATIONS.items():
        if es_phrase in content:
            # We only replace if it looks like a header, title, or bold text to avoid accidental body replacements
            # But specific phrases are long enough to be unique
            content = content.replace(es_phrase, en_phrase)
            print(f"[ROSETTA] Translated '{es_phrase}' -> '{en_phrase}' in {filename}")

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    print("Starting Operation Rosetta...")
    files_processed = 0
    files_changed = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR_EN):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                files_processed += 1
                if rosetta_fix(file_path):
                    files_changed += 1
    
    print(f"Operation Rosetta Complete. Scanned {files_processed} English files. Modified {files_changed} files.")

if __name__ == "__main__":
    main()
