import os
import subprocess
import sys

def run_manual_generation(section, lang):
    print(f"🚀 [CLI] GENERANDO CONTENIDO MANUAL: {section.upper()} ({lang})")
    
    # Llamamos a main.py con argumentos
    # Como main.py está en root, usamos subprocess
    cmd = [sys.executable, "main.py", "--category", section]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Generación completada.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar main.py: {e}")
