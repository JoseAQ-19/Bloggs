import os
import shutil
import frontmatter
from dotenv import load_dotenv
from together import Together

load_dotenv()
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_KEY:
    print("❌ ERROR: Falta TOGETHER_API_KEY")
    exit(1)

client = Together(api_key=TOGETHER_KEY)

CONTENT_ROOT = "content"
VALID_CATEGORIES = ["ia", "fitness", "crypto", "youtube", "viral", "tools"]
# Nota: Usamos 'ia' en lugar de 'tech' según la estructura actual de carpetas

def classify_article(title, summary):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[
                {"role": "system", "content": f"You are a Content Classifier. Categories: {', '.join(VALID_CATEGORIES)}. Output ONLY the category name."},
                {"role": "user", "content": f"Classify this article. Title: '{title}'. Text: '{summary[:300]}'. Category:"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        cat = response.choices[0].message.content.strip().lower()
        # Limpieza básica por si el modelo habla de más
        for v in VALID_CATEGORIES:
            if v in cat: return v
        return "ia" # Default fallback
    except Exception as e:
        print(f"   ⚠️ Error clasificando: {e}")
        return None

def organize_content():
    print("🧹 INICIANDO ORGANIZACIÓN INTELIGENTE...")
    moves = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            current_folder = os.path.basename(root)
            
            # Ignorar páginas estáticas en raíz
            if current_folder == "content": continue

            try:
                post = frontmatter.load(filepath)
                title = post.get('title', '')
                summary = post.get('description', '') or post.content[:200]
                
                # Clasificar
                new_category = classify_article(title, summary)
                
                if new_category and new_category != current_folder:
                    # Preparar movimiento
                    dest_dir = os.path.join(CONTENT_ROOT, new_category)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, filename)
                    
                    # Actualizar frontmatter
                    post['categories'] = [new_category]
                    post['type'] = new_category
                    
                    # Mover y guardar
                    with open(dest_path, 'wb') as f:
                        frontmatter.dump(post, f)
                    
                    os.remove(filepath)
                    print(f"📦 [MOVIDO] {title[:30]}... | {current_folder} -> {new_category}")
                    moves += 1
                else:
                    # print(f"✅ Correcto: {filename} en {current_folder}")
                    pass
                    
            except Exception as e:
                print(f"❌ Error en {filename}: {e}")

    print(f"\n✨ ORGANIZACIÓN FINALIZADA. {moves} artículos movidos.")

if __name__ == "__main__":
    organize_content()
