"""
niche_registry.py — Base de Datos de Configuración de Verticales (Módulo extraído de main.py)

Contiene el diccionario NICHES con la configuración de cada vertical del autoblogger,
las plantillas de estructura narrativa, y utilidades de consulta.
"""
from prompts_factory import (
    PROMPT_PERSONA_ES, PROMPT_PERSONA_EN,
    PROMPT_FITNESS_ES, PROMPT_FITNESS_EN,
    PROMPT_CRYPTO_ES,  PROMPT_CRYPTO_EN,
    PROMPT_YOUTUBE_ES, PROMPT_YOUTUBE_EN,
    PROMPT_VIRAL_ES,   PROMPT_VIRAL_EN,
    PROMPT_TOOLS_ES,   PROMPT_TOOLS_EN,
    PROMPT_FUNDS_ES,   PROMPT_FUNDS_EN,
    PROMPT_REALESTATE_ES, PROMPT_REALESTATE_EN,
)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE NICHOS (SILOS TEMÁTICOS Y EXPERTOS E-E-A-T)
# ═══════════════════════════════════════════════════════════════════

NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "silo": "Tecnologia/IA-SaaS",
        "author_es": "Alex Morgan (Arquitecto de Sistemas & IA)",
        "author_en": "Alex Morgan (Systems & AI Architect)",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news GPT Claude Gemini pricing enterprise adoption",
        "prompt_es": PROMPT_PERSONA_ES,
        "prompt_en": PROMPT_PERSONA_EN
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "silo": "Tecnologia/Salud-Digital",
        "author_es": "Dra. Carmen Izquierdo (Fisióloga y Longevidad)",
        "author_en": "Dr. Carmen Izquierdo (Physiologist & Longevity Researcher)",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed exercise physiology VO2max running economy strength training cardio zone 2 creatine protein synthesis",
        "prompt_es": PROMPT_FITNESS_ES,
        "prompt_en": PROMPT_FITNESS_EN
    },
    "crypto": {
        "name": "Crypto & Web3",
        "silo": "Finanzas/Cripto",
        "author_es": "Dr. Marc Valls (Analista On-Chain & DeFi)",
        "author_en": "Dr. Marc Valls (On-Chain & DeFi Analyst)",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency on-chain analysis DeFi TVL tokenomics whale movements Ethereum Solana Layer2 SEC regulation staking yield",
        "prompt_es": PROMPT_CRYPTO_ES,
        "prompt_en": PROMPT_CRYPTO_EN
    },
    "youtube": {
        "name": "Creator Economy",
        "silo": "Cultura-Digital/Creadores",
        "author_es": "Mateo Benítez (Analista de Economía Creadora)",
        "author_en": "Mateo Benitez (Creator Economy Analyst)",
        "output_dir": "content/youtube",
        "search_context": "YouTube creator drama controversy trending viral TikTok challenge reaction streamer news polemic scandal",
        "prompt_es": PROMPT_YOUTUBE_ES,
        "prompt_en": PROMPT_YOUTUBE_EN
    },
    "viral": {
        "name": "Viral & Trends",
        "silo": "Cultura-Digital/Tendencias",
        "author_es": "Dra. Sofía Alarcón (Socióloga Digital)",
        "author_en": "Dr. Sofia Alarcon (Digital Sociologist)",
        "output_dir": "content/viral",
        "search_context": "viral trends tiktok algorithm Gen Z culture digital sociology consumer behavior Google Trends Pew Research meme culture social media metrics",
        "prompt_es": PROMPT_VIRAL_ES,
        "prompt_en": PROMPT_VIRAL_EN
    },
    "tools": {
        "name": "Tools & Productivity",
        "silo": "Tecnologia/Productividad",
        "author_es": "David K. Miller (Especialista en Automatización)",
        "author_en": "David K. Miller (Automation Specialist)",
        "output_dir": "content/tools",
        "search_context": "productivity tools software review automation zapier notion obsidian personal knowledge management workflow optimization",
        "prompt_es": PROMPT_TOOLS_ES,
        "prompt_en": PROMPT_TOOLS_EN
    },
    "funds": {
        "name": "Economy & Funds",
        "silo": "Finanzas/Fondos",
        "author_es": "Elena Rostova (Estratega Macro y Fondos)",
        "author_en": "Elena Rostova (Macro & Fund Strategist)",
        "output_dir": "content/funds",
        "search_context": "Morningstar fund awards 2026 BlackRock Vanguard mutual fund redemptions equity yield macroeconomics S&P 500 ETF vs mutual funds portfolio management Bloomberg Reuters finance news",
        "prompt_es": PROMPT_FUNDS_ES,
        "prompt_en": PROMPT_FUNDS_EN
    },
    "realestate": {
        "name": "Real Estate",
        "silo": "Inmobiliario/Mercado",
        "author_es": "Carlos De la Fuente (Analista Inmobiliario)",
        "author_en": "Carlos De la Fuente (Real Estate Analyst)",
        "output_dir": "content/realestate",
        "search_context": "FRED 30-year mortgage rates FHFA house price index INE compraventa vivienda transmisiones euribor diario market analysis property yield rent vs buy",
        "prompt_es": PROMPT_REALESTATE_ES,
        "prompt_en": PROMPT_REALESTATE_EN
    }
}

# ═══════════════════════════════════════════════════════════════════
# PLANTILLAS DE ESTRUCTURA NARRATIVA
# ═══════════════════════════════════════════════════════════════════

STRUCTURE_TEMPLATES = {
    'type_a': "INVESTIGATIVE JOURNALISM: Strong Opening Hook -> H2 Context & Background -> H2 Deep Analysis with Data -> H2 Expert Perspectives -> Final Editorial Take",
    'type_b': "NARRATIVE ESSAY: Personal Anecdote or Provocation -> The Core Problem (with numbers) -> Historical Parallel or Case Study -> Contrarian View -> Author's Verdict",
    'type_c': "DATA-DRIVEN REPORT: Striking Statistic Opening -> H2 The Numbers (tables/comparisons) -> H2 What It Means (analysis) -> H2 What Comes Next (prediction)",
    'type_d': "DEBATE FORMAT: Thesis Statement -> H2 The Case For -> H2 The Case Against -> H2 The Uncomfortable Truth -> Short Closing Provocation"
}


def get_niche_config(niche_key: str) -> dict:
    """Devuelve la configuración completa de un nicho, o None si no existe."""
    return NICHES.get(niche_key)


def get_silo(niche_key: str) -> str:
    """Devuelve la categoría de silo temático jerárquico para un nicho."""
    cfg = NICHES.get(niche_key, {})
    return cfg.get("silo", f"General/{niche_key.capitalize()}")


def get_author(niche_key: str, lang: str = "es") -> str:
    """Devuelve el perfil de experto E-E-A-T según el silo temático e idioma."""
    cfg = NICHES.get(niche_key, {})
    key = "author_es" if lang == "es" else "author_en"
    return cfg.get(key, "NovumWorld Editorial Team")


def list_niche_keys() -> list:
    """Devuelve la lista de claves de nichos disponibles."""
    return list(NICHES.keys())

