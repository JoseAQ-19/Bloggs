"""
test_data_pubmed.py — Tests unitarios para el módulo PubMed E-utilities
========================================================================
Verifica: búsqueda real en PubMed, extracción de abstracts, formateo LLM.
"""

import sys
import os

from data_pubmed import search_studies, fetch_abstracts, search_and_fetch, format_for_llm

def test_pubmed_pipeline():
    pmids = search_studies("creatine supplementation muscle hypertrophy", max_results=3, min_year=2022)
    assert isinstance(pmids, list), "PMIDs is list"
    assert len(pmids) >= 1, "At least 1 PMID found"
    assert all(isinstance(p, str) for p in pmids), "PMIDs are strings"
    assert all(p.isdigit() for p in pmids), "PMIDs are numeric"

    if pmids:
        studies = fetch_abstracts(pmids[:2])
        assert isinstance(studies, list), "Studies is list"
        if studies:
            study = studies[0]
            assert bool(study.get("pmid")), "Study has PMID"
            assert bool(study.get("title")), "Study has title"
            assert "pubmed.ncbi.nlm.nih.gov" in study.get("url", "")

    full_results = search_and_fetch("protein synthesis resistance training", max_results=2, min_year=2023)
    assert isinstance(full_results, list), "Full results is list"

    if full_results:
        formatted = format_for_llm(full_results, max_studies=2)
        assert "PUBMED SCIENTIFIC EVIDENCE" in formatted

    empty_results = search_studies("", max_results=1)
    assert isinstance(empty_results, list), "Empty search is list"

if __name__ == "__main__":
    test_pubmed_pipeline()
    print("✅ test_data_pubmed passed")
