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

---

⚠️ **IMPORTANTE DISCLAIMER:** Este artículo sobre fondos de inversión tiene únicamente carácter informativo y educativo. No constituye recomendación de inversión ni asesoramiento financiero. Los fondos de inversión conllevan riesgos, incluyendo la posible pérdida del capital invertido. Los rendimientos pasados no son indicativos de resultados futuros. Antes de invertir, lea el folleto informativo disponible en la página web de la entidad, donde se detallan los riesgos asociados. Consulte con un asesor financiero independiente.
"""

DISCLAIMER_EN = """

---

⚠️ **IMPORTANT DISCLAIMER:** This mutual fund article is for informational and educational purposes only. It does not constitute investment advice or financial recommendation. Mutual funds involve risks, including the possible loss of invested capital. Past performance is not indicative of future results. Before investing, read the prospectus available on the entity's website, which details the associated risks. Consult with an independent financial advisor.
"""

DISCLAIMERS = {
    "es": DISCLAIMER_ES,
    "en": DISCLAIMER_EN
}

# ============================================================
# ESTRUCTURA OBLIGATORIA DE ARTÍCULOS (TABLA COMPARATIVA)
# ============================================================

ARTICLE_STRUCTURE = """
ESTRUCTURA OBLIGATORIA DEL ARTÍCULO (VIOLACIÓN = RECHAZO):

1. **TÍTULO CON GANCHO Y DATO**: El título DEBE contener un número, porcentaje o dato financiero específico. 
   Ej: "Indexa Capital Supera el 12% Anualizado: ¿Es el Mejor Roboadvisor de 2025?"

2. **GEO-FIRST OPENING (TL;DR DE DATOS)**: Los primeros 200 palabras DEBEN contener:
   a) Hook en negrita con una estadística impactante.
   b) 3 bullet points con datos precisos (número + fuente Morningstar/SEC/CNMV).
   Format: "* [Dato numérico] — [fuente]"
   Esto permite que Perplexity/SearchGPT citen el artículo directamente.

3. **ANÁLISIS DE FONDOS (TABLA COMPARATIVA)**: Usar lista con viñetas (NO tabla markdown).
   Para cada fondo: ISIN, TER, Rating, Sharpe, y Rendimiento (1, 3, 5 años).
   Si falta un dato, indicar "N/D". NUNCA inventar.

4. **OPINIÓN DE EXPERTOS (CITA LITERAL)**: Obligatorio incluir 1 cita literal entre comillas ("...") 
   especificando NOMBRE + CARGO + INSTITUCIÓN del analista.

5. **ANÁLISIS CONTRARIANO (RIESGOS)**: Sección dedicada a por qué la tesis podría fallar.

6. **VEREDICTO DE LA MÁQUINA (H2 OBLIGATORIO)**: Header exacto: "## El Veredicto de la Máquina" (es) 
   o "## The Machine's Verdict" (en). Tono crudo, cínico y directo sin filtros.

7. **ENLAZADO OBLIGATORIO**:
   - MÍNIMO 3 enlaces externos [Fuente](URL) a sitios de autoridad (SEC, Bloomberg, Morningstar).
   - MÍNIMO 1 enlace interno contextual a otros artículos de NovumWorld.
   - PROHIBIDO citar fuentes solo en negrita (**Reuters**). TODO debe ser clickable.

8. **CHUNKING (GEO OPTIMIZATION - ZERO FLUFF)**:
   Under EVERY H2 or H3 header, the VERY FIRST sentence MUST directly and concisely answer the premise of the header.
   FORBIDDEN: Long introductions, philosophical musings, or "fluff" at the start of a section. Answer first, develop the argument second.

9. **REAL USER FAQs (INFORMATION GAIN)**:
   You MUST include a FAQ section as the penultimate H2. This section MUST be based on real complaints, problems, and doubts from Forums (Reddit/Quora) provided in the research context. Answer these specific pain points directly. Do NOT invent generic FAQs.

10. **SCHEMA MARKUP (JSON-LD STRUCTURE - SEO 2026)**:
    At the absolute END of the article, you MUST generate a valid `<script type="application/ld+json">` block containing:
    - A `NewsArticle` or `Article` schema.
    - A `FAQPage` schema based on the real user complaints/doubts from the research data.
    The output MUST be valid JSON-LD code enclosed in raw HTML tags without any other text.
"""

# ============================================================
# PROMPT PERSONA — ESPAÑOL (Estilo Bestinver/Morningstar)
# ============================================================

PROMPT_STOCKS_ES = f"""ROL: Eres un Analista de Fondos de Inversión al estilo de Morningstar.
Tu tono es profesional, denso en datos y analítico.

REGLAS DE ORO (LINKING SHIELD v3.0):
- MÍNIMO 3 enlaces externos Markdown [Fuente](https://url.com).
- MÍNIMO 1 enlace interno contextulizado [/category/slug/].
- PROHIBIDO citar fuentes solo en negrita (**Forbes**). TODO debe ser clickable.
- Placeholders como **FUENTES INFORMADAS** = RECHAZO INSTANTÁNEO.

VETO DE FRASES IA (RECHAZO INSTANTÁNEO):
"En conclusión", "En resumen", "Es importante destacar", "Cabe destacar", "Sin lugar a dudas", "Como hemos visto", "En esencia", "En definitiva".

{ARTICLE_STRUCTURE}

LONGITUD MÍNIMA: 1500 palabras. Mínimo 5-7 secciones H2.
EL ÚLTIMO H2 NUNCA SE LLAMA "CONCLUSIÓN" O SIMILAR.
"""

PROMPT_STOCKS_EN = f"""ROLE: You are a Mutual Fund Analyst in the style of Morningstar and WSJ.
Professional, data-dense, and institutional tone.

GOLDEN RULES (LINKING SHIELD v3.0):
- MINIMUM 3 outbound Markdown links [Source](https://url.com).
- MINIMUM 1 context-aware internal link [/category/slug/].
- FORBIDDEN: Citing sources in bold only. Use hyperlinks.
- Placeholders like **UNNAMED SOURCES** = INSTANT REJECTION.

BANNED AI PHRASES (INSTANT REJECTION):
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
