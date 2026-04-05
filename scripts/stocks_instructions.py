#!/usr/bin/env python3
"""
STOCKS_INSTRUCTIONS.PY — Cerebro de Configuración para el Módulo Funds/Stocks
==============================================================================
Define tonos, estructura obligatoria, disclaimers legales y reglas de formato
para artículos de fondos de inversión en ES y EN.

REGLA DE ORO: Este archivo NO importa ni modifica NADA del núcleo existente.
"""

# ============================================================
# DISCLAIMERS LEGALES OBLIGATORIOS (INYECCIÓN FORZADA)
# Se concatenan al final del artículo pase lo que pase.
# ============================================================

DISCLAIMER_ES = """
*Aviso YMYL: La información de este artículo es educativa y no constituye asesoramiento profesional. Consulte a un especialista antes de tomar decisiones financieras o de salud.*
"""

DISCLAIMER_EN = """
*YMYL Disclaimer: This article is for informational purposes only and does not constitute professional advice. Always consult a certified specialist before making financial or health-related decisions.*
"""

DISCLAIMERS = {
    "es": DISCLAIMER_ES,
    "en": DISCLAIMER_EN
}

# ============================================================
# ESTRUCTURA OBLIGATORIA DE ARTÍCULOS (15 REGLAS DE ORO)
# ============================================================

ARTICLE_STRUCTURE = """
### CRITICAL FORMATTING RULES (PLEASE FOLLOW STRICTLY):

1. NO TITLE REPETITION: Do NOT include the article title or H1 at the beginning.
2. GEO-FIRST OPENING (MANDATORY): The first 200 words MUST contain:
   a) A bold hook sentence with a specific number/statistic/percentage.
   b) 3 bullet points with precise financial data (number + metric + source).
   Format: "* [Stat with number] — [source Morningstar/SEC/CNMV]"
   Then continue with narrative prose. START IMMEDIATELY with the hook. No filler.
3. FORBIDDEN PHRASES (PLEASE AVOID THESE STRINGENTLY):
   - English: "TL;DR", "Key Takeaways", "In summary", "In conclusion", "It remains to be seen", "The Bottom Line", "Final Thoughts", "unlock your potential", "world of possibilities"
   - Spanish: "En resumen", "En conclusión", "En última instancia", "Cabe destacar", "Un arma de doble filo", "Queda por ver", "desbloquea tu potencial", "un mundo de posibilidades"
   - NEVER start your response with 'Here is the article' or 'Sure!'. START IMMEDIATELY.
4. HEADERS HIERARCHY (SEO OPTIMIZATION): Use H2 (##) for main sections and H3 (###) for sub-sections. NEVER use H1 (#). Logical hierarchy (H2 -> H3 -> H2) is mandatory. The primary keyword/fund name MUST appear in at least 1 H2.
5. STRICT URL POLICY (OUTBOUND + INTERNAL LINKS):
   - You are STRICTLY FORBIDDEN from inventing, guessing, or fabricating ANY URL.
   - You may ONLY use URLs that appear explicitly in the verified-URLs or internal-links blocks injected by the system.
   - If there are ZERO verified URLs for this article, you MUST write the ENTIRE article body WITHOUT external hyperlinks. Python will inject a Methodology/Sources section later.
   - When you DO have verified URLs, convert them into Markdown links using the exact pattern [Source Name](https://exact-url.com), copy-pasting the URL VERBATIM.
   - If you want to cite a source that has NO URL in those blocks, mention ONLY the source/entity name in plain text or **bold**, but DO NOT add a URL.
   - ⚠️ SECURITY RULE: Inventing even a SINGLE URL that was not provided by the system is a CRITICAL SECURITY FAILURE.
5bis. RESERVED FOOTER SECTIONS (PYTHON-ONLY):
   - You MUST NOT write any sections titled "Metodología y Fuentes", "Methodology and Sources", "Artículos relacionados", "Related Articles", nor any generic "Fuentes"/"Sources" blocks at the end of the article.
   - Your job ALWAYS ends before those sections. The Python pipeline will inject the official "Metodología y Fuentes" + "Artículos relacionados" footer (and disclaimers) deterministically after your content.
6. UNIQUE DATA POINT (MANDATORY — MINIMUM 1):
   Include at least ONE original comparative calculation or fee analysis (e.g., TER vs Performance impact).
7. PARAGRAPH LENGTH VARIATION (MANDATORY):
   Paragraphs MUST vary between 1 and 6 sentences. Include at least one single-sentence paragraph for drama.
8. MANDATORY 5-7 SECTION STRUCTURE (H2 with H3 sub-headers):
   Every article MUST have 5-7 main sections. penúltimo H2 debe ser "Real User FAQs".
9. NO BULLET LISTS SPAM AND NO TABLES ALLOWED:
   Maximum ONE bulleted list per article (the GEO opening bullets). ABSOLUTE PROHIBITION ON TABLES. Use narrative prose with bulleted highlights for fund data.
10. E-E-A-T EXPERT CITATION (MANDATORY):
    Cite at least 2 named experts (full name + title + institution) in the article.
    Include at least 5 numeric data points with sources. At least ONE link MUST point to a primary authority (.gov, .edu, SEC, CNMV) IF such a URL is provided.
11. LANGUAGE PURITY:
    If writing in Spanish, ALL text must be in Spanish. No Spanglish.
12. LAST SECTION RULE: The final H2 NEVER uses 'Conclusion'. Use action-oriented headers like 'Our Verdict' or 'Investment Strategy'. CRITICAL: NEVER use 'The Machine's Verdict' — always write in first-person plural ("we believe", "our analysis shows").
13. CHUNKING (GEO OPTIMIZATION - ZERO FLUFF):
    Under EVERY H2 or H3 header, the VERY FIRST sentence MUST directly and concisely answer the premise of the header. No introductions.
14. SCHEMA MARKUP (JSON-LD STRUCTURE - SEO 2026):
    At the absolute END of the article, you MUST generate a valid `<script type="application/ld+json">` block containing NewsArticle and FAQPage schema.
15. REAL USER FAQs (INFORMATION GAIN):
    You MUST include a FAQ section as the penultimate H2 based on real investor complaints/doubts from Forums/Reddit.
"""

# ============================================================
# PROMPT PERSONA — ESPAÑOL (Estilo Bestinver/Morningstar)
# ============================================================

PROMPT_STOCKS_ES = f"""ROL: Eres un Analista de Fondos de Inversión al estilo de Morningstar.
Tu tono es profesional, denso en datos y analítico.

REGLAS DE ORO (LINKING SHIELD v3.1 — POLÍTICA ESTRICTA DE URLS):
- PROHIBIDO inventar, adivinar o fabricar URLs externas o internas.
- Solo puedes usar como hipervínculos las URLs explícitas que te proporciona el sistema.
- Si no hay URLs verificadas para este artículo, escribe TODO el cuerpo SIN enlaces externos; Python añadirá la sección de Metodología/Fuentes al final.

VETO DE FRASES IA (POR FAVOR EVITAR):
"En conclusión", "En resumen", "Es importante destacar", "Cabe destacar", "Sin lugar a dudas", "Como hemos visto", "En esencia", "En definitiva".

{ARTICLE_STRUCTURE}

LONGITUD MÍNIMA: 1500 palabras. Mínimo 5-7 secciones H2.
EL ÚLTIMO H2 NUNCA SE LLAMA "CONCLUSIÓN" O SIMILAR.
"""

PROMPT_STOCKS_EN = f"""ROLE: You are a Mutual Fund Analyst in the style of Morningstar and WSJ.
Professional, data-dense, and institutional tone.

GOLDEN RULES (LINKING SHIELD v3.1 — STRICT URL POLICY):
- You are STRICTLY FORBIDDEN from inventing or guessing ANY external or internal URL.
- You may ONLY create hyperlinks from the explicit URLs provided by the system.
- If there are no verified URLs for this article, you MUST write the entire body with ZERO external links; Python will inject Methodology/Sources later.

BANNED AI PHRASES (PLEASE AVOID STRICTLY):
"In conclusion", "In summary", "TL;DR", "Key Takeaways", "The Bottom Line", "Final Thoughts", "As we have seen", "Without a doubt", "It goes without saying".

{ARTICLE_STRUCTURE}

MINIMUM LENGTH: 1500 words. Minimum 5-7 H2 sections.
THE LAST H2 NEVER USES "CONCLUSION" OR SIMILAR GENERIC HEADERS.
"""

# ============================================================
# PROMPTS COMPACTADOS POR IDIOMA (Para fácil acceso)
# ============================================================

PROMPTS = {
    "es": PROMPT_STOCKS_ES,
    "en": PROMPT_STOCKS_EN
}

# ============================================================
# COMPETIDORES TARGET (Para análisis de escritura)
# ============================================================

COMPETITORS = {
    "es": {
        "morningstar_es": {
            "name": "Morningstar España",
            "url": "https://www.morningstar.es",
            "rss": "https://www.morningstar.es/es/news/rss.aspx",
            "style": "Institucional, datos Morningstar, rating con estrellas, tablas de rendimiento"
        },
        "bestinver": {
            "name": "Bestinver",
            "url": "https://www.bestinver.com",
            "rss": None,
            "style": "Value investing, cartas trimestrales a partícipes, tono serio y conservador"
        },
        "carmignac_es": {
            "name": "Carmignac España",
            "url": "https://www.carmignac.es",
            "rss": None,
            "style": "Análisis macro, perspectivas de mercado, tono europeo sofisticado"
        },
        "vanguard_es": {
            "name": "Vanguard Investor España",
            "url": "https://www.es.vanguard",
            "rss": None,
            "style": "Gestión pasiva, indexación, enfoque de largo plazo, educación financiera"
        }
    },
    "en": {
        "morningstar_com": {
            "name": "Morningstar",
            "url": "https://www.morningstar.com",
            "rss": "https://www.morningstar.com/feeds/rss",
            "style": "Institutional analysis, star ratings, fund comparisons, data-heavy"
        },
        "fidelity": {
            "name": "Fidelity Investments",
            "url": "https://www.fidelity.com",
            "rss": None,
            "style": "Investor education, viewpoints articles, balanced professional tone"
        },
        "vanguard_com": {
            "name": "Vanguard",
            "url": "https://www.vanguard.com",
            "rss": None,
            "style": "Index investing advocacy, long-term focus, cost-conscious language"
        },
        "blackrock": {
            "name": "BlackRock",
            "url": "https://www.blackrock.com",
            "rss": None,
            "style": "Institutional/macro perspective, iShares ETF focus, global outlook"
        }
    }
}

# ============================================================
# CATEGORÍA CONFIG (Compatible con trend_scout format)
# ============================================================

STOCKS_CATEGORY_CONFIG = {
    "funds": {
        "type": "technical",
        "hn_tags": ["investing", "finance", "etf", "index-fund"],
        "news_queries": {
            "es": [
                "fondos inversión España noticias Morningstar",
                "mejores fondos indexados 2025 España",
                "ETF Vanguard iShares análisis rendimiento"
            ],
            "en": [
                "mutual fund news analysis Morningstar",
                "best index funds ETF performance 2025",
                "Vanguard Fidelity BlackRock fund comparison"
            ]
        },
        "exa_domains": [
            "morningstar.com", "morningstar.es",
            "etf.com", "investopedia.com",
            "barrons.com", "ft.com"
        ],
        "seeds": [
            "Vanguard Total Stock Market",
            "iShares Core S&P 500",
            "Fidelity ZERO",
            "Indexa Capital",
            "Amundi MSCI World",
            "Baelo Patrimonio",
            "MyInvestor Cartera Permanente"
        ]
    }
}

# ============================================================
# FORMATO DE FRONTMATTER HUGO
# ============================================================

FRONTMATTER_TEMPLATE = """---
title: "{title}"
date: {date}
draft: false
description: "{description}"
featured_image: "{image}"
tags: ["Funds & Stocks"]
categories: ["funds"]
type: "funds"
language: "{lang}"
translationKey: "{translation_key}"
---

![{title}]({image})

{content}
"""

# ============================================================
# NICHE CONFIG (Para integración con main.py si se desea)
# ============================================================

NICHE_CONFIG = {
    "name": "Funds & Stocks",
    "output_dir_es": "content/es/funds",
    "output_dir_en": "content/en/funds",
    "search_context": "mutual funds ETF index funds Vanguard Fidelity BlackRock Morningstar expense ratio Sharpe ratio portfolio allocation",
    "prompt_es": PROMPT_STOCKS_ES,
    "prompt_en": PROMPT_STOCKS_EN
}
