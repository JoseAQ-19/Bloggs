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
)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE NICHOS
# ═══════════════════════════════════════════════════════════════════

NICHES = {
    "ia": {
        "name": "IA & SaaS",
        "output_dir": "content/ia",
        "search_context": "SaaS AI tools LLM benchmarks B2B technology news GPT Claude Gemini pricing enterprise adoption",
        "prompt_es": PROMPT_PERSONA_ES,
        "prompt_en": PROMPT_PERSONA_EN
    },
    "fitness": {
        "name": "Biohacking & Fitness",
        "output_dir": "content/fitness",
        "search_context": "hypertrophy science biohacking longevity pubmed exercise physiology VO2max running economy strength training cardio zone 2 creatine protein synthesis",
        "prompt_es": PROMPT_FITNESS_ES,
        "prompt_en": PROMPT_FITNESS_EN
    },
    "crypto": {
        "name": "Crypto & Web3",
        "output_dir": "content/crypto",
        "search_context": "cryptocurrency on-chain analysis DeFi TVL tokenomics whale movements Ethereum Solana Layer2 SEC regulation staking yield",
        "prompt_es": PROMPT_CRYPTO_ES,
        "prompt_en": PROMPT_CRYPTO_EN
    },
    "youtube": {
        "name": "Creator Economy",
        "output_dir": "content/youtube",
        "search_context": "YouTube creator drama controversy trending viral TikTok challenge reaction streamer news polemic scandal",
        "prompt_es": PROMPT_YOUTUBE_ES,
        "prompt_en": PROMPT_YOUTUBE_EN
    },
    "viral": {
        "name": "Viral & Trends",
        "output_dir": "content/viral",
        "search_context": "viral trends tiktok algorithm Gen Z culture digital sociology consumer behavior Google Trends Pew Research meme culture social media metrics",
        "prompt_es": PROMPT_VIRAL_ES,
        "prompt_en": PROMPT_VIRAL_EN
    },
    "tools": {
        "name": "Novum Tools",
        "output_dir": "content/tools",
        "search_context": "tutorial guide automation workflow no-code",
        "prompt_es": PROMPT_TOOLS_ES,
        "prompt_en": PROMPT_TOOLS_EN
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


def list_niche_keys() -> list:
    """Devuelve la lista de claves de nichos disponibles."""
    return list(NICHES.keys())
