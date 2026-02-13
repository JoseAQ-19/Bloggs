from exa_py import Exa
import os
from dotenv import load_dotenv

load_dotenv()

class ToolsHunter:
    @staticmethod
    def get_tutorial_content(niche):
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            print("❌ Error: EXA_API_KEY no encontrada.")
            return None
            
        exa = Exa(api_key)
        
        # Búsqueda orientada a tutoriales técnicos escritos
        query = f"best step-by-step technical tutorial for {niche} tools 2025"
        print(f"🧠 [Exa] Buscando conocimiento: {query}...")
        
        try:
            # Exa hace la magia: Busca y extrae contenido limpio
            result = exa.search_and_contents(
                query,
                type="neural",
                # use_autoprompt=True, # REMOVED: Deprecated/Invalid
                num_results=1,
                text=True, # Extraer texto completo
                # category="blog" # REMOVED: Invalid category
            )
            
            if result.results:
                hit = result.results[0]
                print(f"   ✅ Encontrado: {hit.title} ({hit.url})")
                
                return {
                    "title": hit.title,
                    "video_url": hit.url, # Mantenemos key 'video_url' por compatibilidad, aunque es web
                    "transcript": hit.text[:25000], # Texto del artículo
                    "niche": niche
                }
            
            print("   ⚠️ Exa no encontró resultados relevantes.")
            return None
            
        except Exception as e:
            print(f"❌ Error crítico Exa: {e}")
            return None

if __name__ == "__main__":
    # Test
    res = ToolsHunter.get_tutorial_content("python automation")
    if res:
        print(f"Título: {res['title']}")
        print(f"Contenido (inicio): {res['transcript'][:200]}...")
