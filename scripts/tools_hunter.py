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
        
        # BÚSQUEDA OPTIMIZADA (TECHNICAL ARCHITECTURE & TEARDOWN + FORUM COMPLAINTS)
        # Buscamos documentación oficial, problemas reales en foros y casos de uso en vez de listados genéricos.
        query = f"technical architecture review, developer benchmark, and user complaints, limitations, bugs, subreddit reviews for {niche} software tools 2026"
        print(f"🧠 [Exa] Buscando inteligencia técnica y dolores reales: {query}...")
        
        try:
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            # Exa hace la magia: Busca y extrae contenido limpio
            result = exa.search_and_contents(
                query,
                type="neural",
                start_published_date=start_date,
                # use_autoprompt=True, # Desactivado
                num_results=1,
                text=True, # Extraer texto completo
                # category="blog" # Dejamos abierto
            )
            
            if result.results:
                hit = result.results[0]
                print(f"   ✅ Encontrado: {hit.title} ({hit.url})")
                
                return {
                    "title": hit.title,
                    "video_url": hit.url, # URL del artículo
                    "transcript": hit.text[:30000], # Texto del artículo (ampliado)
                    "niche": niche
                }
            
            print("   ⚠️ Exa no encontró resultados relevantes.")
            return None
            
        except Exception as e:
            print(f"❌ Error crítico Exa: {e}")
            return None

if __name__ == "__main__":
    # Test
    pass
