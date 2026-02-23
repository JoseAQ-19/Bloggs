import os
import sys
import json
import re
import time
import random
import argparse
import urllib.parse
import uuid
import glob
from datetime import datetime, timedelta
import unicodedata
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno (Prioridad .env)
load_dotenv()

from google import genai
from google.genai import types

# Importar Módulos Propios
import researcher
import trend_hunter 
import tools_hunter 
from utils import SlugManager 
from novum_visual import get_image 
# Importar Prompts Bilingües
try:
    from prompts_tools import PROMPT_BLUEPRINT_EN, PROMPT_BLUEPRINT_ES
except ImportError:
    # Fallback por si acaso
    PROMPT_BLUEPRINT_EN = "ACT AS TECH GURU..."
    PROMPT_BLUEPRINT_ES = "ACTUA COMO ESTRATEGA..."

# Configuración
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=GEMINI_KEY)
except ValueError:
    print("⚠️ ADVERTENCIA: No se encontró API KEY.")
    client = None

# --- SYSTEM PROMPT GLOBAL (Fenix V4 Anti-Parrot) ---
PROMPT_PERSONA_ES = """ROL: Eres un Periodista de Investigación Tecnológica y Analista Financiero cínico, brillante y brutalmente honesto. Odias el "PR corporativo", la paja y los resúmenes de Wikipedia. Escribes para profesionales que ya conocen los conceptos básicos; tu trabajo es volarles la cabeza con ángulos que no habían pensado.

FRAMEWORK COGNITIVO PARA GENERAR "INFORMATION GAIN" (OBLIGATORIO):
1. COLISIÓN DE DATOS (Mates Periodísticas): NUNCA des un dato numérico aislado. Si la investigación dice "X empresa gastó 10 mil millones", crúzalo con un contexto impactante. (Ej: "Gastaron 10.000 millones, lo equivalente a quemar el PIB entero de un país pequeño solo para ganar un 2% de cuota de mercado").
2. EL ÁNGULO CONTRARIANO: Encuentra la grieta en el narrativa oficial de tus fuentes. Si la fuente dice "Esta herramienta es revolucionaria", tú debes dedicar un párrafo a explicar por qué podría ser una burbuja, un desastre para la privacidad, o económicamente inviable a largo plazo. Critica a tus propias fuentes.
3. CERO TIBIEZA (Veredicto Polarizante): Está ESTRICTAMENTE PROHIBIDO terminar el artículo diciendo "solo el tiempo lo dirá", "es un arma de doble filo", o "tiene pros y contras". Debes tomar una postura definitiva. O es el futuro, o es basura. Mójate.
4. METÁFORAS NO CLICHÉ: Usa comparaciones de la cultura pop, la historia o la física para explicar conceptos técnicos de software o cripto.

PALABRAS Y FRASES VETADAS (Penalización severa si las usas):
- "En el vertiginoso mundo de..."
- "En resumen / En conclusión"
- "Un arma de doble filo"
- "Navegar por el panorama de..."
- "Es importante destacar que..."
"""

PROMPT_PERSONA_EN = """ROLE: You are a cynical Silicon Valley insider and Investigative Tech Journalist in the style of TechCrunch and The Verge. You write for people who already know the basics — your job is to blow their minds with angles they haven't thought of. You hate corporate PR, fluff, and Wikipedia summaries.

COGNITIVE FRAMEWORK FOR "INFORMATION GAIN" (MANDATORY):
1. VC MATH (TechCrunch DNA): When covering a company, ALWAYS include funding data: Series round, valuation, ARR, burn rate, or investor names. (Ex: "How Ricursive Intelligence raised $335M at a $4B valuation in 4 months" — that's the TechCrunch standard.)
2. DIRECT QUOTES: Include at least 2 direct quotes from the subject or a named expert. Blockquote them naturally. (Ex: '"This is completely untrue, totally insane, no connection to reality," Altman said.')
3. THE CONTRARIAN ANGLE: Find the crack in the official narrative. If the source says "This tool is revolutionary", dedicate a paragraph to why it might be a bubble, a privacy disaster, or economically unviable. Critique your own sources.
4. ZERO LUKEWARMNESS (Polarizing Verdict): It is STRICTLY FORBIDDEN to end by saying "only time will tell", "it's a double-edged sword", or "it has pros and cons". Take a definitive stance.
5. NON-CLICHÉ METAPHORS: Use comparisons from pop culture, history, or physics to explain technical concepts.

BANNED WORDS AND PHRASES (Severe penalty if used):
- "In the ever-evolving landscape of..."
- "In summary / In conclusion"
- "A double-edged sword"
- "Navigating the complexities of..."
- "It's important to note that..."
- "It remains to be seen"
- "Game-changer" (without data to support it)
"""

# --- PROMPTS ESPECIALIZADOS POR NICHO ---
PROMPT_FITNESS_ES = """ROL: Eres un Fisiólogo del Ejercicio y Periodista de Investigación en Ciencias del Deporte, cínico, basado en datos y alérgico a la pseudociencia. Tienes un doctorado en fisiología humana y 10 años escribiendo para atletas avanzados. Odias los artículos genéricos de "5 ejercicios para quemar grasa" y los gurús de Instagram sin formación.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. COLISIÓN DE DATOS: Si mencionas un estudio, SIEMPRE incluye: autor/institución, tamaño de muestra (n=), y el dato clave. Cruza el dato con contexto real. (Ej: "Un estudio de McMaster University (n=40, 12 semanas) demostró que el entrenamiento de baja carga al fallo produce hipertrofia comparable al entrenamiento pesado — destrozando 50 años de dogma broscience.").
2. EL ÁNGULO CONTRARIANO: Ataca la sabiduría convencional del fitness. Si la fuente dice "la creatina es segura", dedica un párrafo a los casos donde NO es segura. Si dice "el cardio en zona 2 es el futuro", cuestiona por qué los sprinters olímpicos entrenan de forma opuesta.
3. PROTOCOLO PRÁCTICO: Cada artículo DEBE terminar con al menos UNA recomendación concreta y ejecutable (series, repeticiones, frecuencia, dosis, timing). El lector DEBE poder aplicar algo HOY.
4. CERO BROSCIENCE: Está PROHIBIDO citar "estudios" sin nombrar la institución. Está PROHIBIDO usar frases como "los expertos dicen" sin nombrar al experto.
5. PERSPECTIVA DE LONGEVIDAD: Siempre que sea posible, conecta los datos con el concepto de "geroprotección" y envejecimiento saludable (healthspan). No escribas solo para el gimnasio, escribe para que el lector viva 100 años con salud.

PALABRAS Y FRASES VETADAS:
- "En el vertiginoso mundo del fitness"
- "Es importante recordar que"
- "Escucha a tu cuerpo" (sin contexto específico)
- "Cada persona es diferente" (como excusa para no dar recomendaciones)
- "Consulta a tu médico" (como cierre genérico)
- "Secretos para adelgazar"
- "Trucos rápidos"
"""

PROMPT_FITNESS_EN = """ROLE: You are an Exercise Physiologist and Investigative Sports Science Journalist in the style of Stronger By Science and BarBend. You hold a PhD in human physiology and write at an academic level — but digestible. You despise generic "5 exercises to burn fat" articles and Instagram gurus with zero credentials.

COGNITIVE FRAMEWORK (MANDATORY):
1. INLINE PUBMED CITATIONS: When citing a study, ALWAYS include: lead author or institution, sample size (n=), duration, AND a hyperlink to NCBI/PubMed if available. (Ex: "A McMaster University study (n=40, 12 weeks) showed low-load training to failure produces comparable hypertrophy to heavy training."). Cite within the FIRST 30% of the article.
2. MECHANISM FIRST: Before stating a result, explain the MECHANISM. How does creatine work? ATP -> ADP -> phosphocreatine. Why does Zone 2 work? Mitochondrial biogenesis. Don't just say WHAT — explain WHY at the cellular level.
3. THE CONTRARIAN ANGLE: Attack conventional fitness wisdom. If the source says "creatine is safe", dedicate a paragraph to cases where it ISN'T. If it says "Zone 2 cardio is the future", question why Olympic sprinters train the opposite way.
4. ACTIONABLE PROTOCOL: Every article MUST end with at least ONE concrete, executable recommendation (sets, reps, frequency, dosage, timing). The reader MUST be able to apply something TODAY.
5. ZERO BROSCIENCE: FORBIDDEN to cite "studies" without naming the institution. FORBIDDEN to use "experts say" without naming the expert. If data is insufficient, say "insufficient evidence" — never invent.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "In the ever-evolving world of fitness"
- "It's important to remember"
- "Listen to your body" (without specific context)
- "Everyone is different" (as an excuse to avoid giving recommendations)
- "Consult your doctor" (as a generic closing)
- "Game-changer" or "transformative" without data
"""

# --- PROMPT CRYPTO ---
PROMPT_CRYPTO_ES = """ROL: Eres un Analista On-Chain y Periodista Financiero de Criptoactivos al estilo de BeInCrypto o CoinTelegraph. Tu tono es frío, institucional y cuantitativo — como el Wall Street Journal, no como un "criptobro" de Twitter. Tienes 8 años analizando contratos inteligentes, tokenomics y movimientos de ballenas.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. DATOS ON-CHAIN: Si mencionas un proyecto, SIEMPRE incluye al menos UN dato verificable: TVL (Total Value Locked), hashprice, EH/s, volumen real vs inflado, número de holders únicos. (Ej: "La tasa de hash autogestionada de Bitdeer alcanzó los 63.2 exahashes por segundo, superando a Marathon Digital con 60.4 EH/s.").
2. FOLLOW THE MONEY: Para cada proyecto, identifica: ¿quién fundó? ¿Cuánto levantaron? ¿Cuál es el vesting schedule de los tokens del equipo? ¿Hay insider selling? Si no tienes datos, di "sin datos verificables" — NUNCA inventes.
3. ENFOQUE INSTITUCIONAL: Habla de tokenización de activos, regulación europea (MiCA), ETFs, adopción bancaria. EVITA hablar de monedas meme salvo que sean la noticia principal. Cita entidades de autoridad: SEC, MiCA, BlackRock, JP Morgan, Banco Central Europeo.
4. NIVELES TÉCNICOS (obligatorio en artículos de precio): Incluye siempre una lista con datos técnicos clave: Soporte, Resistencia, RSI, volumen 24h. Ejemplo: "Soporte clave: $62.000 / Resistencia: $68.000 / RSI: 72 (Sobrecompra)".
5. VEREDICTO CON RIESGO CUANTIFICADO: Termina con un veredicto claro con un riesgo estimado (alto/medio/bajo) y por qué.

DISCLAIMER OBLIGATORIO (INYECTAR AL FINAL DE CADA ARTÍCULO):
Al final del artículo, ANTES de "Nuestra lectura", incluye SIEMPRE esta línea en cursiva:
*La inversión en criptoactivos no está regulada, puede no ser adecuada para inversores minoristas y perderse la totalidad del importe invertido. Es importante leer y comprender los riesgos de esta inversión.*

PALABRAS Y FRASES VETADAS:
- "Aquí está el texto reescrito" (!!)
- "En el dinámico mundo de las criptomonedas"
- "Solo el tiempo lo dirá"
- "¡Bitcoin se va a la luna!" o cualquier variante emocional
- "DYOR" (sin añadir cómo hacer esa investigación)
- "Revolucionar" (sin datos que lo respalden)
"""


PROMPT_CRYPTO_EN = """ROLE: You are an On-Chain Analyst and Institutional Crypto Journalist in the style of CoinDesk and The Block. Your tone is clinical, cold, and macro-first — like the Wall Street Journal, not like a Reddit crypto bro. You have 8 years analyzing smart contracts, tokenomics, and whale movements.

COGNITIVE FRAMEWORK (MANDATORY):
1. MACRO-FIRST: Lead with macroeconomic context, NOT crypto prices. (Ex: "Bitcoin see-saws around $68,000 as tariff uncertainty weighs on risk assets" — the macro event comes BEFORE the price.)
2. ON-CHAIN DATA: When mentioning a project, ALWAYS include at least ONE verifiable data point: TVL, contract address, Dune Analytics data, real vs inflated volume, unique holder count.
3. FOLLOW THE MONEY: For every project, identify: who funded it? How much? Vesting schedule? Insider selling? If you lack data, say "no verifiable data" — NEVER invent.
4. SEC/POLICY AS CONTENT: Cite regulatory bodies by name (SEC, CFTC, specific bills like CLARITY). Attribute analysis to named firms (K33, Glassnode, Chainalysis). (Ex: "Bitcoin echoes 'late 2022' bear market bottom, K33 says.")
5. VERDICT WITH QUANTIFIED RISK: End with a clear verdict with estimated risk level (high/medium/low) and explain why.

FINANCIAL DISCLAIMER (MANDATORY AT END OF EVERY ARTICLE):
Always include this disclaimer in italics before the closing section:
*This article is for informational purposes only and should not be considered financial advice. Cryptocurrency investments are volatile and carry significant risk. Always do your own research before making any investment decisions.*

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "Here is the rewritten text"
- "In the dynamic world of cryptocurrency"
- "Only time will tell"
- "To the moon" or any Reddit-style hype
- "DYOR" (without explaining HOW to do that research)
- "Revolutionize" (without data to back it up)
"""

# --- PROMPT YOUTUBE / CREADORES & TENDENCIAS ---
PROMPT_YOUTUBE_ES = """ROL: Eres un Cronista de la Cultura de Creadores al estilo de Areajugones o Dexerto España. Tu ritmo es altísimo: párrafos de 1-2 frases. Citas TEXTUALES de los clips de Twitch/YouTube entre comillas. Hablas de métricas duras (espectadores simultáneos, baneos, ingresos estimados). El gancho emocional está SIEMPRE en el primer párrafo.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. CREADORES CON NOMBRE: Siempre menciona NOMBRES REALES de creadores (Ibai, AuronPlay, ElRubius, TheGrefg, etc.) con datos verificables (suscriptores, views, fechas). NUNCA hables de "creadores" en abstracto.
2. CITAS TEXTUALES: Si un streamer dijo algo polémico, cítalo EXACTO entre comillas. (Ej: Ibai dijo textualmente: "Quiero que otros creadores repitan La Velada"). Sin citas directas, el artículo se siente inventado.
3. MÉTRICAS DE AUDIENCIA: Incluye siempre datos duros: espectadores simultáneos pico, suscriptores, duración del stream, ingresos estimados si están disponibles.
4. IRL CONTEXT: Conecta cada evento digital con su impacto en el mundo real. ¿Cuánto dinero hay en juego? ¿Qué marcas están involucradas?
5. OPINIÓN EDITORIAL: Toma partido. No seas neutral. Si un creador ha hecho algo cuestionable, dilo.

PALABRAS Y FRASES VETADAS:
- "El algoritmo de YouTube es misterioso"
- "Sube contenido de calidad"
- "La consistencia es la clave"
- "En esta era digital"
- Cualquier consejo tipo tutorial (cómo editar, qué cámara comprar, etc.)
"""

PROMPT_YOUTUBE_EN = """ROLE: You are a Creator Economy Correspondent in the style of Tubefilter and Dexerto. You treat creators as BUSINESSES, not celebrities. You report on RPMs, retention drops, sponsorship deals, demonetization, and concurrent viewership. You despise articles that merely summarize drama without explaining the business impact.

COGNITIVE FRAMEWORK (MANDATORY):
1. CREATOR-AS-BUSINESS: Always frame creators through business metrics: RPM, CPM, subscriber growth rate, concurrent viewers, sponsorship revenue estimates. (Ex: "MrBeast's average RPM of $12.50 across 800M monthly views generates an estimated $10M/month in ad revenue alone.")
2. NAMED CREATORS WITH DATA: Always mention REAL NAMES (MrBeast, KSI, Logan Paul, PewDiePie, etc.) with verifiable data (subscribers, views, dates). NEVER talk about "creators" in abstract.
3. PLATFORM STRATEGY: Cover platform STRATEGY, not just news. Why is TikTok pushing podcasts? Why is Snapchat launching creator subscriptions? What's YouTube's TV play?
4. EXACT QUOTES: Include at least 1 direct blockquote from the creator/executive. (Ex: > "I want other creators to do their own version of La Velada," Ibai said.)
5. EDITORIAL OPINION: Take a side. If a creator did something questionable, say it. If a platform move will hurt creators, explain why.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "The YouTube algorithm is mysterious"
- "Just upload quality content"
- "Consistency is key"
- "In this digital age"
- Any tutorial-style advice (how to edit, what camera to buy, etc.)
"""

# --- PROMPT VIRAL / TRENDS ---
PROMPT_VIRAL_ES = """ROL: Eres un Analista Cultural y de Tendencias Virales al estilo de Magnet (Xataka) o Teknautas (El Confidencial). No haces salseo barato: haces análisis sociológico o económico de una polémica de internet. Tu tono es analítico, ligeramente cínico y contrariano.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. POR QUÉ, NO QUÉ: Nunca describas una tendencia sin explicar su causa sociológica. (Ej: MAL: "Los jóvenes usan vinilos". BIEN: "El vinilo es un acto de rebelión contra la intangibilidad del streaming — la Gen Z paga $35 por un LP porque el objeto físico les da una identidad que Spotify no puede dar.").
2. MICRO-HEADERS EN NEGRITA: Usa etiquetas estilo Magnet/Xataka dentro del texto: "**El dato.**", "**Contexto.**", "**Por qué es importante.**" para estructurar la información de forma escaneada.
3. FUENTES PRIMARIAS: Cita datos de plataformas (TikTok Newsroom, Meta Quarterly Reports, Pew Research, Google Trends, informes del IISS) NO de otros blogs. Si no tienes dato primario, dilo.
4. CITAS INSTITUCIONALES: Cita a personas con nombre + cargo + institución. (Ej: "John Phelan, secretario de Marina de EEUU, reconoció en el Congreso que 'todos nuestros programas son un desastre'.").
5. EL TAMAÑO DE LA BURBUJA: Para cada tendencia viral, dedica al menos un párrafo a por qué podría morir en 6 meses.

PALABRAS Y FRASES VETADAS:
- "Un arma de doble filo"
- "El mundo digital es un torbellino" 
- "No puedes ignorar esta tendencia"
- "Está arrasando en redes sociales"
- "Ha roto internet"
- "Queda por ver" / "Ya veremos"
"""

PROMPT_VIRAL_EN = """ROLE: You are a Cultural Critic and Tech Culture Analyst in the style of Vox and The Atlantic's tech section. You don't do gossip — you write Think Pieces. You take a TikTok controversy or Twitter meltdown and analyze it through the lens of sociology, economics, or algorithm design. Your titles are narrative, not clickbait: "The quiet collapse of..." / "AI agents could change your life — if they don't ruin it first."

COGNITIVE FRAMEWORK (MANDATORY):
1. WHY, NOT WHAT: Never describe a trend without explaining its sociological cause. (Ex: BAD: "Young people use vinyl." GOOD: "Vinyl is an act of rebellion against streaming's intangibility — Gen Z pays $35 for an LP because the physical object gives them an identity Spotify can't.")
2. NARRATIVE SUB-DECK: After the title-like opening, include a punchy one-liner that hooks. (Ex: "You've become increasingly replaceable." / "Blame AI." / "ChatGPT is boring compared to what comes next.")
3. PRIMARY SOURCES: Cite platform data (TikTok Newsroom, Meta Quarterly Reports, Pew Research, Google Trends) NOT from other blogs. If you lack primary data, say so.
4. CULTURAL CROSS-POLLINATION: Connect tech to Gen Z behavior, nostalgia economics, geopolitics, or labor markets. Your analysis must span at least TWO domains.
5. BUBBLE SIZE: For each viral trend, dedicate at least one paragraph to why it might die in 6 months.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "A double-edged sword"
- "The digital world is a whirlwind"
- "You can't ignore this trend"
- "Is taking social media by storm"
- "Has broken the internet"
- "Remains to be seen" / "Time will tell"
"""

PROMPT_TOOLS_ES = """ROL: Eres un Experto en Automatización y Redactor Técnico Senior al estilo de Xataka Basics o el blog oficial de Zapier. Tu misión es enseñar algo útil y práctico. 
No haces periodismo de opinión, haces Guías Paso a Paso orientadas a la resolución de problemas (Problem-Solution Framework). Escribes con claridad absoluta.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. BLUF CONTINUO (Bottom Line Up Front): La respuesta a la intención de búsqueda va en las primeras 2 frases.
2. ESTRUCTURA MILITAR: Problema -> Solución Conceptual -> Instrucciones Numeradas -> Expected Outcome.
3. NEGRILLAS EN UI: Cualquier elemento de la interfaz de usuario (Botones, Menús, Pestañas) DEBE ir en negrita. Ej: Haz clic en **Configuración** > **Avanzado**.
4. EJEMPLOS DE USO REAL: Toda teoría debe tener un caso de uso práctico aplicable a un profesional o empresa.
5. PRECISIÓN QUIRÚRGICA: Si un paso falla porque cambiaste una palabra, fracasaste. Sé exacto.

PALABRAS VETADAS:
- "Magia", "Un mundo de posibilidades", "Fácil y rápido", "Simplemente", "Descubre cómo"
"""

PROMPT_TOOLS_EN = """ROLE: You are an Automation Expert and Senior Technical Writer in the style of How-To Geek or the Zapier blog. You don't do opinion journalism; you do problem-oriented Step-by-Step Guides. You write with clinical clarity.

COGNITIVE FRAMEWORK (MANDATORY):
1. BLUF (Bottom Line Up Front): The answer to the search intent must be in the first 2 sentences. 
2. MILITARY STRUCTURE: The Problem -> The Conceptual Solution -> Numbered Instructions -> Expected Outcome.
3. BOLD UI ELEMENTS: Any user interface element (Buttons, Menus, Tabs) MUST be in bold. Ex: Click on **Settings** > **Advanced**.
4. REAL USE CASES: Every theoretical concept must be tied to a practical business or professional use case.
5. SURGICAL PRECISION: If a user fails because you used a vague word, you failed. Be exact.

BANNED WORDS:
- "Magic", "World of possibilities", "Quick and easy", "Simply", "Discover how"
"""

SYSTEM_FORMAT_RULES = """
CRITICAL FORMATTING RULES (ZERO TOLERANCE — VIOLATION = ARTICLE REJECTED):

1. NO TITLE REPETITION: Do NOT include the article title or H1 at the beginning.
2. START IMMEDIATELY: Start with the Hook paragraph directly.
3. FORBIDDEN PHRASES (INSTANT REJECTION IF FOUND):
   - English: "TL;DR", "Key Takeaways", "In summary", "In conclusion", "It remains to be seen", "In the ever-evolving", "It's worth noting", "Navigating the complexities"
   - Spanish: "En resumen", "En conclusión", "En última instancia", "En el vertiginoso", "Cabe destacar", "Un arma de doble filo", "Queda por ver"
4. HEADERS: Use H2 (##) for main sections. NEVER use H1 (#).
5. OUTBOUND LINKS (MANDATORY — MINIMUM 3):
   Include at least 3 hyperlinks to REAL external authoritative sources in markdown format.
   Examples: academic papers, official reports, established news outlets (Reuters, Bloomberg, TechCrunch, ArsTechnica, PubMed).
   Format: [descriptive anchor text](https://real-verified-url.com)
   NEVER fabricate or hallucinate URLs. Only link to sources you are confident exist.
6. UNIQUE DATA POINT (MANDATORY — MINIMUM 1):
   Include at least ONE original comparative calculation, metric, or data insight that adds information gain.
   Example: "If we divide Meta's $70B investment by Horizon's 200K monthly users, that's $350,000 per user — more expensive than a median US house."
   The reader must learn something they CANNOT find in any other article.
7. PARAGRAPH LENGTH VARIATION (MANDATORY):
   Paragraphs MUST vary between 1 and 6 sentences. Include at least:
   - One single-sentence paragraph for dramatic effect
   - One longer analytical paragraph (5-6 sentences)
   UNIFORM paragraph length is FORBIDDEN.
8. NO CONSTANT BULLET LISTS:
   Do NOT use bullet point lists in every section. Maximum ONE bulleted list per article.
   Prefer narrative prose, numbered steps, comparison tables, or Q&A format.
9. PERSONAL VOICE (MANDATORY):
   Include at least ONE editorial hot take, personal opinion, or rhetorical question that shows genuine author personality.
   The article must NOT read like a Wikipedia summary.
10. LANGUAGE PURITY:
    If writing in Spanish, ALL text must be in Spanish. No Spanglish, no untranslated English headers.
    If writing in English, ALL text must be in English.
"""

# --- CONFIGURACIÓN DE NICHOS ---
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

STRUCTURE_TEMPLATES = {
    'type_a': "INVESTIGATIVE JOURNALISM: Strong Opening Hook -> H2 Context & Background -> H2 Deep Analysis with Data -> H2 Expert Perspectives -> Final Editorial Take",
    'type_b': "NARRATIVE ESSAY: Personal Anecdote or Provocation -> The Core Problem (with numbers) -> Historical Parallel or Case Study -> Contrarian View -> Author's Verdict",
    'type_c': "DATA-DRIVEN REPORT: Striking Statistic Opening -> H2 The Numbers (tables/comparisons) -> H2 What It Means (analysis) -> H2 What Comes Next (prediction)",
    'type_d': "DEBATE FORMAT: Thesis Statement -> H2 The Case For -> H2 The Case Against -> H2 The Uncomfortable Truth -> Short Closing Provocation"
}

COMPLETED_FILE = 'data/completed.txt'

# --- FENIX V3: Bloqueo de Redundancia Semántica ---
STOPWORDS = {'the', 'and', 'of', 'in', 'to', 'a', 'is', 'for', 'on', 'with', 'that', 'it', 'as', 'by', 'an', 'at',
             'el', 'la', 'de', 'en', 'y', 'los', 'las', 'del', 'al', 'un', 'una', 'es', 'por', 'que', 'se', 'con',
             'su', 'no', 'para', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue', 'este', 'ha', 'son', 'its',
             'are', 'was', 'be', 'been', 'has', 'have', 'not', 'but', 'from', 'or', 'which', 'we', 'they', 'will',
             'about', 'today', 'why', 'how', 'what', 'trending', 'analysis', 'new', 'latest'}

def is_topic_redundant(new_topic, category):
    """Bloquea temas con más de 60% de solapamiento semántico con temas completados en la misma categoría."""
    if not os.path.exists(COMPLETED_FILE):
        return False
    
    with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    
    # Filtrar solo temas de la misma categoría
    category_topics = []
    for line in lines:
        if line.startswith(f"{category}:"):
            topic_text = line.split(":", 1)[1].strip().lower()
            category_topics.append(topic_text)
    
    if not category_topics:
        return False
    
    # Extraer keywords del nuevo tema (sin stopwords)
    new_keywords = {w for w in new_topic.lower().split() if w not in STOPWORDS and len(w) > 2}
    
    if not new_keywords:
        return False
    
    # Comparar contra cada tema existente
    for existing_topic in category_topics:
        existing_keywords = {w for w in existing_topic.split() if w not in STOPWORDS and len(w) > 2}
        if not existing_keywords:
            continue
        
        # Solapamiento bidireccional
        overlap = len(new_keywords & existing_keywords)
        similarity = overlap / min(len(new_keywords), len(existing_keywords))
        
        if similarity > 0.4:
            print(f"  ⚠️ REDUNDANCY: '{new_topic}' overlaps {similarity*100:.0f}% with '{existing_topic}'")
            return True
    
    return False

def safety_check(topic):
    try:
        prompt = f"ACT AS: Content Safety Moderator. TOPIC: '{topic}'. OUTPUT: SAFE or UNSAFE.\nRULES: Allow clickbait, sensationalism, drama, controversies, and gossip (SAFE). ONLY reply 'UNSAFE' if it promotes real-world physical violence, terrorism, self-harm, or explicit adult content/pornography. Otherwise, it is SAFE."
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        if "UNSAFE" in resp.text.strip().upper():
            return False
        return True
    except:
        return True

def planificar_articulo(tema, contexto, lang, category_config):
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    lang_instruction = (
        f"\n\nCRITICAL LANGUAGE RULE: The 'titulo' MUST be written ENTIRELY in {'SPANISH (Español)' if lang == 'es' else 'ENGLISH'}. "
        f"{'Do NOT use any English words in the title except proper nouns (brand names like Bitcoin, NBA, etc.).' if lang == 'es' else 'Do NOT use any Spanish words in the title.'} "
        f"VIOLATION = INSTANT REJECTION."
    )
    # Handle V4 dict format
    ctx_text = contexto.get('content', '')[:1000] if isinstance(contexto, dict) else str(contexto)[:1000]
    prompt = f"{prompt_persona}\n{SYSTEM_FORMAT_RULES}{lang_instruction}\nACT LIKE EDITOR. Topic: {tema}\nContext: {ctx_text}\nLanguage: {lang}\nSTRICT JSON: {{ \"titulo\": \"...\", \"slug_sugerido\": \"...\" }}"
    try:
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
        plan = json.loads(resp.text.replace('```json', '').replace('```', '').strip())
        suffix = "-en" if lang == "en" else ""
        plan['slug'] = SlugManager.generate(plan['slug_sugerido']) + suffix
        return plan
    except:
        return {"titulo": f"{tema} Analysis", "slug": SlugManager.generate(tema) + ("-en" if lang=="en" else "")}

# --- E-E-A-T OUTBOUND LINK INJECTION RULES ---
EEAT_LINK_RULES = """
OUTBOUND LINKS — STRICT E-E-A-T COMPLIANCE (ZERO TOLERANCE):

Every time you mention ANY of the following, you MUST include a markdown hyperlink:
- A statistic or data point → link to the original report/study
- An expert's name or quote → link to their profile, interview, or publication
- A company's action (acquisition, layoff, product launch) → link to a credible news article
- A study or research paper → link to PubMed, arXiv, IEEE, or the journal
- A tool, product, or platform → link to its official website

Format: [descriptive anchor text](https://real-verified-url.com)

MINIMUM: 5 outbound links per article.
MAXIMUM: Do not exceed 12 outbound links (avoid appearing spammy).

CRITICAL ANTI-HALLUCINATION RULE:
- You may ONLY use URLs that appear in the RESEARCH DATA section provided below.
- If a fact has NO corresponding URL in the research data, mention the source name as plain text WITHOUT a hyperlink.
- It is ABSOLUTELY FORBIDDEN to invent, guess, or fabricate any URL.
- Do NOT use scholar.google.com or google.com/search as placeholder links.
- A single fabricated URL will cause the ENTIRE article to be rejected.

ARTICLES WITH FEWER THAN 3 OUTBOUND LINKS WILL BE REJECTED.
"""

# ============================================================
# PROTOCOLO SPIDERWEB: Internal Linking Engine
# ============================================================

def _get_internal_links(category, lang, current_slug=""):
    """
    Lee los últimos 15 artículos de la misma categoría/idioma
    y devuelve una lista de (título, ruta_relativa) para interlinking.
    """
    pattern = f"content/{lang}/{category}/*.md"
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:15]
    links = []
    for fpath in files:
        slug = os.path.basename(fpath).replace('.md', '')
        if slug == current_slug or slug == '_index':
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read(500)
            # Extract title from frontmatter
            import re as _re
            match = _re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, _re.MULTILINE)
            if match:
                title = match.group(1).strip().strip('"').strip("'")
                # FIX BILINGÜE: EN es raíz /{cat}/{slug}/, ES es /es/{cat}/{slug}/
                if lang == "es":
                    rel_path = f"/es/{category}/{slug}/"
                else:
                    rel_path = f"/{category}/{slug}/"
                links.append((title, rel_path))
        except:
            continue
    return links[:10]  # Max 10 candidates


def _call_en_engine(prompt_text):
    """
    Motor Inglés Trinity: GLM-4-Flash → Fallback OpenRouter/Llama3.
    Usa la API compatible con OpenAI para ambos proveedores.
    """
    # --- INTENTO 1: Zhipu GLM-4-Flash ---
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    if zhipu_key:
        print("   🧠 [Trinity EN] Motor 1: Zhipu GLM-4.7-FlashX...")
        try:
            glm_client = OpenAI(
                api_key=zhipu_key,
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            )
            resp = glm_client.chat.completions.create(
                model="glm-4.7-flashx",
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.85,
                max_tokens=4096
            )
            result = resp.choices[0].message.content.strip()
            if result and len(result) > 200:
                print("   ✅ GLM-4-Flash respondió correctamente.")
                return result
            else:
                print("   ⚠️ GLM respuesta vacía o muy corta. Activando fallback...")
        except Exception as e:
            print(f"   ⚠️ GLM-4.7-FlashX error: {e}. Activando fallback OpenRouter...")
    else:
        print("   ⚠️ ZHIPU_API_KEY no configurada. Saltando a OpenRouter...")

    # --- INTENTO 2: OpenRouter / Llama 3 ---
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        print("   🔄 [Trinity EN] Motor 2 (Fallback): OpenRouter / Llama 3...")
        try:
            or_client = OpenAI(
                api_key=or_key,
                base_url="https://openrouter.ai/api/v1"
            )
            resp = or_client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.85,
                max_tokens=4096
            )
            result = resp.choices[0].message.content.strip()
            if result and len(result) > 200:
                print("   ✅ OpenRouter/Llama-3.3-70B respondió correctamente.")
                return result
            else:
                print("   ⚠️ OpenRouter respuesta vacía. Cayendo a Gemini de emergencia...")
        except Exception as e:
            print(f"   ⚠️ OpenRouter error: {e}. Cayendo a Gemini de emergencia...")
    else:
        print("   ⚠️ OPENROUTER_API_KEY no configurada. Cayendo a Gemini de emergencia...")

    # --- EMERGENCIA: Gemini (nunca dejar sin artículo) ---
    print("   🚨 [Trinity EN] Motor de Emergencia: Gemini...")
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_text)
    return resp.text.strip()


def escribir_articulo(meta, contexto, lang, category_config, category="ia"):
    print(f"✍️ PULITZER PIPELINE ({lang.upper()}): {meta['titulo']}...")
    # === AISLAMIENTO ESTRICTO DE VARIABLES ===
    prompt_persona = category_config['prompt_es'] if lang == 'es' else category_config['prompt_en']
    structure = random.choice(list(STRUCTURE_TEMPLATES.values()))
    
    # Extract content string from research dict
    if isinstance(contexto, dict):
        research_text = contexto.get('content', '')
        research_layer = contexto.get('layer', 'unknown')
        print(f"   📊 Research source: {research_layer}")
    else:
        research_text = str(contexto)
    
    # === PROTOCOLO SPIDERWEB V2: Solo si hay artículos diversos ===
    internal_links = _get_internal_links(category, lang, meta.get('slug', ''))
    spiderweb_instruction = ""
    if len(internal_links) >= 2:
        unique_links = []
        seen_words = set()
        for title, path in internal_links:
            title_words = {w.lower() for w in title.split() if len(w) > 3}
            if len(title_words & seen_words) < len(title_words) * 0.5:
                unique_links.append((title, path))
                seen_words.update(title_words)
        
        if len(unique_links) >= 2:
            links_text = "\n".join([f"  - [{t}]({p})" for t, p in unique_links[:5]])
            spiderweb_instruction = f"""\nINTERNAL LINKING (Spiderweb Protocol — ONLY if naturally relevant):
You MAY insert UP TO 2 internal links to other articles on our site, but ONLY if they are genuinely relevant to the current topic.
Do NOT force a link if it doesn't fit naturally. A forced, irrelevant internal link is WORSE than no link at all.
Insert them NATURALLY inside paragraphs as contextual hyperlinks. Do NOT put them in a list at the end.
Available articles to link to:
{links_text}
Format: [descriptive anchor text](relative-path)
IF NONE OF THESE ARTICLES ARE RELEVANT TO THE CURRENT TOPIC, DO NOT LINK TO ANY OF THEM.
"""

    # ============================================================
    # FASE 1: ESPECIALISTA EN CLICKBAIT ÉTICO — Genera título viral
    # ============================================================
    print(f"   🎯 [Fase 1/3] Especialista en Clickbait Ético...")
    
    lang_name = "ESPAÑOL" if lang == "es" else "ENGLISH"
    # Regla de capitalización según benchmark:
    # - EN: Title Case estricto (TechCrunch/The Verge: "Sam Altman Would Like to Remind You That Humans Use a Lot of Energy, Too")
    # - ES: Oración (Xataka: "Gemini 3.1 Pro acaba de destronar a Claude: Google vuelve a liderar la carrera de la IA")
    if lang == "es":
        cap_rule = "FORMATO ESPAÑOL (estilo Xataka): Solo la primera palabra del título lleva mayúscula (y los nombres propios). NO uses Title Case con mayúsculas en cada palabra. Ejemplo correcto: 'Databricks acaba de anunciar algo que cambia las reglas del juego'. Ejemplo INCORRECTO: 'Databricks Acaba De Anunciar Algo Que Cambia Las Reglas Del Juego'."
    else:
        cap_rule = "FORMAT ENGLISH (TechCrunch/Verge style): Use strict Title Case — capitalize every major word (nouns, verbs, adjectives, adverbs). Only lowercase articles (a, the, an), conjunctions (and, or, but), and short prepositions (in, of, to, for) unless they are the first word. Example: 'Sam Altman Would Like to Remind You That Humans Use a Lot of Energy, Too'."
    
    title_prompt = f"""ACT AS: Viral headline editor for TechCrunch (EN) or Xataka (ES). You write titles that DEMAND clicks.

TASK: Generate 5 candidate titles for an article about: "{meta['titulo']}"
LANGUAGE: {lang_name} ONLY. {"ABSOLUTAMENTE PROHIBIDO usar palabras en inglés excepto nombres propios (Bitcoin, ChatGPT, etc.)." if lang == "es" else ""}

RESEARCH CONTEXT (use the juiciest data points):
{research_text[:3000]}

RULES:
- Each title MUST contain a specific NUMBER, NAME, or SHOCKING CLAIM from the research
- FORBIDDEN WORDS: "crecimiento exponencial", "panorama", "landscape", "comprehensive", "overview", "deep dive", "guía completa", "todo lo que necesitas saber"
- FORBIDDEN: Titles that are questions. NO question marks allowed. Make STATEMENTS, not questions.
- TITLES MUST provoke emotion: outrage, curiosity, fear, or disbelief
- Use patterns like: "X did Y and nobody noticed", "The hidden X behind Y", "Why X is lying about Y", "X just broke: what it means for Y"
- Maximum 15 words per title. Minimum 8 words.
- {cap_rule}
- {"Los títulos deben estar COMPLETAMENTE en español. Cero spanglish." if lang == "es" else ""}

OUTPUT FORMAT (exactly 6 lines):
1. [title option 1]
2. [title option 2]
3. [title option 3]
4. [title option 4]
5. [title option 5]
BEST: [paste the single best title here]

OUTPUT ONLY THESE 6 LINES. NOTHING ELSE."""

    try:
        title_resp = client.models.generate_content(model='gemini-2.0-flash', contents=title_prompt)
        title_lines = title_resp.text.strip().split('\n')
        
        # Extraer el BEST title
        viral_title = meta['titulo']  # fallback
        for line in title_lines:
            if line.strip().upper().startswith('BEST:'):
                candidate = line.split(':', 1)[1].strip().strip('"').strip("'")
                if len(candidate.split()) >= 4:
                    viral_title = candidate
                    break
        
        # Si no encontró BEST:, tomar el último título válido
        if viral_title == meta['titulo']:
            for line in reversed(title_lines):
                clean = re.sub(r'^\d+\.\s*', '', line.strip()).strip('"').strip("'")
                if len(clean.split()) >= 4 and not clean.upper().startswith('BEST'):
                    viral_title = clean
                    break
        
        meta['titulo'] = viral_title
        print(f"   ✅ [Fase 1/3] Título viral: {viral_title}")
    except Exception as e:
        print(f"   ⚠️ [Fase 1/3] Error generando título viral: {e}. Usando título original.")

    # ============================================================
    # FASE 2: REDACTOR DE DATOS DUROS — Escribir el artículo
    # Con blindaje militar anti-chatbot, anti-alucinación, anti-leak
    # ============================================================
    print(f"   ✍️ [Fase 2/3] Redactor de Datos Duros (Blindaje Militar)...")
    
    # Outline rápido (mantener la pre-digestión de datos)
    outline_prompt = f"""ACT AS: Senior Editorial Strategist for a publication like Autoblog, TechCrunch, or Xataka.
TASK: Create a CONCISE article outline for: "{meta['titulo']}"
LANGUAGE: {lang}

RESEARCH DATA:
{research_text[:8000]}

OUTPUT a structured outline with this EXACT structure:

TL;DR BULLETS (exactly 3):
- [Bullet 1: The single most important fact. Must be a complete sentence with a specific number or name. This should answer the article's core question in one line.]
- [Bullet 2: The second most surprising data point. Include the source name.]
- [Bullet 3: The practical consequence or "so what" for the reader. What changes for them.]

## [Descriptive Title for Section 1] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Named Entity: [Full name + title + institution]
- Key data point from research with source
- What new information this section adds

## [Descriptive Title for Section 2] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Named Entity: [different person/institution]
- Context and background analysis
- Key data point from research with source

## [Descriptive Title for Section 3] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Named Entity: [different person/institution]
- Nuanced perspective or contrarian view
- Key data point from research with source

## [Descriptive Title for Section 4] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Named Entity: [different person/institution]
- Practical steps or actionable insights
- Key data point from research with source

## [Descriptive Title for Section 5] {"(EN ESPAÑOL)" if lang == "es" else ""}
- Future outlook based on data
- Key data point from research with source

## {"Nuestra lectura" if lang == "es" else "The Bottom Line"}
- Author's definitive stance (pick a side)
- One specific actionable recommendation
- Punchy closing one-liner

CRITICAL RULES:
- Section titles must be DESCRIPTIVE and SPECIFIC (e.g. "The $20K Price Cut That Changes Everything"), NEVER generic ("Section 1", "The Current Landscape").
- ONLY use facts from the RESEARCH DATA.
- Do NOT invent numbers or perform calculations.
- Every section must name at least one real person, company, or institution.
"""

    try:
        outline_resp = client.models.generate_content(model='gemini-2.0-flash', contents=outline_prompt)
        outline = outline_resp.text.strip()
        print(f"   ✅ Outline: {len(outline)} chars")
    except Exception as e:
        print(f"   ⚠️ Outline error: {e}. Modo directo.")
        outline = ""

    outline_section = f"\n\nARTICLE OUTLINE (follow this structure strictly):\n{outline}\n" if outline else ""

    # Configurar ejemplos dinámicos por idioma y CATEGORÍA para inyectar en el prompt militar (Protocolo Camaleón)
    if lang == "es":
        if category == "fitness":
            # ── Estilo Vitónica / Fitness Revolucionario: Científico, longevidad, geroprotección ──
            ex_opening = '"Las personas que incluyen polifenoles en su dieta son las que mejor envejecen y viven más años, según los últimos estudios sobre zonas azules."'
            ex_bullets = """   * Los polifenoles actúan como "geroprotectores" naturales, ralentizando el deterioro celular al influir en los mecanismos que regulan el envejecimiento.
   * En zonas como Okinawa, el consumo de antocianinas presentes en la batata morada es clave para la salud cardiovascular de sus centenarios. 
   * La evidencia publicada en el Aging Research Reviews asocia directamente la ingesta de estos compuestos con una reducción drástica de la inflamación sistémica."""
            ex_link1 = '"Lo más interesante de estos compuestos, según explica [Vitónica](https://...), es que no solo previenen enfermedades, sino que alargan la vida saludable."'
            ex_link2 = '"Al igual que ocurre con el [aceite de oliva virgen extra](https://...), el café aporta estilbenos y ácidos fenólicos que protegen el cerebro."'
        elif category == "crypto":
            # ── Estilo BeInCrypto / CoinTelegraph ES: Institucional, frío, datos on-chain ──
            ex_opening = '"Bitdeer, con sede en Singapur y actualmente el mayor self-miner que cotiza en bolsa a nivel mundial, liquidó toda su tesorería de Bitcoin reportando cero BTC en posesión al 20 de febrero."'
            ex_bullets = """   * Bitdeer ha liquidado toda su tesorería de Bitcoin, reportando cero BTC en posesión al 20 de febrero, tras vender su producción reciente de 189.8 BTC.
   * La medida se produce mientras la dificultad de la red aumenta un 14.7% y el hashprice cae por debajo de 30 dólares por PH/s por día.
   * Para extender su runway, Bitdeer anunció una ampliación de su emisión de notas convertibles por 325 millones de dólares, acelerando su giro hacia la IA."""
            ex_link1 = '"Tras una breve recuperación causada por tormentas invernales, según [BeInCrypto](https://...), la red de Bitcoin vivió una recuperación en forma de V."'
            ex_link2 = '"Bitdeer destinará 138,2 millones de dólares a [recomprar sus notas convertibles senior](https://...) con vencimiento en 2029."'
        elif category == "viral":
            # ── Estilo Magnet/Xataka: Análisis sociológico, micro-headers, títulos magnéticos ──
            ex_opening = '"En un momento geopolítico tenso a escala mundial con varios frentes abiertos, China acaba de lograr un hito histórico: está fabricando submarinos nucleares más rápido que cualquier otro país, según un informe del IISS."'
            ex_bullets = """   * China ha superado a Estados Unidos en el ritmo de lanzamiento de submarinos nucleares: 10 unidades entre 2021-2025 frente a 7 de Washington.
   * John Phelan, secretario de Marina de EEUU, reconoció en el Congreso que "todos nuestros programas son un desastre".
   * El sorpasso amenaza la hegemonía que Washington ha mantenido bajo el agua durante décadas."""
            ex_link1 = '"China acaba de lograr un hito histórico, [según un informe del IISS](https://...), al superar a EEUU en producción de submarinos nucleares."'
            ex_link2 = '"John Phelan, secretario de Marina de EEUU, [reconocía en el Congreso](https://...) que todos sus programas llevan retraso."'
        elif category == "youtube":
            # ── Estilo Areajugones / Dexerto ES: Ritmo altísimo, citas de streamers, métricas ──
            ex_opening = '"Ibai Llanos ha confirmado la segunda edición de la Streamers Cup 3x3, el torneo de baloncesto que organiza junto a la FIBA para dar visibilidad al formato 3 contra 3."'
            ex_bullets = """   * La Streamers Cup 3x3 se celebrará el 21 de abril a las 18:00 hora española, con retransmisión en el canal de Twitch de Ibai.
   * El evento llega apenas seis meses después de la primera edición, que superó los 400.000 espectadores simultáneos.
   * Ibai confirmó la noticia con un simple "Dos eventos en una semana, al viejo estilo", señalando su vuelta a la hiperactividad de contenidos."""
            ex_link1 = '"Ibai dijo textualmente: \"Quiero que otros creadores repitan La Velada\", en [una entrevista con Dexerto](https://...)."'
            ex_link2 = '"El evento llega tras el éxito de [Disaster Chefs](https://...), que arrancó su segunda temporada esta misma semana."'
        else:
            # ── Estilo Genbeta/Xataka: Negocio tech, IA, impacto corporativo ──
            ex_opening = '"Meta acaba de cerrar una de las operaciones más llamativas del año: la compra de Manus por 2.000 millones de dólares para liderar la carrera de los agentes de IA."'
            ex_bullets = """   * La adquisición de Manus, una startup de origen chino con sede en Singapur, busca dotar a Meta de agentes capaces de ejecutar tareas complejas con mínima supervisión.
   * La operación, valorada en más de 2.000 millones de dólares, responde al cambio de paradigma: de los chatbots que hablan a los agentes que "hacen".
   * Meta integrará esta tecnología en sus servicios globales, centrándose en automatizar flujos de trabajo de oficina como análisis de datos y generación de informes autónomos."""
            ex_link1 = '"Según el análisis de [un experto en X](https://x.com/...), el movimiento de Zuckerberg no es solo talento, es una barrera geopolítica contra China."'
            ex_link2 = '"Manus saltó a la fama por ser el [primer trabajador digital autónomo](https://...), superando la barrera de los simples chatbots de [conversación generativa](https://...)."'
    else:
        if category == "fitness":
            # ── Stronger By Science / BarBend: Academic, mechanism-first ──
            ex_opening = '"Without question, creatine is the gold standard by which all strength-related supplements are judged — and the science behind it is more nuanced than most fitness influencers would have you believe."'
            ex_bullets = """   * Compared to rest, the rate of ATP demand increases up to 1,000-fold during intense exercise, making phosphocreatine the body's emergency energy currency.
   * A McMaster University study (n=40, 12 weeks) showed low-load training to failure produces comparable hypertrophy to heavy training.
   * Creatine may also promote lean body mass by directly affecting myostatin, myogenic regulatory factors, and satellite cell activation."""
            ex_link1 = '"As reviewed by [Chilibeck et al](https://ncbi.nlm.nih.gov/...), creatine may promote increases in lean body mass by directly affecting myostatin and satellite cell activation."'
            ex_link2 = '"The rate of ATP demand [increases up to 1,000-fold](https://ncbi.nlm.nih.gov/...) during intense exercise, making phosphocreatine the body\'s rapid-fire energy system."'
        elif category == "crypto":
            # ── CoinDesk / The Block: Macro-first, institutional ──
            ex_opening = '"Bitcoin see-saws around $68,000 as tariff uncertainty weighs on risk assets after President Trump raised the global tariff rate to 15% despite a Supreme Court ruling."'
            ex_bullets = """   * Bitcoin echoes 'late 2022' bear market bottom, K33 says, with on-chain metrics showing capitulation-level selling pressure.
   * ProShares' stablecoin-ready ETF sees $17 billion debut, sparking speculation about Circle's reserve strategy.
   * SEC makes quiet shift to brokers' stablecoin holdings that may pack big results for institutional adoption."""
            ex_link1 = '"Bitcoin echoes \'late 2022\' bear market bottom, [K33 says](https://...), with on-chain metrics showing capitulation."'
            ex_link2 = '"Ripple\'s Brad Garlinghouse says [CLARITY bill has \'80% chance\'](https://...) of passing by April."'
        elif category == "viral":
            # ── Vox / The Atlantic: Think-piece, narrative ──
            ex_opening = '"AI agents could change your life — if they don\'t ruin it first. ChatGPT is boring compared to what comes next."'
            ex_bullets = """   * AI's threat to white-collar jobs just got more real: you've become increasingly replaceable, according to labor economists at MIT.
   * Gadgets are getting worse and more expensive at the same time — blame AI's insatiable appetite for memory chips and data center capacity.
   * Gen Z's obsession with the 2010s isn't mere nostalgia: it's an escape mechanism from entering the workforce at the lowest real wage in 40 years."""
            ex_link1 = '"As [Vox reported](https://...), the new TikTok is freaking people out — and the censorship concerns are warranted."'
            ex_link2 = '"Claude has an 80-page \'soul document.\' As [The Atlantic explains](https://...), the real question is whether that\'s enough to make it good."'
        elif category == "youtube":
            # ── Tubefilter / Dexerto: Creator economy metrics ──
            ex_opening = '"Snapchat pledges to unlock scalable creator revenue with a new Subscriptions product — a direct response to YouTube\'s dominance in the long-form creator economy."'
            ex_bullets = """   * YouTube's 'pester power' converts kids' requests into purchases, making it the most important platform for Generation Alpha.
   * TikTok wants to use its commanding position in the recording industry to assist its podcast push — but can it stay 'In the Mix'?
   * Spotter is bringing its Showcase back to New York to build buzz around 'Creator TV', signaling the next phase of creator monetization."""
            ex_link1 = '"As [Tubefilter reported](https://...), YouTube\'s first video now belongs in a museum — \'Me at the Zoo\' is on display at the V&A."'
            ex_link2 = '"Snapchat pledges to [unlock scalable creator revenue](https://...) with a new Subscriptions product."'
        else:
            # ── TechCrunch / The Verge: Silicon Valley insider ──
            ex_opening = '"OpenAI CEO Sam Altman addressed concerns about AI\'s environmental impact this week, calling water usage claims \"completely untrue, totally insane, no connection to reality.\""'
            ex_bullets = """   * OpenAI reportedly finalizing $100B deal at more than $850B valuation, making it the most valuable private company in history.
   * Google's new Gemini Pro model has record benchmark scores — again — but the real question is whether benchmarks still matter.
   * Peak XV raises $1.3B, doubling down on AI as global VC rivalry in India heats up."""
            ex_link1 = '"Sam Altman [addressed concerns](https://...) about AI\'s environmental impact, calling water usage claims \"completely untrue.\""'
            ex_link2 = '"As [TechCrunch reported](https://...), How Ricursive Intelligence raised $335M at a $4B valuation in just 4 months."'

    # === PROMPT MILITAR ===
    anti_chatbot_shield = f"""
════════════════════════════════════════════════════
 ███ MILITARY-GRADE OUTPUT RULES — VIOLATION = REJECTION ███
════════════════════════════════════════════════════

🚫 ANTI-CHATBOT SHIELD:
- START the article IMMEDIATELY with a powerful opening sentence with a hard fact.
- DO NOT write introductory phrases: "Here is the article", "Aquí está el artículo", "Aquí tienes", "Sure", "Claro", "Of course", "Let me", "I'll write".
- DO NOT write meta-commentary about writing or instructions.
- The FIRST character of your output must be part of the article content.

📐 AUTOBLOG STRUCTURE (follow this EXACT layout):

1. OPENING PARAGRAPH: One powerful sentence with the core news. Max 2 sentences. Like Autoblog: {ex_opening}

2. TL;DR BULLET BLOCK (immediately after opening, NO header, NO "## Key Takeaways"):
   Write exactly 3 bullet points starting with "*". Each must be:
   - A COMPLETE, self-contained sentence that answers one key question about the topic
   - Contains at least ONE specific number, name, or date
   - Could be directly quoted by Google AI Overview as a standalone fact
   Example from Autoblog:
{ex_bullets}

3. BODY SECTIONS: Use descriptive ## H2 headers (NEVER "Section 1", "Section 2"). Then short paragraphs.

4. CLOSING: A punchy editorial one-liner. Declarative. No questions.

✂️ PARAGRAPH RULES (Autoblog standard):
- MAXIMUM 3 sentences per paragraph. If a paragraph has 4+ sentences, SPLIT IT.
- Every paragraph must introduce exactly ONE new fact or data point. No fluff.
- ABSOLUTELY FORBIDDEN: ALL question marks (? and ¿). Zero tolerance everywhere in the article.
  BAD: "Is AI really replacing jobs?" → GOOD: "AI is already eliminating 34% of entry-level roles, according to McKinsey."
  BAD: "¿Qué significa esto?" → GOOD: "Esto implica una reducción del 40% en costos operativos."
- FORBIDDEN: Repeating the same idea. Every paragraph = new information.
- FORBIDDEN: Vague filler like "This is important because...", "It's worth noting...", "Es importante destacar..."
- Lead each paragraph with its most important fact (Inverted Pyramid).

🔢 MATH SHIELD:
- DO NOT perform any calculations. Report numbers EXACTLY as stated by sources.
- NEVER write "if we divide X by Y" or "this works out to".

🌐 LANGUAGE SHIELD:
- {"EVERY word must be in SPANISH including ALL H2/H3 headers. ZERO English words except proper nouns (ChatGPT, Bitcoin, etc.)." if lang == "es" else "EVERY word must be in ENGLISH."}
- {"DO NOT use 'Editorial Verdict'. Use 'Nuestra lectura' or 'El veredicto' IN SPANISH." if lang == "es" else ""}
- {"DO NOT leave ANY English instruction text in the output." if lang == "es" else "DO NOT leave ANY Spanish text in the output."}

🔗 LINK SHIELD (Autoblog style — links WOVEN into sentences):
- Include at least 3 outbound links woven naturally INTO sentences.
- Autoblog example: {ex_link1}
- Autoblog example: {ex_link2}
- ONLY use URLs that appear VERBATIM in the RESEARCH DATA. Copy-paste the exact URL.
- If a URL in the research contains "vertexaisearch.cloud.google.com" DO NOT USE IT. Mention the source name in **bold** instead.
- If a fact has NO URL in the research, mention the source as **Source Name** with NO hyperlink.
- FABRICATING a URL = INSTANT REJECTION.
- NEVER paste a naked URL. Every URL must be inside [Anchor Text](URL) format.
- NEVER use bracket-only references like [source name] without a proper (URL).

📏 LENGTH: Minimum 1500 words. Articles under 1200 words are REJECTED.

🌐 GEO-DOMINANCE & FORMATTING:
- The 3 TL;DR bullets (described above) ARE the GEO signal. No separate "Key Takeaways" header needed.
- TABLE USE (PROBABILISTIC): If comparing 3 or more complex data points, use a clean Markdown table (| --- |). Otherwise, rely on spaced bullet lists. Vary your structural choices.
- SPACED LISTS: Whenever you use a bulleted list (* ), ALWAYS add a blank line between each bullet point so they don't render bunched together.
- ENTITY DENSITY: Always write "Satya Nadella, CEO de Microsoft" never "el CEO". Full names everywhere.
- CITATION FORMAT: Weave source names into sentences: "Según [nombre de la fuente](URL), dato..." Never cite anonymously.
════════════════════════════════════════════════════
"""

    prompt = (
        f"{prompt_persona}\n"
        f"{SYSTEM_FORMAT_RULES}\n"
        f"{anti_chatbot_shield}\n"
        f"{EEAT_LINK_RULES}\n"
        f"{spiderweb_instruction}\n"
        f"WRITE ARTICLE: {meta['titulo']}\n"
        f"{outline_section}"
        f"ORIGINAL RESEARCH DATA (use as factual foundation — cite sources with links):\n{research_text}\n"
        f"TEMPLATE: {structure}\n"
        f"LANG: {lang}"
    )

    # === CEREBRO ESPAÑOL: GEMINI ===
    if lang == "es":
        print("   🇪🇸 [Fase 2/3] Motor ES: Gemini 2.0 Flash")
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        resultado = resp.text.strip()
    # === CEREBRO INGLÉS: GLM → OpenRouter → Gemini Emergency ===
    else:
        print("   🇬🇧 [Fase 2/3] Motor EN: GLM-4-Flash → OpenRouter → Gemini")
        resultado = _call_en_engine(prompt)
        
    # === VALIDACIÓN DE LONGITUD MÍNIMA (Ambos idiomas) ===
    word_count = len(resultado.split()) if resultado else 0
    if word_count < 1500:
        print(f"   ⚠️ [Quality] Artículo demasiado corto ({word_count} palabras). Regenerando con Gemini para EXPANDIR...")
        extended_prompt = prompt + f"\n\nCRITICAL: The article MUST be at LEAST 1500 words. You only wrote {word_count} words! Write a comprehensive, in-depth analysis. Do NOT be brief. Expand every single section with deep analysis, data context, and expert commentary."
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=extended_prompt)
        retry_result = resp.text.strip()
        if len(retry_result.split()) > word_count:
            resultado = retry_result
            print(f"   ✅ [Quality] Regenerado expandido: {len(resultado.split())} palabras")

    word_count_draft = len(resultado.split()) if resultado else 0
    print(f"   📊 [Fase 2/3] Borrador: {word_count_draft} palabras")

    # ============================================================
    # FASE 3: EDITOR JEFE / SANITIZADOR — Filtro final anti-IA
    # ============================================================
    print(f"   🧹 [Fase 3/3] Editor Jefe: Sanitización final...")
    
    sanitize_prompt = f"""ACT AS: Senior copy editor at Autoblog / Car and Driver. You enforce the Autoblog house style mercilessly. You are the LAST line of defense.

TASK: Clean and reformat this article draft to match Autoblog's exact editorial standard. Return the final Markdown ready for publication.

ARTICLE DRAFT:
{resultado}

AUTOBLOG HOUSE STYLE CHECKLIST (apply ALL):

1. OPENING (first lines of the article):
   - The article MUST start with 1-2 sentences stating the core news with a hard fact. No fluff, no preamble.
   - DELETE any AI phrases: "Aquí está", "Here is", "Sure", "Claro", "Let me", "Aquí tienes", "I'll", "Below is".
   - Immediately after the opening sentence(s), there MUST be 3 bullet points (using *) summarizing the key facts.
   - These 3 bullets must NOT have a header like "## Key Takeaways" or "## Puntos Clave". They appear bare, right after the intro paragraph, before the first ## H2 section.
   - If a "## Key Takeaways" or "## Puntos Clave" header exists, REMOVE the header but KEEP the bullets.

2. PARAGRAPH LENGTH (CRITICAL):
   - MAXIMUM 3 sentences per paragraph. Split any paragraph with 4+ sentences into two.
   - Every paragraph must contain at least one specific data point (number, name, date, or quote).

3. QUESTION MARKS — TOTAL ANNIHILATION:
   - DELETE or REWRITE every sentence that contains "?" or "¿".
   - Replace with a declarative statement that conveys the same information.
   - Example: "Is this the end of SaaS?" → "This marks a turning point for the SaaS industry."

4. LINKS:
   - DELETE any URL containing "vertexaisearch.cloud.google.com". Replace with the source name in **bold**.
   - DELETE any naked URL (a URL not wrapped in [Anchor Text](URL) format).
   - All remaining links must use format: [descriptive text](https://real-url.com). Fix any malformed links.

5. HEADERS:
   - Remove any # (H1) headers. Only ## (H2) and ### (H3) allowed.
   - Headers must be DESCRIPTIVE and SPECIFIC, never generic like "Section 1", "The Current Landscape", "Overview".
   - {"Replace 'Editorial Verdict' with 'Nuestra lectura' or 'El veredicto'." if lang == "es" else ""}
   - {"All headers MUST be in Spanish. Rewrite any English headers." if lang == "es" else "All headers must be in English."}

6. ENTITY CHECK:
   - Replace vague pronouns ("the company", "the expert", "el CEO") with actual names and titles.

7. TABLE AND LIST CHECK (CRITICAL FORMATTING):
   - TABLE OPTIMIZATION: Keep Markdown tables ONLY if they compare 3 or more entities clearly. If it's a simple list, convert to text. Ensure table headers are clean.
   - LIST SPACING: Ensure there is an empty line between EVERY bullet point in the article. Bullets must never touch each other.

8. CLOSING:
   - The article must end with a punchy editorial statement (1-2 sentences max). Declarative. No questions.
   - DELETE any "what do you think?" or audience engagement questions at the end.

9. PRESERVE everything else: all valid links, formatting, data points, expert quotes, bold text.

OUTPUT: The cleaned Markdown article matching Autoblog house style. NOTHING ELSE — no preamble."""

    try:
        if lang == "es":
            sanitize_resp = client.models.generate_content(model='gemini-2.0-flash', contents=sanitize_prompt)
            clean_result = sanitize_resp.text.strip()
        else:
            clean_result = _call_en_engine(sanitize_prompt)
        
        # Validar que el sanitizador no destruyó el artículo
        if clean_result and len(clean_result.split()) > word_count_draft * 0.6:
            resultado = clean_result
            print(f"   ✅ [Fase 3/3] Sanitizado: {len(resultado.split())} palabras (de {word_count_draft})")
        else:
            print(f"   ⚠️ [Fase 3/3] Sanitizador devolvió texto demasiado corto. Conservando borrador original.")
    except Exception as e:
        print(f"   ⚠️ [Fase 3/3] Error en sanitización: {e}. Conservando borrador original.")

    # === POST-PROCESADO REGEX: Limpieza de artefactos residuales ===
    resultado = _clean_article_content(resultado)
    return resultado


def _clean_article_content(text):
    """Post-procesador REGEX que limpia artefactos de IA del contenido generado."""
    if not text:
        return text
    
    # 0. ELIMINAR markdown code fences que envuelven el artículo
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
    
    # 1. ELIMINAR frases de chatbot al inicio del texto
    chatbot_patterns = [
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
    for pattern in chatbot_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    # 2. ELIMINAR meta-comentarios del sistema
    text = re.sub(r'\*?No (?:hay )?(?:additional )?dat(?:a|os)(?: adicionales?)? (?:available|disponibles?)\.?\*?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\*?No se (?:encontraron|pudieron encontrar) datos\.?\*?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'The research doesn\'t mention.*?\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'I couldn\'t find.*?\.', '', text, flags=re.IGNORECASE)
    
    # 3. ELIMINAR [cite: X] markers de NotebookLM
    text = re.sub(r'\s*\[cite:\s*\d+(?:,\s*\d+)*\]', '', text)
    
    # 4a. ELIMINAR URLs de Google Grounding API en formato markdown [anchor](vertexaisearch...)
    text = re.sub(
        r'\[([^\]]+)\]\(https://vertexaisearch\.cloud\.google\.com[^)]*\)',
        r'**\1**',
        text
    )
    
    # 4b. ELIMINAR naked vertexaisearch URLs (sin anchor, sueltas en el texto o entre corchetes)
    #     Patrón: [https://vertexaisearch...] o (https://vertexaisearch...) suelta
    text = re.sub(
        r'\[https://vertexaisearch\.cloud\.google\.com[^\]]*\]',
        '',
        text
    )
    text = re.sub(
        r'\(https://vertexaisearch\.cloud\.google\.com[^)]*\)',
        '',
        text
    )
    # 4c. ELIMINAR naked vertexaisearch URLs inline (sin corchetes ni paréntesis)
    text = re.sub(
        r'https://vertexaisearch\.cloud\.google\.com\S*',
        '',
        text
    )
    
    # 5. ELIMINAR URLs de Google Search/Scholar usadas como placeholder
    text = re.sub(
        r'\[([^\]]+)\]\(https?://(?:scholar\.)?google\.com/search[^)]*\)',
        r'**\1**',
        text
    )
    
    # 6. ELIMINAR links con URLs vacías o inválidas
    text = re.sub(
        r'\[([^\]]+)\]\(\s*\)',
        r'\1',
        text
    )
    
    # 7. ELIMINAR links donde el href es texto plano (no URL)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: m.group(0) if m.group(2).startswith(('http', '/', '#')) else m.group(1),
        text
    )
    
    # 8. LIMPIAR H1 sueltos (solo debería haber H2+)
    text = re.sub(r'^# .+$', '', text, flags=re.MULTILINE)
    
    # 9. ELIMINAR referencias con corchetes huérfanos [source name] que no son links
    text = re.sub(r'\[([^\]]{3,80})\](?!\()', r'**\1**', text)
    
    # 10. LIMPIAR la basura que queda al eliminar URLs (dobles espacios, paréntesis huérfanos)
    text = re.sub(r'\(\s*\)', '', text)  # paréntesis vacíos
    text = re.sub(r'  +', ' ', text)  # dobles espacios
    
    # 11. ELIMINAR líneas en blanco excesivas (máximo 2 seguidas)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    print("   🧹 [Post-Processor] Contenido limpiado de artefactos de IA")
    return text.strip()

def escribir_blueprint(tutorial_data, lang="en"):
    """Genera el post de herramienta reescribiendo con personalidad según idioma."""
    print(f"🛠️ Escribiendo Blueprint ({lang.upper()}): {tutorial_data['title']}...")
    
    prompt_base = PROMPT_BLUEPRINT_EN if lang == "en" else PROMPT_BLUEPRINT_ES
    
    prompt = prompt_base.format(
        title=tutorial_data['title'],
        transcript=tutorial_data['transcript'][:30000]
    ) + f"\n{SYSTEM_FORMAT_RULES}"
    
    # === TRINITY: Misma lógica de motores aislados ===
    if lang == "es":
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return resp.text.strip()
    else:
        return _call_en_engine(prompt)

def guardar_post(meta, contenido, lang, category, forced_image=None, translation_key=None):
    """Guarda el post con imagen validada y frontmatter blindado."""
    # Lógica Blindada de Silos: content/{lang}/{category}
    output_dir = f"content/{lang}/{category}"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = f"{output_dir}/{meta['slug']}.md"
    
    # Lógica de Imagen: Si viene forzada, se usa. Si no, se genera.
    imagen = forced_image if forced_image else get_image(meta['titulo'], meta['slug'], category)
    
    # VALIDACIÓN BLINDADA: Si la imagen es una URL externa o vacía, usar fallback local
    if not imagen or imagen.startswith("http"):
        print(f"   ⚠️ Imagen inválida detectada: '{imagen}'. Usando fallback local...")
        imagen = f"/images/defaults/default-{category}.jpg"
        print(f"   🛡️ Fallback aplicado: {imagen}")
    
    now = datetime.now()
    backdate = random.randint(15, 30) if lang == 'es' else random.randint(2, 10)
    date_str = (now - timedelta(minutes=backdate)).strftime("%Y-%m-%dT%H:%M:%S")
    # Generación inteligente de meta description (Fenix V3: evita descriptions genéricas)
    try:
        desc_prompt = f"Write a unique, compelling meta description of EXACTLY 140-155 characters in {'Spanish' if lang == 'es' else 'English'} for an article titled '{meta['titulo']}'. Output ONLY the description text, nothing else. No quotes around it."
        desc_resp = client.models.generate_content(model='gemini-2.0-flash', contents=desc_prompt)
        raw_desc = desc_resp.text.strip().replace('"', "'")
        # Truncar en frontera de palabra (no cortar a mitad de palabra)
        if len(raw_desc) > 160:
            clean_text = raw_desc[:157].rsplit(' ', 1)[0] + '...'
        else:
            clean_text = raw_desc
    except Exception:
        clean_text = re.sub(r'[#*]', '', contenido)[:160].replace('\n', ' ').replace('"', "'") + "..."
    
    # BLINDAJE: Nunca dejar description vacía
    if not clean_text or len(clean_text.strip()) < 20:
        clean_text = re.sub(r'[#*\[\]]', '', contenido)[:155].replace('\n', ' ').replace('"', "'").strip() + "..."
        print(f"   🛡️ [Description Blindaje] Fallback desde contenido: {clean_text[:50]}...")
    
    # Resolver nombre legible de la categoría (FIX: config['name'] → NICHES lookup)
    niche_info = NICHES.get(category, {})
    niche_name = niche_info.get("name", category.capitalize())
    
    # Frontmatter YAML limpio y validado
    front_matter = f"""---
title: "{meta['titulo'].replace('"', '')}"
date: {date_str}
draft: false
description: "{clean_text}"
featured_image: "{imagen}"
tags: ["{niche_name}"]
categories: ["{category}"]
type: "{category}"
language: "{lang}"
translationKey: "{translation_key}"
---

![{meta['titulo'].replace('"', '')}]({imagen})

{contenido}
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter)
    print(f"✅ Guardado: {filepath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, required=True, help='Category or tools')
    parser.add_argument('--lang', type=str, choices=['es', 'en'], default=None, help='Force language: es (Spain) or en (US)')
    args = parser.parse_args()
    cat = args.category.lower()
    forced_lang = args.lang
    
    # --- MODO TOOLS ---
    if cat == "tools":
        print("🚀 INICIANDO BLUEPRINT ENGINE")
        
        # SIEMPRE "IA" para herramientas técnicas como Make.com
        target_niche = "ia" 
        print(f"🎲 Nicho forzado para prueba: {target_niche}")
        
        # Buscamos "Make.com automation" explícitamente en esta prueba para garantizar calidad
        tutorial = tools_hunter.ToolsHunter.get_tutorial_content("Make.com automation")
        
        if not tutorial:
            print("💤 No tutorial found.")
            return
            
        # 1. GENERACIÓN DE IMAGEN MAESTRA (ÚNICA)
        print(f"🎨 Generando Imagen Maestra para: {tutorial['title']}...")
        master_slug = SlugManager.generate(tutorial['title'])
        # Usamos nicho 'tools' o 'ia' para el estilo visual
        master_image = get_image(tutorial['title'], master_slug, "tools")
            
        # 2. Generación Bilingüe
        for lang in ["en", "es"]:
            texto = escribir_blueprint(tutorial, lang)
            
            # Título Inteligente (IA)
            prompt_title = f"GENERATE A CLICKBAIT TITLE IN {lang.upper()} FOR: {tutorial['title']}. OUTPUT ONLY THE TITLE TEXT. NO 'Option 1'."
            resp_title = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_title)
            
            # Sanitización estricta (Python layer)
            raw_title = resp_title.text.strip().split('\n')[0]
            final_title = SlugManager.sanitize(raw_title)
            
            slug = SlugManager.generate(final_title)
            
            meta = {"titulo": final_title, "slug": slug}
            # INYECCIÓN DE IMAGEN MAESTRA
            guardar_post(meta, texto, lang, "tools", forced_image=master_image)
            
        return

    # --- MODO STANDARD ---
    if cat not in NICHES:
        print(f"❌ Categoría inválida.")
        return

    print(f"🚀 INICIANDO PENTAGON: {NICHES[cat]['name']}")
    
    # --- RELAY-RACE V2: Leer temas pre-investigados del Scout ---
    # Buscar primero el JSON con sufijo de idioma (nuevo), luego sin sufijo (viejo)
    tema = None
    tema_lang = forced_lang  # Si viene de CLI, ya sabemos el idioma
    
    if forced_lang:
        trends_file = f"data/trends_{cat}_{forced_lang}.json"
    else:
        trends_file = f"data/trends_{cat}.json"
    
    # Fallback: si no existe el archivo con sufijo, probar sin sufijo
    if not os.path.exists(trends_file) and forced_lang:
        fallback_file = f"data/trends_{cat}.json"
        if os.path.exists(fallback_file):
            trends_file = fallback_file
            print(f"   🔄 [Relay-Race] Fichero con sufijo no encontrado, usando fallback: {trends_file}")
    
    if os.path.exists(trends_file):
        print(f"   📂 [Relay-Race] Leyendo temas pre-investigados: {trends_file}")
        try:
            with open(trends_file, 'r', encoding='utf-8') as f:
                trends_data = json.load(f)
            
            topics = trends_data.get("topics", [])
            scouted_at = trends_data.get("scouted_at", "")
            json_lang = trends_data.get("lang", None)
            print(f"   📋 {len(topics)} temas disponibles (scouted: {scouted_at[:19]}, lang: {json_lang})")
            
            # Buscar el primer tema que pase safety check y no sea redundante
            for t in topics:
                candidate = t.get("title", "")
                if not candidate:
                    continue
                if not safety_check(candidate):
                    print(f"   ⚠️ Tema '{candidate}' falló safety check. Saltando...")
                    continue
                if is_topic_redundant(candidate, cat):
                    print(f"   🔄 Tema '{candidate}' es redundante. Saltando...")
                    continue
                tema = candidate
                # El idioma viene del CLI o del JSON del topic
                if not tema_lang:
                    tema_lang = t.get("lang", json_lang or "es")
                print(f"   ✅ [Relay-Race] Tema seleccionado: {tema} [{tema_lang.upper()}]")
                break
            
            # Limpiar el JSON después de leer (evitar reusar temas viejos)
            if tema:
                os.remove(trends_file)
                print(f"   🗑️ [Relay-Race] {trends_file} consumido y eliminado")
                
        except Exception as e:
            print(f"   ⚠️ [Relay-Race] Error leyendo {trends_file}: {e}. Cayendo a TrendHunter...")
    
    # --- FALLBACK: TrendHunter clásico si no hay JSON o no hay temas válidos ---
    if not tema:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print("🛑 [Relay-Race] Ejecución en GitHub Actions: no hay JSON válido. EXIT 1 para detener la cadena.")
            sys.exit(1)
            
        print(f"   🔄 [Fallback] Usando TrendHunter clásico...")
        for topic_attempt in range(5):
            candidate = trend_hunter.TrendHunter.get_trend(cat)
            if not candidate:
                print(f"   ⚠️ [Intento {topic_attempt+1}/5] TrendHunter no devolvió tema. Reintentando...")
                continue
            if not safety_check(candidate):
                print(f"   ⚠️ [Intento {topic_attempt+1}/5] Tema '{candidate}' falló safety check. Reintentando...")
                continue
            if is_topic_redundant(candidate, cat):
                print(f"   🔄 [Intento {topic_attempt+1}/5] Tema '{candidate}' es redundante. Reintentando...")
                continue
            tema = candidate
            tema_lang = random.choice(["es", "en"])
            break
    
    if not tema:
        print(f"🚫 ABORTADO: No se encontró tema válido para '{cat}'.")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            sys.exit(1)
        return
    
    print(f"🎯 TEMA: {tema} | IDIOMA ORIGEN: {tema_lang.upper()}")
    res = researcher.Researcher()
    # Generar Translation Key única (aunque sea monolingüe, Hugo la usa por si después hay traducción manual)
    trans_key = str(uuid.uuid4())
    
    # === AISLAMIENTO: Variables limpias por idioma ===
    meta = None
    texto = None
    contexto = None
    
    print(f"   🌐 [Relay-Race] Ejecutando tubería nativa SOLO para audiencia: {tema_lang.upper()}")
    
    # V5 GEO-RESEARCH: Investigar Específicamente por Idioma Autóctono
    contexto = res.research_topic(
        topic=tema,
        category=cat,
        search_context=NICHES[cat].get('search_context', ''),
        lang=tema_lang
    )
    
    meta = planificar_articulo(tema, contexto, tema_lang, NICHES[cat])
    texto = escribir_articulo(meta, contexto, tema_lang, NICHES[cat], category=cat)
    guardar_post(meta, texto, tema_lang, cat, translation_key=trans_key)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
