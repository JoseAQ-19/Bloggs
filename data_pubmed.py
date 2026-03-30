"""
data_pubmed.py — Golden Stack Module: PubMed E-utilities Integration
====================================================================
Extrae abstracts y metadatos de estudios científicos reales de PubMed
para respaldar artículos de Fitness y Salud con autoridad E-E-A-T.

API: NCBI E-utilities (GRATIS, 3 req/s sin API key, 10 req/s con key)
Docs: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

import re
import logging
import requests
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger("data_pubmed")

# ── CONFIGURACIÓN ──
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SEARCH_URL = f"{PUBMED_BASE}/esearch.fcgi"
FETCH_URL = f"{PUBMED_BASE}/efetch.fcgi"
SUMMARY_URL = f"{PUBMED_BASE}/esummary.fcgi"
REQUEST_TIMEOUT = 20


def search_studies(query: str, max_results: int = 5, min_year: int = 2023, sort: str = "relevance") -> list:
    """
    Busca estudios en PubMed y devuelve una lista de PMIDs.

    Args:
        query: Término de búsqueda (ej: "creatine supplementation muscle hypertrophy").
        max_results: Máximo de resultados (1-20).
        min_year: Año mínimo de publicación.
        sort: Criterio de ordenación ("relevance" o "date").

    Returns:
        Lista de PMIDs (strings).
    """
    try:
        params = {
            "db": "pubmed",
            "term": f"{query} AND humans[Filter] AND {min_year}:{2026}[dp]",
            "retmax": min(max_results, 20),
            "sort": sort,
            "retmode": "json",
        }
        resp = requests.get(SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        data = resp.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        logger.info(f"[PubMed] Found {len(ids)} studies for: '{query[:50]}'")
        return ids

    except requests.RequestException as e:
        logger.warning(f"[PubMed] Search failed: {type(e).__name__}: {e}")
        return []


def fetch_abstracts(pmids: list) -> list:
    """
    Descarga abstracts y metadatos de una lista de PMIDs.

    Args:
        pmids: Lista de PubMed IDs (strings).

    Returns:
        Lista de dicts con keys: pmid, title, authors, journal, year, abstract, doi, url.
    """
    if not pmids:
        return []

    try:
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "xml",
            "retmode": "xml",
        }
        resp = requests.get(FETCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        studies = []

        for article in root.findall(".//PubmedArticle"):
            try:
                # Extraer PMID
                pmid = article.findtext(".//PMID", default="")

                # Título
                title = article.findtext(".//ArticleTitle", default="")

                # Autores (primeros 3)
                authors_list = []
                for author in article.findall(".//Author")[:3]:
                    last = author.findtext("LastName", "")
                    first = author.findtext("ForeName", "")
                    if last:
                        authors_list.append(f"{last} {first}".strip())
                authors_str = ", ".join(authors_list)
                if len(article.findall(".//Author")) > 3:
                    authors_str += " et al."

                # Journal
                journal = article.findtext(".//Journal/Title", default="")

                # Año de publicación
                year = article.findtext(".//PubDate/Year", default="")
                if not year:
                    medline_date = article.findtext(".//PubDate/MedlineDate", default="")
                    year_match = re.search(r'(\d{4})', medline_date)
                    year = year_match.group(1) if year_match else ""

                # Abstract
                abstract_parts = []
                for abstract_text in article.findall(".//AbstractText"):
                    label = abstract_text.get("Label", "")
                    text = abstract_text.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                abstract = " ".join(abstract_parts)

                # DOI
                doi = ""
                for art_id in article.findall(".//ArticleId"):
                    if art_id.get("IdType") == "doi":
                        doi = art_id.text or ""
                        break

                # URL limpia
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                studies.append({
                    "pmid": pmid,
                    "title": title,
                    "authors": authors_str,
                    "journal": journal,
                    "year": year,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                })

            except Exception as e:
                logger.warning(f"[PubMed] Error parsing article: {e}")
                continue

        logger.info(f"[PubMed] ✅ Fetched {len(studies)} abstracts successfully")
        return studies

    except requests.RequestException as e:
        logger.warning(f"[PubMed] Fetch failed: {type(e).__name__}: {e}")
        return []
    except ET.ParseError as e:
        logger.warning(f"[PubMed] XML parse error: {e}")
        return []


def search_and_fetch(query: str, max_results: int = 5, min_year: int = 2023) -> list:
    """
    Pipeline completo: busca en PubMed y devuelve abstracts + metadatos.
    Función principal de integración.
    """
    pmids = search_studies(query, max_results, min_year)
    if not pmids:
        return []
    return fetch_abstracts(pmids)


def format_for_llm(studies: list, max_studies: int = 3) -> str:
    """
    Formatea los resultados de PubMed para inyectar en el contexto del LLM.
    Produce una cadena con citas académicas listas para usar en el artículo.
    """
    if not studies:
        return ""

    parts = ["[PUBMED SCIENTIFIC EVIDENCE — E-E-A-T PRIMARY SOURCES]"]

    for i, study in enumerate(studies[:max_studies], 1):
        parts.append(f"\n📄 Study {i}: {study['title']}")
        parts.append(f"   Authors: {study['authors']}")
        parts.append(f"   Journal: {study['journal']} ({study['year']})")
        parts.append(f"   PMID: {study['pmid']} | URL: {study['url']}")
        if study['doi']:
            parts.append(f"   DOI: https://doi.org/{study['doi']}")

        # Abstract truncado a 500 chars
        abstract = study.get('abstract', '')
        if len(abstract) > 500:
            abstract = abstract[:500].rsplit('. ', 1)[0] + "."
        parts.append(f"   Abstract: {abstract}")

    parts.append("\n[END PUBMED EVIDENCE — Use these citations in the article with hyperlinks]")
    return "\n".join(parts)
