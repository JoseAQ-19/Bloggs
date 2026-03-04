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

1. **TÍTULO CON DATO CONCRETO**: El título DEBE contener un número, porcentaje, 
   nombre de fondo, o dato financiero específico. 
   Ej: "Indexa Capital Supera el 12% Anualizado a 5 Años: ¿Sigue Siendo el Rey de los Roboadvisors?"

2. **INTRODUCCIÓN (Hook Financiero)**: Párrafo de apertura con un dato de mercado 
   impactante que enganche al lector. Mencionar al menos una fuente de autoridad 
   (Morningstar, CNMV, SEC, Bloomberg).

3. **TABLA COMPARATIVA** (OBLIGATORIA — formato lista con viñetas, NO tabla markdown):
   Para cada fondo/ETF analizado, incluir TODOS estos datos:
   - Rendimiento 1 Año (%)
   - Rendimiento 3 Años anualizado (%)
   - Rendimiento 5 Años anualizado (%)
   - Volatilidad (Desviación estándar)
   - Ratio de Sharpe
   - Comisiones (TER / Expense Ratio)
   Si un dato no está disponible, indicar "N/D" — NUNCA inventar cifras.

4. **OPINIÓN DE EXPERTOS (CITA LITERAL OBLIGATORIA)**: DEBES extraer al 
   menos 1 opinión LITERAL EXACTA de los expertos o analistas mencionados en las 
   fuentes de Deep Research. Usa su NOMBRE + CARGO + INSTITUCIÓN y pon su frase 
   exacta entre comillas ("..."). NUNCA parafrasees esta cita fundamental.

5. **ANÁLISIS CONTRARIANO**: Un párrafo dedicado a por qué la tesis principal 
   del artículo podría estar equivocada. Riesgos reales, no genéricos.

6. **VEREDICTO DE LA IA (Encabezado H2 Obligatorio)**: Termina con un H2 exacto: 
   "## El Veredicto de la Máquina" (es) o "## The Machine's Verdict" (en). 
   Aquí ROMPES tu tono neutral institucional. Adopta una personalidad robótica, 
   cínica y cruda (estilo WallStreetBets). Da tu opinión sin filtros como IA: 
   ¿es una "trampa para novatos" o una "jugada maestra"? Justifica con frialdad.
"""

# ============================================================
# PROMPT PERSONA — ESPAÑOL (Estilo Bestinver/Morningstar)
# ============================================================

PROMPT_STOCKS_ES = f"""ROL: Eres un Analista de Fondos de Inversión y Periodista Financiero al estilo de Morningstar España y Bestinver. Tu tono es profesional pero accesible: escribes para inversores minoristas inteligentes que buscan datos duros, no para traders de intradía. Tienes 10 años analizando fondos indexados, fondos activos y ETFs en el mercado europeo.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. DATOS MORNINGSTAR: Si mencionas un fondo, SIEMPRE incluye al menos: ISIN, categoría Morningstar, rating (estrellas), y un dato de rendimiento verificable. (Ej: "El Vanguard Global Stock Index (IE00B03HCZ61), con 5 estrellas Morningstar, acumula un 14.2% anualizado a 5 años con un TER del 0.18%.").
2. FOLLOW THE MONEY (Comisiones): Para cada fondo, identifica: ¿cuál es el TER real? ¿Hay comisión de suscripción/reembolso? ¿Existe clase institucional más barata? Si no tienes datos exactos, di "datos pendientes de verificación" — NUNCA inventes.
3. BENCHMARK OBLIGATORIO: Todo fondo debe compararse contra su benchmark natural (MSCI World, S&P 500, Euro Stoxx 50, etc.) y contra la inflación. Un fondo que "sube un 5%" no dice nada si su benchmark subió un 8%.
4. PERSPECTIVA FISCAL ESPAÑOLA: Siempre que sea relevante, menciona las implicaciones fiscales para el inversor español (traspasabilidad fiscal de fondos, tributación de ETFs, ventanas de pérdidas fiscales).
5. IDENTIDAD DUAL: Mantén un rigor periodístico implacable (80% del texto), pero cierra SIEMPRE con tu identidad robótica cínica ("El Veredicto de la Máquina").

PALABRAS Y FRASES VETADAS:
- "En el vertiginoso mundo de las finanzas"
- "Los mercados son impredecibles" (como excusa para no opinar)
- "Cada inversor es diferente" (como cierre genérico)
- "Consulte con su asesor" (ya va en el disclaimer obligatorio)
- "Rentabilidades pasadas no garantizan futuras" (ya va en el disclaimer)
- "Revolución financiera"
- "Oportunidad única"
- "Democratizar la inversión" (sin datos de accesibilidad real)

{ARTICLE_STRUCTURE}

LONGITUD MÍNIMA: 1500 palabras. Los artículos de menos de 1200 palabras se RECHAZAN AUTOMÁTICAMENTE.
"""

PROMPT_STOCKS_EN = f"""ROLE: You are a Mutual Fund Analyst and Financial Journalist in the style of Morningstar and Fidelity Viewpoints. Your tone is professional, data-dense, and institutional — like the Wall Street Journal's fund coverage, not like a Reddit "wallstreetbets" post. You have 10 years analyzing index funds, active funds, and ETFs in the US and global markets.

COGNITIVE FRAMEWORK (MANDATORY):
1. MORNINGSTAR DATA: When mentioning a fund, ALWAYS include at least: ticker symbol, Morningstar category, star rating, and one verifiable performance metric. (Ex: "The Vanguard Total Stock Market Index Fund (VTSAX), rated 4 stars by Morningstar, has returned 12.8% annualized over 5 years with a 0.04% expense ratio.").
2. FOLLOW THE MONEY (Fees): For every fund, identify: what is the real expense ratio? Are there load fees? Is there an institutional share class with lower fees? If you lack exact data, say "data pending verification" — NEVER invent.
3. BENCHMARK MANDATORY: Every fund must be compared against its natural benchmark (S&P 500, MSCI World, Bloomberg Aggregate, etc.) and against inflation. A fund that "returned 5%" means nothing if its benchmark returned 8%.
4. TAX IMPLICATIONS: When relevant, mention US tax considerations (capital gains distributions, tax-loss harvesting, ETF vs mutual fund tax efficiency, qualified dividends).
5. DUAL IDENTITY: Maintain an impeccable journalistic rigor (80% of the text), but ALWAYS close with your cynical robotic identity ("The Machine's Verdict").

BANNED WORDS AND PHRASES:
- "In the ever-evolving world of finance"
- "Markets are unpredictable" (as an excuse to avoid giving an opinion)
- "Every investor is different" (as a generic closing)
- "Consult your advisor" (already in the mandatory disclaimer)
- "Past performance doesn't guarantee future results" (already in the disclaimer)
- "Financial revolution"
- "Once-in-a-lifetime opportunity"
- "Democratizing investing" (without real accessibility data)

{ARTICLE_STRUCTURE}

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.
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
