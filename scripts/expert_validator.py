import re
from urllib.parse import urlparse

AUTHORITY_SCORES = {
    # Dominios académicos y científicos
    ".edu": 95, ".ac.uk": 95, "scholar.google": 90, "nature.com": 95, "sciencedirect.com": 90, "ncbi.nlm.nih.gov": 95,
    # Dominios institucionales y gubernamentales
    ".gov": 98, "ecb.europa.eu": 95, "sec.gov": 95, "imf.org": 95, "who.int": 98,
    # Medios de autoridad Tier 1
    "reuters.com": 85, "bloomberg.com": 85, "wsj.com": 85, "ft.com": 85, "nytimes.com": 85,
    # Tech authority
    "arstechnica.com": 75, "techcrunch.com": 75, "wired.com": 75, "theverge.com": 70,
    # Medios locales de calidad
    "elpais.com": 70, "elmundo.es": 70, "xataka.com": 70,
    # Bajo / desconocido
    "medium.com": 30, "substack.com": 40, "reddit.com": 20, "quora.com": 20
}

def validate_citation_authority(url):
    """
    Valida la autoridad de un enlace basándose en el dominio.
    Retorna un diccionario con score y recomendación.
    """
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
            
        base_score = 30 # Default for unknown blogs
        for key, score in AUTHORITY_SCORES.items():
            if key in domain:
                base_score = score
                break
                
        # Bonus for specific known high-quality paths or TLDs
        if domain.endswith(".org") and base_score == 30:
            base_score = 60 # Non-profits are generally better than random .coms
            
        return {
            "authority_score": base_score,
            "is_eeat_compliant": base_score >= 70,
            "domain": domain
        }
    except:
        return {
            "authority_score": 0,
            "is_eeat_compliant": False,
            "domain": "unknown"
        }

def extract_all_markdown_links(markdown_text):
    """Extrae todos los enlaces [texto](url) del markdown."""
    # Pattern to match [text](url)
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.finditer(pattern, markdown_text)
    links = []
    for match in matches:
        links.append({
            "full_match": match.group(0),
            "text": match.group(1),
            "url": match.group(2),
            "start": match.start(),
            "end": match.end()
        })
    return links
