import os
import glob
from content_engine_pro import main_upgrade_engine

def full_repository_sanitization():
    print("🚀 INICIANDO SANEAMIENTO AGRESIVO 2.0 (MODO DEMOLEDOR)...")
    content_root = "c:/Users/usuario/Bloggs/content"
    
    # 1. Obtener todos los archivos markdown en content/es/ y content/en/
    all_files = glob.glob(os.path.join(content_root, "es", "**", "*.md"), recursive=True)
    all_files += glob.glob(os.path.join(content_root, "en", "**", "*.md"), recursive=True)
    
    # Excluir _index.md
    target_files = [f for f in all_files if not f.endswith("_index.md")]
    
    print(f"📦 Total de archivos a procesar: {len(target_files)}")
    
    for i, file_path in enumerate(target_files):
        print(f"[{i+1}/{len(target_files)}] Reparando: {file_path}")
        try:
            # Reusamos la función del motor pero forzando la parte de footer/cleanup 
            # (main_upgrade_engine hace todo: genera con IA + inyecta footer)
            # Para mayor precisión en esta fase decorativa, solo vamos a arreglar el footer sin regenerar el cuerpo si es v3 pro.
            # O mejor, ejecutamos el motor completo para asegurar calidad Pro en todo.
            main_upgrade_engine(file_path)
        except Exception as e:
            print(f"   ❌ Error procesando {file_path}: {e}")

if __name__ == "__main__":
    full_repository_sanitization()
