import json
import subprocess
import time
import os
import glob
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class ToolsHunter:
    @staticmethod
    def get_tutorial_content(niche):
        query = f"{niche} tutorial 2025 how to guide"
        print(f"📹 [ToolsHunter] Buscando tutorial para: {query}...")
        
        videos = ToolsHunter._search_videos(query, limit=3)
        
        if not videos:
            print("⚠️ No se encontraron vídeos.")
            return None
            
        for vid in videos:
            print(f"   🔎 Procesando: {vid['title']} ({vid['id']})")
            
            # Intento 1: Transcript
            transcript = ToolsHunter._get_transcript(vid['id'])
            
            # Intento 2: Fallback a Descripción
            desc = vid.get('description') or ""
            if not transcript and len(desc) > 200:
                print("   ⚠️ Transcript falló. Usando Descripción del vídeo como base.")
                transcript = f"[VIDEO DESCRIPTION SOURCE]\n{desc}\n\n(Note: Transcript unavailable. Use general knowledge about this tool based on title.)"
            
            if transcript:
                print("   ✅ Contenido extraído con éxito.")
                return {
                    "title": vid['title'],
                    "video_url": f"https://youtu.be/{vid['id']}",
                    "transcript": transcript,
                    "niche": niche
                }
                
        return None

    @staticmethod
    def _search_videos(query, limit=3):
        """Usa yt-dlp para buscar IDs, Títulos y Descripciones."""
        import sys
        cmd = [
            sys.executable, "-m", "yt_dlp",
            f"ytsearch{limit}:{query}",
            "--dump-json",
            "--no-playlist",
            "--flat-playlist", 
            "--skip-download"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            candidates = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    candidates.append({
                        "id": data.get('id'),
                        "title": data.get('title', 'Sin Título'),
                        "description": data.get('description') or "" 
                    })
            return candidates
            
        except Exception as e:
            print(f"❌ Error buscando con yt-dlp: {e}")
            return []

    @staticmethod
    def _get_transcript(video_id):
        """Obtiene el texto plano usando yt-dlp (Robusto)."""
        print(f"   ℹ️ Usando yt-dlp para subtítulos: {video_id}")
        
        # Limpiar residuos
        for f in glob.glob(f"transcript-{video_id}.*"):
            try: os.remove(f)
            except: pass

        import sys
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en,es", 
            "--skip-download",
            "--output", f"transcript-{video_id}",
            f"https://youtu.be/{video_id}"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            files = glob.glob(f"transcript-{video_id}.*.vtt")
            if not files: return None
                
            content = ""
            with open(files[0], 'r', encoding='utf-8') as f:
                for line in f:
                    if "-->" in line: continue
                    if line.strip() and not line.startswith("WEBVTT") and not line.startswith("Kind:") and not line.startswith("Language:"):
                        content += line.strip() + " "
            
            # Limpieza final
            for f in glob.glob(f"transcript-{video_id}.*"):
                try: os.remove(f)
                except: pass

            return content.strip()
            
        except Exception as e:
            print(f"⚠️ Error yt-dlp transcript: {e}")
            return None

if __name__ == "__main__":
    # Test
    pass
