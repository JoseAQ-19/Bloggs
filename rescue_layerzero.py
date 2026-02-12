import os
import frontmatter
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

TARGET_FILE = "content/crypto/why-is-layerzero-trending-today-in-crypto.md"

def rescue_layerzero():
    print("🚑 RESCATANDO LAYERZERO (Muro de Texto)...")
    if not os.path.exists(TARGET_FILE):
        print("   ⚠️ Archivo no encontrado.")
        return
        
    try:
        post = frontmatter.load(TARGET_FILE)
        
        prompt = f"""
        ACT AS: Crypto Technical Analyst.
        TASK: Rewrite this article completely. It has no structure.
        TITLE: "{post.get('title')}"
        ORIGINAL CONTENT (Use as source):
        {post.content[:4000]}
        
        RULES:
        1. Use H2 (##) for main sections.
        2. Use H3 (###) for subsections.
        3. Use Bullet Points.
        4. Length: 1000 words.
        5. Tone: Analytical, serious.
        """
        
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        post.content = resp.text.strip()
        
        with open(TARGET_FILE, 'wb') as f:
            frontmatter.dump(post, f)
            
        print("   ✅ LayerZero Reestructurado.")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    rescue_layerzero()
