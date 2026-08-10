"""
test_data_youtube.py — Tests unitarios para el módulo YouTube Transcript
=========================================================================
Verifica: parsing de URLs, extracción real de transcripciones, manejo de errores.
"""

import sys
import os

from data_youtube import extract_video_id, get_transcript, get_transcript_summary

def test_youtube_url_parsing():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("") == ""

def test_youtube_transcript_extraction():
    result = get_transcript("dQw4w9WgXcQ", languages=['en'])
    if result['success']:
        assert len(result['transcript']) > 50
        assert result['word_count'] > 10
        assert len(result['language']) > 0
        assert result['duration_seconds'] > 0
    
    bad_result = get_transcript("INVALID_ID_XY")
    assert bad_result['success'] is False
    assert len(bad_result['error']) > 0

    summary = get_transcript_summary("dQw4w9WgXcQ", languages=['en'], max_chars=500)
    if summary:
        assert "[YouTube Transcript" in summary

if __name__ == "__main__":
    test_youtube_url_parsing()
    test_youtube_transcript_extraction()
    print("✅ test_data_youtube passed")
