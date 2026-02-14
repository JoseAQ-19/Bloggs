
import os
import time
import frontmatter
from dotenv import load_dotenv
from google import genai
from researcher import ResearcherV3

# Configuración
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not GEMINI_KEY:
    print("❌ ERROR: Falta GEMINI_API_KEY.")
    exit(1)

client = genai.Client(api_key=GEMINI_KEY)
researcher = ResearcherV3()

CONTENT_DIRS = [
    'content/ia', 
    'content/crypto', 
    'content/fitness', 
    'content/youtube', 
    'content/viral'
]

# NO LÍMITE (Massive Scale)
# MAX_REMASTERS = 9999 

PROMPT_REMASTER = """
ACT AS: Senior Tech Journalist & Subject Matter Expert (NotebookLM Analyst Profile).
TASK: Rewrite this article from scratch to make it High-Quality, Insightful, and Google HCU Compliant.

TOPIC: "{title}"
REAL-TIME DATA & RESEARCH (FROM NOTEBOOKLM/GEMINI):
{context}

RULES (ZERO TOLERANCE):
1. NO AI FLUFF: Ban words like "Delve", "Tapestry", "In conclusion", "It is important to note".
2. STRUCTURE: Hook -> Deep Dive (Data/Facts) -> Critical Analysis -> Verdict.
3. TONE: Authoritative, slightly cynical (if tech/crypto) or evidence-based (if fitness). Human voice.
4. LENGTH: 1200-1500 words of pure value. No filler.
5. LANGUAGE: {language} (MANDATORY). Translate source material if needed.

OUTPUT: Markdown body ONLY. No Frontmatter. Do NOT wrap in ```markdown blocks.
"""

def remaster_phoenix_notebooklm():
    print(f"\n🔥 INICIANDO OPERACIÓN FÉNIX: PROTOCOLO NOTEBOOKLM (MASSIVE SCALE)...")
    
    count = 0
    skipped = 0
    total_files = 0
    
    # Pre-calcular total
    for folder in CONTENT_DIRS:
        if os.path.exists(folder):
            total_files += len([f for f in os.listdir(folder) if f.endswith('.md')])
    
    print(f"📂 Total Archivos Detectados: {total_files}")
    
    for folder in CONTENT_DIRS:
        if not os.path.exists(folder): continue
        
        files = [f for f in os.listdir(folder) if f.endswith('.md') and not f.startswith('_index')]
        
        for filename in files:
            filepath = os.path.join(folder, filename)
            
            try:
                # Cargar Post
                post = frontmatter.load(filepath)
                
                # CRITERIOS DE SALIDA (Para no reprocesar lo bueno)
                # 1. Ya procesado por Fénix
                if post.get('quality_tier', '').startswith('fenix'):
                    skipped += 1
                    continue
                    
                # 2. Contenido suficientemente largo (> 8KB) y NO antiguo
                # Si es > 8KB asumimos que es denso. Si es < 6KB es candidato fijo.
                file_size = os.path.getsize(filepath)
                if file_size > 8000 and not post.get('draft'):
                    skipped += 1
                    continue
                    
                print(f"\n🐦 Remasterizando: {filename} (Size: {file_size} bytes)")
                title = post.get('title', 'Untitled')
                
                # 1. INVESTIGACIÓN (ResearcherV3 -> NotebookLM/Gemini)
                print(f"   🧠 [Researcher] Investigando: '{title}'...")
                research_data = researcher.research(title)
                
                context = "Global Expert Knowledge"
                if research_data and "content" in research_data:
                    context = research_data["content"]
                    print(f"   ✅ Contexto obtenido ({len(context)} chars). Fuente: {research_data.get('layer', 'Unknown')}")
                else:
                    print("   ⚠️ Investigación falló, improvisando con conocimiento base del modelo.")

                # 2. REESCRITURA (Gemini Pro)
                print("   ✍️  Reescribiendo con estilo NotebookLM Analyst...")
                target_lang = post.get('language', 'es').upper() # ES or EN
                prompt = PROMPT_REMASTER.format(title=title, context=context[:25000], language=target_lang)
                
                resp = client.models.generate_content(
                    model='gemini-2.0-flash', 
                    contents=prompt
                )
                
                if not resp.text:
                    print("   ❌ Error: Respuesta vacía de Gemini.")
                    continue
                    
                new_body = resp.text.strip()
                
                # CLEANUP: Eliminar bloques de código markdown ```markdown ... ```
                if new_body.startswith("```"):
                    new_body = new_body.split("\n", 1)[1] # Quitar primera línea ```markdown
                    if new_body.endswith("```"):
                       new_body = new_body.rsplit("\n", 1)[0] # Quitar última línea ```
                
                new_body = new_body.strip()
                
                # Validación de seguridad
                if len(new_body) < 1500:
                    print(f"   ⚠️ Generación muy corta ({len(new_body)} chars). Abortando guardado.")
                    continue
                
                # 3. GUARDADO
                post.content = new_body
                post['quality_tier'] = "fenix_v2_notebooklm" 
                post['last_updated'] = time.strftime("%Y-%m-%d")
                
                # Preservar tags, pero añadir 'remastered'
                tags = post.get('tags', [])
                if 'remastered' not in tags:
                    tags.append('remastered')
                post['tags'] = tags
                
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                    
                new_size = os.path.getsize(filepath)
                gain = new_size - file_size
                print(f"   ✅ ÉXITO: {filename} | {file_size}B -> {new_size}B (+{gain}B)")
                
                count += 1
                
                # Rate Limiting suave (para evitar 429 masivo en Gemini, aunque tenemos RPD alto)
                time.sleep(2) 
                
            except Exception as e:
                print(f"   ❌ Error procesando {filename}: {e}")

    print(f"\n🔥 OPERACIÓN FÉNIX COMPLETADA.")
    print(f"   ✅ Remasterizados: {count}")
    print(f"   ⏭️ Saltados (Ya buenos): {skipped}")
    print(f"   📉 Errores/Ignorados: {total_files - count - skipped}")

if __name__ == "__main__":
    remaster_phoenix_notebooklm()
