import os
import frontmatter
import yaml

CONTENT_DIR = "content"

def validate_yaml():
    print("🔍 VALIDANDO SINTAXIS YAML...")
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md"): continue
            
            filepath = os.path.join(root, filename)
            
            try:
                # Intento de carga estricta
                post = frontmatter.load(filepath)
                
                # Validar campos críticos
                if not post.get('title'):
                    print(f"❌ {filename}: Falta título")
                
            except Exception as e:
                print(f"🚨 ERROR CRÍTICO YAML en: {filename}")
                print(f"   Razón: {e}")
                
                # Intentar leer el archivo crudo para ver el error
                with open(filepath, 'r') as f:
                    print("   --- CONTENIDO ---")
                    print(f.read()[:300])
                    print("   -----------------")

    print("✅ Validación finalizada.")

if __name__ == "__main__":
    validate_yaml()
