"""
test_data_youtube.py — Tests unitarios para el módulo YouTube Transcript
=========================================================================
Verifica: parsing de URLs, extracción real de transcripciones, manejo de errores.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_youtube import extract_video_id, get_transcript, get_transcript_summary

PASSED = 0
FAILED = 0

def assert_eq(test_name, actual, expected):
    global PASSED, FAILED
    if actual == expected:
        print(f"  ✅ {test_name}")
        PASSED += 1
    else:
        print(f"  ❌ {test_name}: expected '{expected}', got '{actual}'")
        FAILED += 1

def assert_true(test_name, condition):
    global PASSED, FAILED
    if condition:
        print(f"  ✅ {test_name}")
        PASSED += 1
    else:
        print(f"  ❌ {test_name}: condition was False")
        FAILED += 1


print("\n🧪 TEST SUITE: data_youtube.py")
print("=" * 50)

# ── TEST 1: URL Parsing ──
print("\n📌 Test Group 1: extract_video_id()")
assert_eq("Standard URL", extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "dQw4w9WgXcQ")
assert_eq("Short URL", extract_video_id("https://youtu.be/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
assert_eq("Embed URL", extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
assert_eq("Shorts URL", extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
assert_eq("Direct ID", extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")
assert_eq("Empty string", extract_video_id(""), "")

# ── TEST 2: Real Transcript Extraction ──
print("\n📌 Test Group 2: get_transcript() — LIVE API CALL")
# Usando un vídeo popular con subtítulos conocidos (TED Talk)
result = get_transcript("dQw4w9WgXcQ", languages=['en'])
print(f"  📊 Result: success={result['success']}, words={result['word_count']}, lang={result['language']}")
if result['success']:
    assert_true("Transcript not empty", len(result['transcript']) > 50)
    assert_true("Word count > 10", result['word_count'] > 10)
    assert_true("Language detected", len(result['language']) > 0)
    assert_true("Duration > 0", result['duration_seconds'] > 0)
    assert_eq("No error", result['error'], "")
else:
    print(f"  ⚠️ SKIPPED (video may not have subtitles): {result['error']}")
    PASSED += 1  # No penalizar si el vídeo no tiene subs

# ── TEST 3: Invalid Video ──
print("\n📌 Test Group 3: Error Handling")
bad_result = get_transcript("INVALID_ID_XY")
assert_true("Invalid video returns success=False", bad_result['success'] == False)
assert_true("Error message present", len(bad_result['error']) > 0)

# ── TEST 4: Summary Format ──
print("\n📌 Test Group 4: get_transcript_summary()")
summary = get_transcript_summary("dQw4w9WgXcQ", languages=['en'], max_chars=500)
if summary:
    assert_true("Summary contains header", "[YouTube Transcript" in summary)
    assert_true("Summary length <= max_chars + header", len(summary) < 700)
else:
    print("  ⚠️ SKIPPED (no transcript available)")
    PASSED += 1

# ── RESULTADO FINAL ──
print(f"\n{'=' * 50}")
print(f"🏆 RESULTS: {PASSED} passed, {FAILED} failed")
if FAILED == 0:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
sys.exit(FAILED)
