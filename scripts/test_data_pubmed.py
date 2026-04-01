"""
test_data_pubmed.py — Tests unitarios para el módulo PubMed E-utilities
========================================================================
Verifica: búsqueda real en PubMed, extracción de abstracts, formateo LLM.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pubmed import search_studies, fetch_abstracts, search_and_fetch, format_for_llm

PASSED = 0
FAILED = 0

def assert_true(test_name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        print(f"  ✅ {test_name}")
        PASSED += 1
    else:
        print(f"  ❌ {test_name}: {detail}")
        FAILED += 1


print("\n🧪 TEST SUITE: data_pubmed.py")
print("=" * 50)

# ── TEST 1: Search PubMed ──
print("\n📌 Test Group 1: search_studies() — LIVE API CALL")
pmids = search_studies("creatine supplementation muscle hypertrophy", max_results=3, min_year=2022)
print(f"  📊 Found {len(pmids)} PMIDs: {pmids}")
assert_true("Returns list", isinstance(pmids, list))
assert_true("At least 1 result", len(pmids) >= 1, f"Got {len(pmids)} results")
assert_true("PMIDs are strings", all(isinstance(p, str) for p in pmids))
assert_true("PMIDs are numeric", all(p.isdigit() for p in pmids))

# ── TEST 2: Fetch Abstracts ──
print("\n📌 Test Group 2: fetch_abstracts() — XML PARSING")
if pmids:
    studies = fetch_abstracts(pmids[:2])
    print(f"  📊 Fetched {len(studies)} studies")
    assert_true("Returns list of studies", len(studies) >= 1, f"Got {len(studies)}")
    
    if studies:
        study = studies[0]
        print(f"  📄 First study: {study.get('title', 'NO TITLE')[:80]}...")
        assert_true("Has pmid", bool(study.get("pmid")))
        assert_true("Has title", bool(study.get("title")))
        assert_true("Has url", "pubmed.ncbi.nlm.nih.gov" in study.get("url", ""))
        assert_true("Has journal", bool(study.get("journal")))
        assert_true("Has year", bool(study.get("year")))
        assert_true("Has abstract", len(study.get("abstract", "")) > 10, f"Abstract length: {len(study.get('abstract', ''))}")
else:
    print("  ⚠️ SKIPPED (no PMIDs from search)")

# ── TEST 3: Full Pipeline ──
print("\n📌 Test Group 3: search_and_fetch() — FULL PIPELINE")
full_results = search_and_fetch("protein synthesis resistance training", max_results=2, min_year=2023)
print(f"  📊 Full pipeline returned {len(full_results)} studies")
assert_true("Full pipeline returns results", len(full_results) >= 1)

# ── TEST 4: LLM Formatting ──
print("\n📌 Test Group 4: format_for_llm()")
if full_results:
    formatted = format_for_llm(full_results, max_studies=2)
    print(f"  📊 Formatted output: {len(formatted)} chars")
    assert_true("Contains header", "PUBMED SCIENTIFIC EVIDENCE" in formatted)
    assert_true("Contains PMID", "PMID:" in formatted)
    assert_true("Contains URL", "pubmed.ncbi.nlm.nih.gov" in formatted)
    assert_true("Contains footer", "END PUBMED EVIDENCE" in formatted)
else:
    print("  ⚠️ SKIPPED (no results to format)")

# ── TEST 5: Empty query handling ──
print("\n📌 Test Group 5: Edge Cases")
empty_results = search_studies("", max_results=1)
assert_true("Empty query returns list", isinstance(empty_results, list))

# ── RESULTADO FINAL ──
print(f"\n{'=' * 50}")
print(f"🏆 RESULTS: {PASSED} passed, {FAILED} failed")
if FAILED == 0:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
sys.exit(FAILED)
