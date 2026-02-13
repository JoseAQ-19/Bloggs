import os
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

# Excluir 'tools' (ya es calidad nueva)

# Límite de seguridad
MAX_REMASTERS = 3

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
        result = exa.search_and_contents(
            query,
            type="neural",
            num_results=1,
            text=True
        )
        if result.results:
            return result.results[0].text[:15000] # Contexto denso
    except Exception as e:
        print(f"   ⚠️ Error Exa: {e}")
    return "No new data available. Use general expert knowledge."

def remaster_phoenix():
    print("🔥 INICIANDO OPERACIÓN FÉNIX (REMASTERIZACIÓN DE TEXTO)...")
    
    count = 0
    
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        if count >= MAX_REMASTERS: break
        
        files = [f for f in os.listdir(folder) if f.endswith('.md') and not f.startswith('_index')]
        # Ordenar por fecha o nombre para ser deterministas? Mejor aleatorio o secuencial.
        
        for filename in files:
            if count >= MAX_REMASTERS: break
            
            filepath = os.path.join(folder, filename)
            
            try:
                # Cargar Post
                post = frontmatter.load(filepath)
                
                # CRITERIO DE FILTRADO: ¿Ya fue remasterizado?
                # Podemos usar un metadato custom o chequear si tiene "TL;DR" (viejo) vs estructura nueva.
                # Si tiene "TL;DR" en el cuerpo (aunque lo limpiamos antes, el estilo viejo era corto).
                # Mejor: Si tiene menos de 4KB de tamaño, es candidato seguro a ser basura antigua.
                
                file_size = os.path.getsize(filepath)
                if file_size > 6000: # Si ya es grande, asumimos que es bueno o ya procesado
                    continue
                    
                print(f"\n🐦 Remasterizando: {filename} (Size: {file_size} bytes)")
                
                # 1. Investigar
                title = post.get('title', 'Untitled')
                context = get_real_context(f"latest detailed analysis facts {title} 2025")
                
                # 2. Reescribir (Gemini)
                print("   ✍️ Reescribiendo con alma humana...")
                prompt = PROMPT_REMASTER.format(title=title, context=context)
                
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=prompt
                )
                new_body = resp.text.strip()
                
                # Validación de seguridad
                if len(new_body) < 1000:
                    print("   ⚠️ Generación muy corta. Abortando guardado.")
                    continue
                
                # 3. Guardado Quirúrgico (Preservar Frontmatter)
                # frontmatter.dump sobrescribe todo, pero mantiene los metadatos que ya estaban en 'post'
                # Solo cambiamos el contenido.
                post.content = new_body
                
                # MARCA DE CALIDAD (Para no volver a procesarlo)
                post['quality_tier'] = "fenix_v1" 
                
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                    
                new_size = os.path.getsize(filepath)
                print(f"   ✅ ÉXITO: {filename} | {file_size}B -> {new_size}B (+{new_size-file_size})")
                
                count += 1
                
            except Exception as e:
                print(f"   ❌ Error en {filename}: {e}")

    print(f"\n🔥 OPERACIÓN FINALIZADA. {count} artículos renacidos.")

if __name__ == "__main__":
    remaster_phoenix()
