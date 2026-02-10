import os
import re
import frontmatter
from dotenv import load_dotenv
from google import genai
from google.genai import types
import researcher # NUEVO: Inyección de realidad

# Configuración
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except:
    print("❌ Error: No API Key found.")
    exit(1)

CONTENT_DIRS = [
    'content/crypto', 'content/fitness', 'content/ia', 'content/youtube', 'content/viral'
]

PERSONAS = {
    'crypto': "Inversor de Wall Street experto en Blockchain",
    'fitness': "Entrenador basado en evidencia y científico del deporte",
    'ia': "Analista Senior de Tecnología y SaaS",
    'youtube': "Estratega de Negocios Digitales",
    'viral': "Editor Jefe de Cultura Pop y Tendencias"
}

def needs_remaster(post, content_body):
    if len(content_body) < 3000: return True, "Short Content"
    title = post.get('title', '').lower()
    suspicious = ['test', 'prueba', 'hola', 'draft', 'borrador']
    if title in suspicious: return True, "Bad Title"
    if '##' not in content_body: return True, "No Structure"
    return False, "OK"

def remaster_article(filepath, category):
    try:
        post = frontmatter.load(filepath)
        content_body = post.content
        flag, reason = needs_remaster(post, content_body)
        
        if not flag:
            print(f"✅ OK: {filepath}")
            return

        print(f"🚩 REMASTERIZANDO ({reason}): {filepath}")
        
        # --- INVESTIGACIÓN DE REALIDAD (NUEVO) ---
        topic = post.get('title', 'Tema desconocido')
        print(f"   🔍 Investigando realidad sobre: {topic}")
        res = researcher.Researcher()
        real_context = res.research_topic(topic)
        # -----------------------------------------
        
        persona = PERSONAS.get(category, "Editor Senior")
        prompt = f"""
        ACT AS: {persona}.
        TASK: Rewrite and upgrade this legacy article using REAL DATA.
        
        ORIGINAL TITLE: "{topic}"
        REAL CONTEXT (USE THIS):
        {real_context[:3000]}
        
        INSTRUCTIONS:
        1. Rewrite from scratch. 1000+ words.
        2. Use the REAL CONTEXT to provide actual facts, dates, and numbers.
        3. Tone: Ultra-professional.
        4. Structure: Hook -> H2 -> H2 -> Conclusion.
        
        OUTPUT: Markdown body only.
        """
        
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        new_body = resp.text.strip()
        
        if len(new_body) < 500: return

        post.content = new_body
        post['type'] = category
        post['categories'] = [category]
        
        with open(filepath, 'wb') as f:
            frontmatter.dump(post, f)
            
        print(f"✨ GLOW UP EXITOSO: {filepath} ({len(new_body)} chars)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🕵️‍♂️ INICIANDO REMASTERIZACIÓN CON DATOS REALES...")
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        files = [f for f in os.listdir(folder) if f.endswith('.md')]
        for filename in files:
            remaster_article(os.path.join(folder, filename), os.path.basename(folder))

if __name__ == "__main__":
    main()
