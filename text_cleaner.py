"""
text_cleaner.py — Ingeniero de Datos (Módulo extraído de main.py y utils.py)

Contiene TODA la lógica de procesamiento de texto, regex, saneamiento de Markdown
y extracción de esquemas SEO, centralizando el formateo.
"""
import re
import unicodedata
import logging
import time
import random
from urllib.parse import urlparse, unquote

# ═══════════════════════════════════════════════════════════════════
# CONSTANTES DE DETECCIÓN Y CONFIANZA
# ═══════════════════════════════════════════════════════════════════

TRUSTED_DOMAINS = {
    'reuters.com', 'bloomberg.com', 'nytimes.com', 'wsj.com', 'ft.com',
    'cnbc.com', 'techcrunch.com', 'theverge.com', 'wired.com', 'arstechnica.com',
    'nature.com', 'science.org', 'pubmed.ncbi.nlm.nih.gov', 'arxiv.org',
    'github.com', 'stackoverflow.com', 'reddit.com', 'ycombinator.com',
    'xataka.com', 'elpais.com', 'elmundo.es', 'lavanguardia.com', 'cincodias.elpais.com',
    'boe.es', 'cnmv.es', 'sec.gov', 'ecb.europa.eu', 'imf.org',
    'coindesk.com', 'coingecko.com', 'decrypt.co', 'theblock.co',
    'youtube.com', 'twitter.com', 'x.com', 'linkedin.com',
    'forbes.com', 'bbc.com', 'bbc.co.uk', 'theguardian.com',
    'statista.com', 'mckinsey.com', 'hbr.org', 'economist.com',
}

PROMPT_LEAK_PATTERNS = [
    r'ACTÚA COMO:', r'TAREA:', r'TITULO \(NUEVO\):', r'TÍTULO NUEVO',
    r'Here is the article', r'ROLE:', r'TASK:', r'MANDATORY RULES',
    r'CRITICAL FORMATTING RULES'
]

CHATBOT_PREAMBLE_PATTERNS = [
    r'^(?:Aquí (?:está|tienes) el artículo\.?\s*\n*)',
    r'^(?:Here is the article\.?\s*\n*)',
    r'^(?:Sure[,!]?\s*(?:here (?:is|you go)).*?\n*)',
    r'^(?:Claro[,!]?\s*(?:aquí (?:tienes|está)).*?\n*)',
    r'^(?:Of course[,!]?\s*.*?\n*)',
    r'^(?:Let me\s.*?\n*)',
    r'^(?:I\'ll\s.*?\n*)',
    r'^(?:Below is\s.*?\n*)',
    r'^(?:The following article.*?\n*)',
    r'^(?:El siguiente artículo.*?\n*)',
    r'^(?:A continuación.*?\n*)',
    r'^(?:Here\'s the.*?\n*)',
]

AI_SELF_REFERENCE_PATTERNS = [
    r'As an AI(?: language model)?.*?,?',
    r'Como(?: un)? modelo de lenguaje(?: de IA| de inteligencia artificial)?,?',
    r'I am an AI.*?\.',
    r'Soy una IA.*?\.',
    r'Como IA, no (?:tengo|puedo).*?\,',
    r'I don\'t have personal opinions.*?,',
    r'No tengo opiniones personales.*?,',
    r'I cannot foresee the future.*?,',
    r'It is not possible for me to.*?,',
    r'As a virtual assistant.*?,',
    r'I am not capable of.*?,',
    r'Sin embargo, como IA.*?,',
    r'Please note that I am.*?,',
]

# ═══════════════════════════════════════════════════════════════════
# GOOGLE NEWS LINK RESOLVER (Desofuscador)
# ═══════════════════════════════════════════════════════════════════

def _resolve_google_news_url(opaque_url: str, timeout: int = 10) -> str:
    """
    Resuelve una URL opaca de Google News RSS (news.google.com/rss/articles/...)
    siguiendo las redirecciones HTTP para obtener el Deep Link real.
    Retorna la URL final o la original si falla.
    """
    try:
        import requests as req_lib
    except ImportError:
        return opaque_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # Seguir redirecciones con HEAD para rapidez
        resp = req_lib.head(
            opaque_url, headers=headers, allow_redirects=True, timeout=timeout
        )
        final_url = resp.url

        # Validar que no sea otra redirección de Google
        if 'google.com' not in final_url and final_url != opaque_url:
            return final_url

        # Si HEAD no resolvió, intentar GET completo
        resp = req_lib.get(
            opaque_url, headers=headers, allow_redirects=True, timeout=timeout, stream=True
        )
        final_url = resp.url
        if 'google.com' not in final_url:
            return final_url

    except Exception as e:
        logging.debug(f"Link Resolver falló para {opaque_url[:60]}: {e}")

    return opaque_url  # Fallback: devolver la original


def resolve_google_news_links(text: str) -> str:
    """
    Escanea el texto Markdown buscando enlaces de Google News RSS
    y los reemplaza por los Deep Links reales resueltos.
    Si la resolución falla para un enlace, se conserva el texto ancla
    como referencia en negrita (sin link roto).
    """
    google_news_pattern = re.compile(
        r'\[([^\]]+)\]\((https?://news\.google\.com/rss/articles/[^)]+)\)'
    )
    matches = google_news_pattern.findall(text)
    if not matches:
        return text

    print(f"   🔗 [Link Resolver] Encontrados {len(matches)} enlaces de Google News. Resolviendo...")
    resolved_count = 0

    for anchor, opaque_url in matches:
        real_url = _resolve_google_news_url(opaque_url)
        original_md = f'[{anchor}]({opaque_url})'

        if real_url != opaque_url and 'google.com' not in real_url:
            # Éxito: reemplazar con deep link
            text = text.replace(original_md, f'[{anchor}]({real_url})')
            resolved_count += 1
        else:
            # Fallo: conservar el ancla como texto en negrita sin link roto
            text = text.replace(original_md, f'**{anchor}**')

    print(f"   ✅ [Link Resolver] {resolved_count}/{len(matches)} enlaces resueltos a Deep Links.")
    return text


# ═══════════════════════════════════════════════════════════════════
# FAQ HEADING HIERARCHY FIXER (SEO Semántico)
# ═══════════════════════════════════════════════════════════════════

def fix_faq_heading_hierarchy(text: str) -> str:
    """
    Asegura que las preguntas FAQ (### H3) siempre tengan un
    ## H2 padre que las englobe. Busca patrones comunes de
    secciones FAQ sin H2 y los corrige.
    """
    # Patrón: detectar si hay un H3 de FAQ sin un H2 previo que lo contenga
    faq_h3_patterns = [
        r'(^|\n)(### (?:¿|Is |How |What |Can |Why |Does |Should |Where |When |Will ))',
    ]

    # Buscar si ya existe un H2 de FAQs
    has_faq_h2 = bool(re.search(
        r'^## (?:Real User FAQs|Preguntas Frecuentes|Frequently Asked Questions|FAQs|FAQ)',
        text, flags=re.MULTILINE | re.IGNORECASE
    ))

    if has_faq_h2:
        return text  # Ya tiene estructura correcta

    # Buscar la primera pregunta FAQ (H3 que empieza con ¿ o palabras interrogativas EN)
    faq_start = re.search(
        r'^(### (?:¿[^\n]+|(?:Is|How|What|Can|Why|Does|Should|Where|When|Will) [^\n]+))',
        text, flags=re.MULTILINE
    )

    if faq_start:
        # Determinar idioma basado en contenido
        is_spanish = '¿' in text[:500] or bool(re.search(r'DISCLAIMER.*inversión', text, re.IGNORECASE))
        faq_header = '## Preguntas Frecuentes' if is_spanish else '## Real User FAQs'

        # Inyectar H2 justo antes de la primera pregunta H3 detectada
        pos = faq_start.start()
        # Buscar un separador --- antes, si existe
        pre_separator = text.rfind('---', max(0, pos - 20), pos)
        inject_pos = pre_separator if pre_separator != -1 else pos

        text = text[:inject_pos] + f'\n\n{faq_header}\n\n' + text[inject_pos:]
        print(f"   📐 [FAQ Fixer] Inyectado '{faq_header}' como H2 padre de las FAQs.")

    return text


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES CLAVE DE PROCESAMIENTO
# ═══════════════════════════════════════════════════════════════════

def sanitize_slug(text: str) -> str:
    """Genera un slug SEO-friendly determinista para crear URLs limpias."""
    if not text:
        return f"post-{int(time.time())}"
    slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    slug = slug.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')[:100]

def remove_redundant_h1(text: str) -> str:
    """Down-casting de H1 a H2 para evitar el problema del doble título y proteger la semántica SEO."""
    if not text:
        return text
    return re.sub(r'^#\s+', '## ', text, flags=re.MULTILINE)

def extract_json_ld(text: str) -> str:
    """Para manejar los esquemas SEO sin que se pierdan en formatos crudos."""
    if not text:
        return text
    # 1. Preservar bloques <script> enteros o convertir bloques ```json de schema
    text = re.sub(r'(?i)```html\n?(<script type="application/ld\+json">.*?</script>)\n?```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'(?i)```json\n?(\{.*?"@context".*?\})\n?```', r'<script type="application/ld+json">\n\1\n</script>', text, flags=re.DOTALL)

    # 2. Purgar bloque JSON-LD de NewsArticle o Article (el orquestador inyecta el oficial)
    text = re.sub(r'(?si)<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?(?:"@type"\s*:\s*["\'](?:News)?Article["\']).*?</script>\s*', '', text)

    # 3. Purgar bloques JSON-LD "desnudos" que el LLM suelta sin <script> tags
    #    Ejemplo: un bloque { "@context": "https://schema.org", "@type": "NewsArticle"...}
    text = re.sub(r'(?s)\n\{[^{}]*"@context"\s*:\s*"https?://schema\.org"[^{}]*"@type"\s*:\s*"(?:News)?Article"[^{}]*\}\s*', '\n', text)

    # 4. Purgar secciones markdown-header del LLM que encabezan el JSON
    text = re.sub(r'(?i)\*\*JSON-LD:\*\*.*?\n', '', text)
    text = re.sub(r'(?im)^#{2,3}\s*(?:Schema Markup|Metadatos SEO|Structured Data).*?\n', '', text)
    text = re.sub(r'(?i)\*\*(?:Data|FAQ) Schema\*\*\s*\n', '', text)

    # 5. Limpiar mainEntityOfPage con example.com (huella digital del LLM)
    text = re.sub(r'(?s)<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?example\.com.*?</script>\s*', '', text)
    
    return text

def clean_markdown(text: str) -> str:
    """Elimina artefactos raros de la IA, escapes residuales y formatea el body del artículo."""
    if not text:
        return text

    # Escudo Anti-Fugas
    for fp in PROMPT_LEAK_PATTERNS:
        if re.search(fp, text, flags=re.IGNORECASE):
            raise Exception(f"Fuga de prompt masiva detectada: {fp}")

    # Limpieza de Chatbots y Meta-Comentarios
    for pattern in CHATBOT_PREAMBLE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    for phrase in AI_SELF_REFERENCE_PATTERNS:
        text = re.sub(phrase, '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\*?No (?:hay )?(?:additional )?dat(?:a|os)(?: adicionales?)? (?:available|disponibles?)\.?\*?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\*?No se (?:encontraron|pudieron encontrar) datos\.?\*?', '', text, flags=re.IGNORECASE)
    
    # Limpieza estructural
    text = re.sub(r'```(?:json|markdown|md|html)?\s*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```', '', text)
    text = re.sub(r'\{\{.*?\}\}', '', text)
    text = re.sub(r'\s*\[cite:\s*\d+(?:,\s*\d+)*\]', '', text)

    # URLs Placeholder y sucias
    text = re.sub(r'\[([^\]]+)\]\(https://vertexaisearch\.cloud\.google\.com[^)]*\)', r'**\1**', text)
    text = re.sub(r'\[https://vertexaisearch\.cloud\.google\.com[^\]]*\]', '', text)
    text = re.sub(r'\(https://vertexaisearch\.cloud\.google\.com[^)]*\)', '', text)
    text = re.sub(r'https://vertexaisearch\.cloud\.google\.com\S*', '', text)
    text = re.sub(r'\[([^\]]+)\]\(https?://(?:scholar\.)?google\.com/search[^)]*\)', r'**\1**', text)
    text = re.sub(r'\[([^\]]+)\]\(\s*\)', r'\1', text)
    
    # Textos ancla falsos
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: m.group(0) if m.group(2).startswith(('http', '/', '#')) else m.group(1), text)
    text = re.sub(r'\[([^\]]{3,80})\](?!\()', r'**\1**', text)

    # Convertir redundantes H1
    text = remove_redundant_h1(text)
    
    # Pulido final de espacios vacíos
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Llamar extracción explícita (si había json-ld, protegerlo)
    text = extract_json_ld(text)
    
    # Resolver enlaces opacos de Google News a Deep Links reales
    text = resolve_google_news_links(text)
    
    # Corregir jerarquía de FAQs (H3 sin H2 padre)
    text = fix_faq_heading_hierarchy(text)
    
    # Validar enlaces como última capa
    text = validate_links(text)
    
    return text.strip()

def validate_links(text: str) -> str:
    """Escudo Anti-404 para verificar la solidez de los outbound links."""
    try:
        import requests as req_lib
    except ImportError:
        return text

    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    links = link_pattern.findall(text)

    if not links:
        return text

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for anchor, url in links:
        domain = urlparse(url).netloc.replace('www.', '')
        if any(trusted in domain for trusted in TRUSTED_DOMAINS):
            continue
        try:
            r = req_lib.head(url, timeout=12, headers=headers, allow_redirects=True)
            if r.status_code >= 400:
                r2 = req_lib.get(url, timeout=12, headers=headers, allow_redirects=True, stream=True)
                if r2.status_code >= 400:
                    text = text.replace(f'[{anchor}]({url})', f'**{anchor}**')
        except req_lib.exceptions.Timeout:
            pass
        except Exception:
            text = text.replace(f'[{anchor}]({url})', f'**{anchor}**')

    return text

def sanitize_description(raw_text: str, contenido_fallback: str = "") -> str:
    """Genera descripciones metatags estrictamente cortadas para SEO (155 char)."""
    if not raw_text or len(raw_text.strip()) < 20:
        raw_text = re.sub(r'[#*\[\]]', '', contenido_fallback)[:154].replace('\n', ' ').replace('"', "'").strip() + "."
    clean = raw_text.replace('"', "'").strip()
    if len(clean) > 155:
        clean = clean[:155].rsplit(' ', 1)[0] + '.'
    elif not clean.endswith('.'):
        clean += '.'
    return clean
