import os
import re
import frontmatter
from dotenv import load_dotenv
from google import genai
from google.genai import types
from exa_py import Exa

# Configuración
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
EXA_KEY = os.getenv("EXA_API_KEY")

if not GEMINI_KEY or not EXA_KEY:
    print("❌ ERROR: Faltan API KEYS (Gemini o Exa).")
    exit(1)

client = genai.Client(api_key=GEMINI_KEY)
exa = Exa(EXA_KEY)

CONTENT_DIRS = [
    'content/ia', 
    'content/crypto', 
    'content/fitness', 
    'content/youtube', 
    'content/viral'
]

# Sin límite (Procesar todo lo que no sea 'fenix_v2')
MAX_REMASTERS = 1000 

PROMPT_REMASTER = """
ACT AS: Senior Tech Journalist & Subject Matter Expert.
TASK: Rewrite this article from scratch to make it High-Quality, Insightful, and Google HCU Compliant.

TOPIC: "{title}"
REAL-TIME DATA (FROM EXA):
{context}

RULES (ZERO TOLERANCE):
1. NO AI FLUFF: Ban words like "Delve", "Tapestry", "In conclusion", "It is important to note".
2. STRUCTURE: Hook -> Deep Dive (Data/Facts) -> Critical Analysis -> Verdict.
3. TONE: Authoritative, slightly cynical (if tech/crypto) or evidence-based (if fitness). Human voice.
4. LENGTH: 1000-1200 words of pure value. No filler.
5. LANGUAGE: Write in the language detected from the title (ES or EN).

OUTPUT: Markdown body ONLY. No Frontmatter.
"""

def get_real_context(query):
    """Busca datos reales en Exa."""
    print(f"   🧠 [Exa] Investigando: {query}...")
    try:
        # Optimizamos query para encontrar análisis profundos
        result = exa.search_and_contents(
            query,
            type="neural",
            num_results=2, # Buscar 2 fuentes para mezclar ideas
            text=True
        )
        context = ""
        if result.results:
            for res in result.results:
                context += f"\nSOURCE ({res.title}):\n{res.text[:8000]}\n"
        return context
    except Exception as e:
        print(f"   ⚠️ Error Exa: {e}")
    return "No new data available. Use general expert knowledge."

def sanitize_h1(text):
    """Elimina el H1 inicial si existe."""
    text = text.lstrip()
    # Elimina '# Titulo' al inicio
    text = re.sub(r'^\s*#\s+.*(\n|$)', '', text, count=1).lstrip()
    return text

def remaster_phoenix_final():
    print("🔥 INICIANDO OPERACIÓN FÉNIX MASIVA (V2)...")
    
    count = 0
    
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        
        files = [f for f in os.listdir(folder) if f.endswith('.md') and not f.startswith('_index')]
        
        for filename in files:
            if count >= MAX_REMASTERS: break
            
            filepath = os.path.join(folder, filename)
            
            try:
                # Cargar Post (Usamos frontmatter lib que es robusta)
                post = frontmatter.load(filepath)
                
                # CRITERIO DE FILTRADO
                # Si ya tiene la marca fenix_v2, saltar.
                if post.get('quality_tier') == 'fenix_v2_notebooklm': # Usamos esta marca nueva
                    continue
                    
                print(f"\n🐦 Remasterizando: {filename}")
                
                # 1. Investigar
                title = post.get('title', 'Untitled')
                context = get_real_context(f"deep analysis facts {title} 2025 2026")
                
                # 2. Reescribir (Gemini)
                print("   ✍️ Reescribiendo con alma humana...")
                prompt = PROMPT_REMASTER.format(title=title, context=context)
                
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=prompt
                )
                new_body = resp.text.strip()
                
                # 3. Sanitización H1 (La clave)
                new_body = sanitize_h1(new_body)
                
                # Validación de seguridad
                if len(new_body) < 1000:
                    print("   ⚠️ Generación muy corta. Abortando guardado.")
                    continue
                
                # 4. Guardado Quirúrgico
                post.content = new_body
                post['quality_tier'] = "fenix_v2_notebooklm" 
                post['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                
                # Truco para preservar comillas dobles en descripción si existen
                # La librería frontmatter suele manejarlo bien
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                    
                print(f"   ✅ ÉXITO: {filename} REMASTERIZADO.")
                count += 1
                
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n🔥 OPERACIÓN MASIVA FINALIZADA. {count} artículos renacidos.")

if __name__ == "__main__":
    from datetime import datetime
    remaster_phoenix_final()
