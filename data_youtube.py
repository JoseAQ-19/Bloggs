"""
data_youtube.py — Golden Stack Module: YouTube Transcript Extractor
===================================================================
Extrae transcripciones completas de vídeos de YouTube para alimentar
al LLM con contenido original en lugar de depender solo de noticias.

API: youtube-transcript-api (GRATIS, sin API key)
"""

import re
import logging

logger = logging.getLogger("data_youtube")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
    YT_AVAILABLE = True
except ImportError:
    YT_AVAILABLE = False
    logger.warning("[data_youtube] youtube-transcript-api not installed. pip install youtube-transcript-api")


def extract_video_id(url_or_id: str) -> str:
    """
    Extrae el video ID de cualquier formato de URL de YouTube.
    Soporta: youtu.be/ID, youtube.com/watch?v=ID, youtube.com/shorts/ID, o ID directo.
    """
    if not url_or_id:
        return ""

    # Patrón para URLs largas y cortas
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtube\.com/embed/|youtube\.com/shorts/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # ID directo
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return url_or_id.strip()[:11]  # Fallback: asumir que es un ID


def get_transcript(video_url_or_id: str, languages: list = None, max_chars: int = 15000) -> dict:
    """
    Obtiene la transcripción completa de un vídeo de YouTube.

    Args:
        video_url_or_id: URL completa o ID del vídeo.
        languages: Lista de idiomas preferidos (ej: ['es', 'en']).
        max_chars: Límite de caracteres para la transcripción.

    Returns:
        dict con keys:
            - success (bool)
            - video_id (str)
            - transcript (str): Texto completo de la transcripción.
            - language (str): Idioma detectado.
            - duration_seconds (float): Duración estimada del vídeo.
            - word_count (int): Conteo de palabras.
            - error (str): Mensaje de error si falla.
    """
    if not YT_AVAILABLE:
        return {
            "success": False,
            "video_id": "",
            "transcript": "",
            "language": "",
            "duration_seconds": 0,
            "word_count": 0,
            "error": "youtube-transcript-api not installed"
        }

    if languages is None:
        languages = ['es', 'en', 'pt', 'fr', 'de']

    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        return {
            "success": False, "video_id": "", "transcript": "",
            "language": "", "duration_seconds": 0, "word_count": 0,
            "error": "Invalid video URL or ID"
        }

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prioridad: Manual > Generated, en el idioma preferido
        transcript = None
        detected_lang = ""

        # Intentar transcripciones manuales primero
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
            detected_lang = transcript.language_code
        except NoTranscriptFound:
            pass

        # Si no hay manual, intentar generated
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(languages)
                detected_lang = transcript.language_code
            except NoTranscriptFound:
                # Último recurso: tomar la primera disponible y traducir
                try:
                    available = list(transcript_list)
                    if available:
                        transcript = available[0]
                        detected_lang = transcript.language_code
                        # Intentar traducir al idioma preferido
                        try:
                            transcript = transcript.translate(languages[0])
                            detected_lang = languages[0]
                        except Exception:
                            pass
                except Exception:
                    pass

        if transcript is None:
            return {
                "success": False, "video_id": video_id, "transcript": "",
                "language": "", "duration_seconds": 0, "word_count": 0,
                "error": f"No transcript found for video {video_id} in languages {languages}"
            }

        # Extraer el texto
        entries = transcript.fetch()
        full_text = " ".join([entry['text'] for entry in entries])

        # Duración estimada (último timestamp + duración del último segmento)
        duration = 0
        if entries:
            last = entries[-1]
            duration = last.get('start', 0) + last.get('duration', 0)

        # Truncar si excede el límite
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars].rsplit(' ', 1)[0] + "..."

        word_count = len(full_text.split())

        logger.info(f"[YouTube] ✅ Transcript extracted: {video_id} | {detected_lang} | {word_count} words | {duration:.0f}s")

        return {
            "success": True,
            "video_id": video_id,
            "transcript": full_text,
            "language": detected_lang,
            "duration_seconds": round(duration, 1),
            "word_count": word_count,
            "error": ""
        }

    except TranscriptsDisabled:
        return {
            "success": False, "video_id": video_id, "transcript": "",
            "language": "", "duration_seconds": 0, "word_count": 0,
            "error": f"Transcripts are disabled for video {video_id}"
        }
    except VideoUnavailable:
        return {
            "success": False, "video_id": video_id, "transcript": "",
            "language": "", "duration_seconds": 0, "word_count": 0,
            "error": f"Video {video_id} is unavailable"
        }
    except Exception as e:
        return {
            "success": False, "video_id": video_id, "transcript": "",
            "language": "", "duration_seconds": 0, "word_count": 0,
            "error": f"Unexpected error: {type(e).__name__}: {e}"
        }


def get_transcript_summary(video_url_or_id: str, languages: list = None, max_chars: int = 4000) -> str:
    """
    Versión simplificada: devuelve solo el texto o un string vacío.
    Ideal para inyectar directamente en el contexto del LLM.
    """
    result = get_transcript(video_url_or_id, languages, max_chars)
    if result["success"]:
        return f"[YouTube Transcript | {result['language']} | {result['word_count']} words | {result['duration_seconds']}s]\n{result['transcript']}"
    return ""
