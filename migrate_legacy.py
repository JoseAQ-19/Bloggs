import os
import shutil
import re
import frontmatter

SOURCE_DIR = 'content/posts'
TARGET_BASE = 'content'

# Reglas de Clasificación (Keyword -> Carpeta)
RULES = {
    'crypto': ['bitcoin', 'crypto', 'ethereum', 'solana', 'blockchain', 'nft', 'defi', 'wallet', 'token', 'coin'],
    'fitness': ['gym', 'rutina', 'dieta', 'salud', 'fitness', 'entrenamiento', 'musculo', 'perder peso', 'health'],
    'youtube': ['youtube', 'twitch', 'streamer', 'mrbeast', 'rubius', 'ibai', 'views', 'monetizacion', 'creator'],
    'viral': ['viral', 'polemica', 'twitter', 'reddit', 'tiktok', 'trend', 'salseo', 'drama', 'meme'],
    'ia': [] # Default
}

def classify_post(post_obj):
    """Devuelve la categoría basada en título/tags."""
    text_to_scan = (post_obj.get('title', '') + " " + " ".join(post_obj.get('tags', []))).lower()
    
    for category, keywords in RULES.items():
        if category == 'ia': continue
        for kw in keywords:
            if kw in text_to_scan:
                return category
    
    return 'ia' # Default fallback

def migrate_legacy():
    print("🧹 Iniciando Migración de Legado...")
    
    if not os.path.exists(SOURCE_DIR):
        print("✅ No hay carpeta legacy (content/posts). Migración ya realizada.")
        return

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.md')]
    
    if not files:
        print("✅ Carpeta content/posts vacía.")
        return

    count = 0
    for filename in files:
        src_path = os.path.join(SOURCE_DIR, filename)
        
        try:
            post = frontmatter.load(src_path)
            category = classify_post(post)
            
            # Definir destino
            dest_dir = os.path.join(TARGET_BASE, category)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            
            # Actualizar Frontmatter
            post['type'] = category
            post['categories'] = [category]
            # Asegurar campo language (asumimos 'es' si no existe para legacy)
            if 'language' not in post:
                post['language'] = 'es'
                
            # Guardar en nuevo destino
            with open(dest_path, 'wb') as f:
                frontmatter.dump(post, f)
            
            # Borrar original
            os.remove(src_path)
            
            print(f"📦 Movido: {filename} -> {category}/")
            count += 1
            
        except Exception as e:
            print(f"❌ Error migrando {filename}: {e}")

    print(f"✨ Migración completada. {count} archivos procesados.")
    
    # Intentar borrar carpeta vacía
    try:
        os.rmdir(SOURCE_DIR)
        print("🗑️ Carpeta content/posts eliminada.")
    except:
        pass

if __name__ == "__main__":
    migrate_legacy()
