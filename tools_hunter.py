import json
import subprocess
import time
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class ToolsHunter:
    @staticmethod
    def get_tutorial_content(niche):
        """
        Busca un tutorial en YouTube y extrae la transcripción.
        Retorna: Dict {title, video_url, transcript} o None.
        """
        # Query optimizada para tutoriales técnicos recientes
        query = f"{niche} tutorial 2025 how to guide"
        print(f"📹 [ToolsHunter] Buscando tutorial para: {query}...")
        
        # Paso 1: Buscar vídeos candidatos (Top 3) con yt-dlp
        videos = ToolsHunter._search_videos(query, limit=3)
        
        if not videos:
            print("⚠️ No se encontraron vídeos.")
            return None
            
        # Paso 2: Intentar extraer transcript del mejor candidato
        for vid in videos:
            print(f"   🔎 Intentando extraer transcript de: {vid['title']} ({vid['id']})")
            transcript = ToolsHunter._get_transcript(vid['id'])
            
            if transcript:
                print("   ✅ Transcript extraído con éxito.")
                return {
                    "title": vid['title'],
                    "video_url": f"https://youtu.be/{vid['id']}",
                    "transcript": transcript,
                    "niche": niche
                }
            else:
                print("   ⚠️ Sin transcript, probando siguiente...")
                
        print("❌ Ningún vídeo candidato tenía transcripción disponible.")
        return None

    @staticmethod
    def _search_videos(query, limit=3):
        """Usa yt-dlp para buscar IDs y Títulos."""
        cmd = [
            "yt-dlp",
            f"ytsearch{limit}:{query}",
            "--dump-json",
            "--no-playlist",
            "--flat-playlist",  # Más rápido, solo metadatos
            "--skip-download"
        ]
        
        try:
            # Ejecutar yt-dlp y capturar output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            candidates = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    candidates.append({
                        "id": data.get('id'),
                        "title": data.get('title', 'Sin Título')
                    })
            return candidates
            
        except Exception as e:
            print(f"❌ Error buscando con yt-dlp: {e}")
            return []

    @staticmethod
    def _get_transcript(video_id):
        """Obtiene el texto plano de los subtítulos."""
        try:
            # Intentar obtener lista de transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Preferir inglés o español generados manual o auto
            # .find_transcript(['en', 'es']) busca el primero disponible en esa lista
            # Si no, .find_generated_transcript(['en', 'es'])
            
            # Estrategia robusta: Coger cualquiera disponible, preferiblemente EN/ES
            try:
                t = transcript_list.find_transcript(['en', 'es'])
            except:
                # Si falla, coger cualquiera (incluso autogenerado en otro idioma y traducirlo seria top, 
                # pero por ahora cogemos el que haya)
                try: 
                    t = transcript_list.find_generated_transcript(['en', 'es'])
                except:
                    # Fallback final: iterar y coger el primero
                    t = next(iter(transcript_list))
            
            # Fetch y unir texto
            data = t.fetch()
            full_text = " ".join([item['text'] for item in data])
            return full_text
            
        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception as e:
            print(f"⚠️ Error transcript API: {e}")
            return None

if __name__ == "__main__":
    # Test
    res = ToolsHunter.get_tutorial_content("python automation")
    if res:
        print(f"Éxito: {res['title']}")
        print(f"Transcript (first 100): {res['transcript'][:100]}...")
