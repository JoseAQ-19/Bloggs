"""
qa_link_validator.py — Verificador HTTP de enlaces en artículos Markdown.

Extrae todos los enlaces [texto](url) de un texto markdown y hace HEAD request
concurrente para clasificarlos como vivos, muertos o timeout.

Uso:
    from qa_link_validator import validate_links
    result = validate_links(markdown_body)
    # result = {"alive": [...], "dead": [...], "timeout": [...]}
"""

import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Regex para extraer enlaces markdown: [anchor](url)
LINK_PATTERN = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')

# Dominios internos que siempre se consideran vivos
INTERNAL_DOMAINS = [
    "novumworld.com",
    "localhost",
    "127.0.0.1",
]

# User-Agent realista para evitar bloqueos por bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Configuración
REQUEST_TIMEOUT = 8  # segundos
MAX_WORKERS = 10     # hilos concurrentes


def _is_internal(url):
    """Verifica si una URL pertenece a un dominio interno."""
    for domain in INTERNAL_DOMAINS:
        if domain in url:
            return True
    return False


def _check_single_url(url):
    """
    Hace HEAD request a una URL individual.
    Returns: (url, status) donde status es 'alive', 'dead', o 'timeout'
    """
    if _is_internal(url):
        return (url, "alive")

    # Limpiar URL de posibles artefactos de markdown
    url = url.rstrip('.,;:')

    try:
        response = requests.head(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        if 200 <= response.status_code < 400:
            return (url, "alive")
        elif response.status_code in (403, 405):
            # Algunos servidores bloquean HEAD, intentar GET
            try:
                response = requests.get(
                    url,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    stream=True  # No descargar el body completo
                )
                response.close()
                if 200 <= response.status_code < 400:
                    return (url, "alive")
            except Exception:
                pass
            # Si 403 en ambos, considerarlo "vivo pero protegido" (no lo matamos)
            return (url, "alive")
        else:
            return (url, "dead")

    except requests.exceptions.Timeout:
        return (url, "timeout")
    except requests.exceptions.ConnectionError:
        return (url, "dead")
    except Exception:
        return (url, "timeout")


def extract_links(markdown_text):
    """
    Extrae todos los enlaces markdown de un texto.
    Returns: list of (anchor_text, url) tuples
    """
    return LINK_PATTERN.findall(markdown_text)


def validate_links(markdown_text, max_workers=MAX_WORKERS):
    """
    Valida todos los enlaces HTTP en un texto markdown.

    Args:
        markdown_text: String con contenido markdown
        max_workers: Número máximo de hilos concurrentes

    Returns:
        dict con tres listas:
        {
            "alive": [{"anchor": str, "url": str}, ...],
            "dead": [{"anchor": str, "url": str}, ...],
            "timeout": [{"anchor": str, "url": str}, ...],
            "total": int,
            "summary": str
        }
    """
    links = extract_links(markdown_text)

    if not links:
        return {
            "alive": [],
            "dead": [],
            "timeout": [],
            "total": 0,
            "summary": "No se encontraron enlaces externos."
        }

    # Deduplicar URLs manteniendo el primer anchor
    seen_urls = {}
    unique_links = []
    for anchor, url in links:
        clean_url = url.rstrip('.,;:')
        if clean_url not in seen_urls:
            seen_urls[clean_url] = anchor
            unique_links.append((anchor, clean_url))

    result = {"alive": [], "dead": [], "timeout": []}

    print(f"   🔗 [LinkValidator] Verificando {len(unique_links)} enlaces únicos...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_link = {}
        for anchor, url in unique_links:
            future = executor.submit(_check_single_url, url)
            future_to_link[future] = (anchor, url)

        for future in as_completed(future_to_link):
            anchor, url = future_to_link[future]
            try:
                _, status = future.result()
                result[status].append({"anchor": anchor, "url": url})
            except Exception:
                result["timeout"].append({"anchor": anchor, "url": url})

    total = len(unique_links)
    alive = len(result["alive"])
    dead = len(result["dead"])
    timeout = len(result["timeout"])

    result["total"] = total
    result["summary"] = (
        f"✅ {alive} vivos | ❌ {dead} muertos | ⏳ {timeout} timeout "
        f"(de {total} únicos)"
    )

    print(f"   📊 [LinkValidator] {result['summary']}")

    return result


# === CLI para testing rápido ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python qa_link_validator.py <archivo.md>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    result = validate_links(content)
    print(f"\n{'='*60}")
    print(f"RESULTADO: {result['summary']}")
    if result["dead"]:
        print(f"\n❌ ENLACES MUERTOS:")
        for link in result["dead"]:
            print(f"   [{link['anchor']}]({link['url']})")
    if result["timeout"]:
        print(f"\n⏳ TIMEOUT:")
        for link in result["timeout"]:
            print(f"   [{link['anchor']}]({link['url']})")
