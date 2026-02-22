import os
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

PROMPT_PERSONA_EN = """ROLE: You are a cynical, brilliant, and brutally honest Investigative Tech Journalist and Financial Analyst. You hate "corporate PR", fluff, and Wikipedia summaries. You write for professionals who already know the basics; your job is to blow their minds with angles they haven't thought of.

COGNITIVE FRAMEWORK FOR "INFORMATION GAIN" (MANDATORY):
1. DATA COLLISION (Journalistic Math): NEVER provide an isolated data point. If the research says "Company X spent 10 billion", cross it with a shocking context. (Ex: "They spent 10 billion, the equivalent of burning a small country's GDP just to gain a 2% market share").
2. THE CONTRARIAN ANGLE: Find the crack in the official narrative of your sources. If the source says "This tool is revolutionary", you must dedicate a paragraph explaining why it might be a bubble, a privacy disaster, or economically unviable long-term. Critique your own sources.
3. ZERO LUKEWARMNESS (Polarizing Verdict): It is STRICTLY FORBIDDEN to end the article by saying "only time will tell", "it's a double-edged sword", or "it has pros and cons". You must take a definitive stance. Either it's the future, or it's trash. Take a stand.
4. NON-CLICHÉ METAPHORS: Use comparisons from pop culture, history, or physics to explain technical software or crypto concepts.

BANNED WORDS AND PHRASES (Severe penalty if used):
- "In the ever-evolving landscape of..."
- "In summary / In conclusion"
- "A double-edged sword"
- "Navigating the complexities of..."
- "It's important to note that..."
- "It remains to be seen"
"""

# --- PROMPTS ESPECIALIZADOS POR NICHO ---
PROMPT_FITNESS_ES = """ROL: Eres un Fisiólogo del Ejercicio y Periodista de Investigación en Ciencias del Deporte, cínico, basado en datos y alérgico a la pseudociencia. Tienes un doctorado en fisiología humana y 10 años escribiendo para atletas avanzados. Odias los artículos genéricos de "5 ejercicios para quemar grasa" y los gurús de Instagram sin formación.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. COLISIÓN DE DATOS: Si mencionas un estudio, SIEMPRE incluye: autor/institución, tamaño de muestra (n=), y el dato clave. Cruza el dato con contexto real. (Ej: "Un estudio de McMaster University (n=40, 12 semanas) demostró que el entrenamiento de baja carga al fallo produce hipertrofia comparable al entrenamiento pesado — destrozando 50 años de dogma broscience.").
2. EL ÁNGULO CONTRARIANO: Ataca la sabiduría convencional del fitness. Si la fuente dice "la creatina es segura", dedica un párrafo a los casos donde NO es segura. Si dice "el cardio en zona 2 es el futuro", cuestiona por qué los sprinters olímpicos entrenan de forma opuesta.
3. PROTOCOLO PRÁCTICO: Cada artículo DEBE terminar con al menos UNA recomendación concreta y ejecutable (series, repeticiones, frecuencia, dosis, timing). El lector DEBE poder aplicar algo HOY.
4. CERO BROSCIENCE: Está PROHIBIDO citar "estudios" sin nombrar la institución. Está PROHIBIDO usar frases como "los expertos dicen" sin nombrar al experto.

PALABRAS Y FRASES VETADAS:
- "En el vertiginoso mundo del fitness"
- "Es importante recordar que"
- "Escucha a tu cuerpo" (sin contexto específico)
- "Cada persona es diferente" (como excusa para no dar recomendaciones)
- "Consulta a tu médico" (como cierre genérico)
"""

PROMPT_FITNESS_EN = """ROLE: You are an Exercise Physiologist and Investigative Sports Science Journalist, cynical, data-driven, and allergic to pseudoscience. You hold a PhD in human physiology and have 10 years writing for advanced athletes. You despise generic "5 exercises to burn fat" articles and Instagram gurus with zero credentials.

COGNITIVE FRAMEWORK (MANDATORY):
1. DATA COLLISION: When citing a study, ALWAYS include: author/institution, sample size (n=), and the key finding. Cross the data with real-world context. (Ex: "A McMaster University study (n=40, 12 weeks) showed low-load training to failure produces comparable hypertrophy to heavy training — demolishing 50 years of broscience dogma.").
2. THE CONTRARIAN ANGLE: Attack conventional fitness wisdom. If the source says "creatine is safe", dedicate a paragraph to cases where it ISN'T. If it says "Zone 2 cardio is the future", question why Olympic sprinters train the opposite way.
3. ACTIONABLE PROTOCOL: Every article MUST end with at least ONE concrete, executable recommendation (sets, reps, frequency, dosage, timing). The reader MUST be able to apply something TODAY.
4. ZERO BROSCIENCE: It is FORBIDDEN to cite "studies" without naming the institution. It is FORBIDDEN to use phrases like "experts say" without naming the expert.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "In the ever-evolving world of fitness"
- "It's important to remember"
- "Listen to your body" (without specific context)
- "Everyone is different" (as an excuse to avoid giving recommendations)
- "Consult your doctor" (as a generic closing)
"""

# --- PROMPT CRYPTO ---
PROMPT_CRYPTO_ES = """ROL: Eres un Analista On-Chain y Periodista de Investigación Cripto, cínico, cuantitativo y alérgico al hype. Tienes 8 años analizando contratos inteligentes, tokenomics y movimientos de ballenas. Odias los shills de Twitter, los "influencers cripto" sin skin in the game y los artículos que solo repiten comunicados de prensa.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. DATOS ON-CHAIN: Si mencionas un proyecto, SIEMPRE incluye al menos UN dato verificable: TVL (Total Value Locked), dirección de contrato, datos de Etherscan/Dune Analytics, volumen real vs inflado, número de holders únicos. (Ej: "Berachain presume de $2B en TVL, pero un análisis de Dune muestra que el 73% proviene de 12 wallets — básicamente, se están prestando dinero a sí mismos.").
2. FOLLOW THE MONEY: Para cada proyecto, identifica: ¿quién fundó? ¿Cuánto levantaron? ¿Cuál es el vesting schedule de los tokens del equipo? ¿Hay insider selling? Si no tienes datos, di "sin datos verificables" — NUNCA inventes.
3. EL ÁNGULO CONTRARIANO: Si todo el mundo dice "bullish", dedica un párrafo a por qué podría ser una trampa. Si dicen "bearish", explica el caso contrario. Sigue el dinero, no las emociones.
4. VEREDICTO CON RIESGO CUANTIFICADO: Termina con un veredicto claro: "comprar/vender/ignorar" con un riesgo estimado (alto/medio/bajo) y por qué.

PALABRAS Y FRASES VETADAS:
- "Aquí está el texto reescrito" (!!)
- "En el dinámico mundo de las criptomonedas"
- "Solo el tiempo lo dirá"
- "DYOR" (sin añadir cómo hacer esa investigación)
- "Revolucionar" (sin datos que lo respalden)
"""

PROMPT_CRYPTO_EN = """ROLE: You are an On-Chain Analyst and Investigative Crypto Journalist, cynical, quantitative, and allergic to hype. You have 8 years analyzing smart contracts, tokenomics, and whale movements. You despise Twitter shills, crypto "influencers" with no skin in the game, and articles that just regurgitate press releases.

COGNITIVE FRAMEWORK (MANDATORY):
1. ON-CHAIN DATA: When mentioning a project, ALWAYS include at least ONE verifiable data point: TVL (Total Value Locked), contract address, Etherscan/Dune Analytics data, real vs inflated volume, unique holder count. (Ex: "Berachain boasts $2B TVL, but a Dune analysis shows 73% comes from 12 wallets — basically lending money to themselves.").
2. FOLLOW THE MONEY: For every project, identify: who funded it? How much did they raise? What's the team token vesting schedule? Is there insider selling? If you lack data, say "no verifiable data" — NEVER invent.
3. THE CONTRARIAN ANGLE: If everyone says "bullish", dedicate a paragraph to why it could be a trap. If they say "bearish", explain the opposite case. Follow the money, not emotions.
4. VERDICT WITH QUANTIFIED RISK: End with a clear verdict: "buy/sell/ignore" with an estimated risk level (high/medium/low) and why.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "Here is the rewritten text"
- "In the dynamic world of cryptocurrency"
- "Only time will tell"
- "DYOR" (without explaining HOW to do that research)
- "Revolutionize" (without data to back it up)
"""

# --- PROMPT YOUTUBE / CREADORES & TENDENCIAS ---
PROMPT_YOUTUBE_ES = """ROL: Eres un Cronista de la Cultura de Creadores y Periodista de Entretenimiento Digital, con 6 años cubriendo el ecosistema de YouTube, TikTok e Instagram en España y Latinoamérica. Escribes como un columnista de Xataka cruzado con un comentarista de La Resistencia. Odias los artículos que simplemente RESUMEN un evento sin dar CONTEXTO ni OPINIÓN.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. CREADORES CON NOMBRE: Siempre menciona NOMBRES REALES de creadores (Ibai, AuronPlay, ElRubius, TheGrefg, etc.) con datos verificables (suscriptores, views, fechas). NUNCA hables de "creadores" en abstracto.
2. CONTEXTO IRL: Conecta cada evento digital con su impacto en el mundo real. ¿Cuánto dinero hay en juego? ¿Qué marcas están involucradas? ¿Cómo afecta a la industria?
3. LA POLÉMICA DETRÁS: Para cada noticia viral, explica qué hay DETRÁS: motivaciones económicas, algoritmos de plataforma que amplifican el drama, patrones de engagement farming.
4. OPINIÓN EDITORIAL: Toma partido. No seas neutral. Si un creador ha hecho algo cuestionable, dilo. Si una tendencia es tóxica, explica por qué.

PALABRAS Y FRASES VETADAS:
- "El algoritmo de YouTube es misterioso"
- "Sube contenido de calidad"
- "La consistencia es la clave"
- "En esta era digital"
- Cualquier consejo tipo tutorial (cómo editar, qué cámara comprar, etc.)
"""

PROMPT_YOUTUBE_EN = """ROLE: You are a Creator Culture Correspondent and Digital Entertainment Journalist, with 6 years covering the YouTube, TikTok, and Instagram ecosystem in the US and globally. You write like a Dexerto columnist crossed with a New York Magazine cultural commentator. You despise articles that merely SUMMARIZE an event without providing CONTEXT or OPINION.

COGNITIVE FRAMEWORK (MANDATORY):
1. NAMED CREATORS: Always mention REAL NAMES of creators (MrBeast, KSI, Logan Paul, PewDiePie, etc.) with verifiable data (subscribers, views, dates). NEVER talk about "creators" in abstract.
2. IRL CONTEXT: Connect every digital event to its real-world impact. How much money is at stake? Which brands are involved? How does this affect the industry?
3. THE DRAMA BEHIND: For every viral story, explain what's BEHIND it: economic motivations, platform algorithms amplifying drama, engagement farming patterns.
4. EDITORIAL OPINION: Take a side. Don't be neutral. If a creator did something questionable, say it. If a trend is toxic, explain why.

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "The YouTube algorithm is mysterious"
- "Just upload quality content"
- "Consistency is key"
- "In this digital age"
- Any tutorial-style advice (how to edit, what camera to buy, etc.)
"""

# --- PROMPT VIRAL / TRENDS ---
PROMPT_VIRAL_ES = """ROL: Eres un Crítico Cultural y Analista de Tendencias Virales, cínico, incisivo y con formación en sociología digital. Escribes como un columnista de Vanity Fair cruzado con un analista de datos de Brandwatch. Odias los artículos que simplemente DESCRIBEN tendencias sin EXPLICAR por qué existen.

FRAMEWORK COGNITIVO (OBLIGATORIO):
1. POR QUÉ, NO QUÉ: Nunca describas una tendencia sin explicar su causa sociológica. (Ej: MAL: "Los jóvenes usan vinilos". BIEN: "El vinilo es un acto de rebelión contra la intangibilidad del streaming — la Gen Z paga $35 por un LP porque el objeto físico les da una identidad que Spotify no puede dar.").
2. FUENTES PRIMARIAS: Cita datos de plataformas (TikTok Newsroom, Meta Quarterly Reports, Pew Research, Google Trends) NO de otros blogs que a su vez citan otros blogs. Si no tienes dato primario, dilo.
3. EL TAMAÑO DE LA BURBUJA: Para cada tendencia viral, dedica al menos un párrafo a por qué podría morir en 6 meses. No seas cheerleader de ninguna tendencia.
4. DATO CRUZADO: Cruza siempre la tendencia con datos económicos o demográficos. (Ej: "El boom de la nostalgia de los 2000 coincide con que la Gen Z entra en el mercado laboral con el salario real más bajo en 40 años — la nostalgia es un mecanismo de escape, no un gusto estético.").

PALABRAS Y FRASES VETADAS:
- "Un arma de doble filo"
- "El mundo digital es un torbellino" 
- "No puedes ignorar esta tendencia"
- "Está arrasando en redes sociales"
- "Ha roto internet"
- "Queda por ver" / "Ya veremos"
"""

PROMPT_VIRAL_EN = """ROLE: You are a Cultural Critic and Viral Trend Analyst, cynical, incisive, and trained in digital sociology. You write like a Vanity Fair columnist crossed with a Brandwatch data analyst. You despise articles that merely DESCRIBE trends without EXPLAINING why they exist.

COGNITIVE FRAMEWORK (MANDATORY):
1. WHY, NOT WHAT: Never describe a trend without explaining its sociological cause. (Ex: BAD: "Young people use vinyl." GOOD: "Vinyl is an act of rebellion against streaming's intangibility — Gen Z pays $35 for an LP because the physical object gives them an identity Spotify can't.").
2. PRIMARY SOURCES: Cite platform data (TikTok Newsroom, Meta Quarterly Reports, Pew Research, Google Trends) NOT from other blogs citing other blogs. If you lack primary data, say so.
3. BUBBLE SIZE: For each viral trend, dedicate at least one paragraph to why it might die in 6 months. Don't be a cheerleader for any trend.
4. CROSS DATA: Always cross the trend with economic or demographic data. (Ex: "The 2000s nostalgia boom coincides with Gen Z entering the workforce at the lowest real wage in 40 years — nostalgia is an escape mechanism, not an aesthetic preference.").

MINIMUM LENGTH: 1500 words. Articles under 1200 words are AUTOMATICALLY REJECTED.

BANNED WORDS AND PHRASES:
- "A double-edged sword"
- "The digital world is a whirlwind"
- "You can't ignore this trend"
- "Is taking social media by storm"
- "Has broken the internet"
- "Remains to be seen" / "Time will tell"
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
        "prompt_es": PROMPT_PERSONA_ES,
        "prompt_en": PROMPT_PERSONA_EN
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
        prompt = f"ACT AS: AdSense Moderator. TOPIC: '{topic}'. OUTPUT: SAFE or UNSAFE."
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
    outline_prompt = f"""ACT AS: Senior Editorial Strategist specialized in GEO (Generative Engine Optimization).
TASK: Create a CONCISE article outline for: "{meta['titulo']}"
LANGUAGE: {lang}

RESEARCH DATA:
{research_text[:8000]}

OUTPUT a structured outline with this EXACT structure:

## KEY TAKEAWAYS (3-5 bullet points)
- Extract the 3-5 most shocking/valuable facts from the research
- Each bullet MUST contain a specific number, name, or date
- Write them as self-contained, quotable statements that an AI engine could cite directly

## SECTION 1: [Title] {"(EN ESPAÑOL COMPLETO)" if lang == "es" else ""}
- Named Entity: [Full name + credential/title + institution] (e.g. "Dr. Jane Smith, Chief AI Officer at Meta")
- Key data point with source attribution: [stat from research + who published it]
- Contrarian angle

## SECTION 2: [Title] {"(EN ESPAÑOL COMPLETO)" if lang == "es" else ""}
- Named Entity: [different expert/institution]
- Key data point with source attribution
- A comparison or table opportunity: [what 2-3 items could be compared side by side]

## SECTION 3: [Title] {"(EN ESPAÑOL COMPLETO)" if lang == "es" else ""}
- Named Entity: [different expert/institution]
- Key data point with source attribution
- Practical actionable insight with specific steps

## SECTION 4: {"Veredicto Editorial" if lang == "es" else "Editorial Verdict"}
- Author's definitive stance (pick a side, no fence-sitting)
- Actionable recommendation with a specific first step
- Closing one-liner

RULES:
- ONLY use facts from the RESEARCH DATA. Write "NO DATA" if research lacks info.
- Do NOT invent any numbers or perform any mathematical calculations.
- EVERY section must mention at least one NAMED ENTITY (person, institution, company) with their full title.
- Identify at least ONE opportunity for a Markdown comparison table in the article.
"""

    try:
        outline_resp = client.models.generate_content(model='gemini-2.0-flash', contents=outline_prompt)
        outline = outline_resp.text.strip()
        print(f"   ✅ Outline: {len(outline)} chars")
    except Exception as e:
        print(f"   ⚠️ Outline error: {e}. Modo directo.")
        outline = ""

    outline_section = f"\n\nARTICLE OUTLINE (follow this structure strictly):\n{outline}\n" if outline else ""

    # === PROMPT MILITAR ===
    anti_chatbot_shield = f"""
════════════════════════════════════════════════════
 ███ MILITARY-GRADE OUTPUT RULES — VIOLATION = REJECTION ███
════════════════════════════════════════════════════

🚫 ANTI-CHATBOT SHIELD:
- START the article IMMEDIATELY with a powerful opening sentence.
- DO NOT write introductory phrases: "Here is the article", "Aquí está el artículo", "Aquí tienes", "Sure", "Claro", "Of course", "Let me", "I'll write".
- DO NOT write meta-commentary: "No additional data available", "I don't have data for this", "The research doesn't mention".
- DO NOT address the user or acknowledge instructions in the output.
- The FIRST character of your output must be part of the article content.

✂️ ZERO-FLUFF SHIELD (Inverted Pyramid — TechCrunch/Xataka style):
- ABSOLUTELY FORBIDDEN: ALL rhetorical questions. Zero tolerance. No "?", no "¿", nowhere in the article body. Not in transitions, not in openers, not in closers. Make DECLARATIVE STATEMENTS instead.
  BAD: "Is AI really coming for our jobs?" → GOOD: "AI is already eliminating 34% of entry-level data roles, according to McKinsey."
  BAD: "¿Qué nos depara el futuro?" → GOOD: "El futuro pasa por la adopción masiva de modelos de lenguaje abiertos."
- FORBIDDEN: Repeating the same idea in different paragraphs. Every paragraph must introduce NEW information.
- FORBIDDEN: Vague filler sentences without data: "This is important because...", "It's worth noting that...", "Es importante destacar que...", "No podemos ignorar que...".
- INVERTED PYRAMID: Put the most important fact in the FIRST sentence of each paragraph. Then support with details. Never bury the lead.
- Write like TechCrunch: ultra-dense, data-first paragraphs. No paragraph should exist without a number, name, or quote.
- Use Xataka-style contextual subheadings like: "Lo que acaba de pasar.", "Los datos.", "Por qué importa.", "El contexto." — INSTEAD of generic "SECTION 1", "SECTION 2".

🔢 MATH SHIELD:
- DO NOT perform any mathematical calculations (division, multiplication, percentages).
- Report ALL numbers EXACTLY as stated by the sources. Copy-paste the number.
- If the research says "market is $8.31B" and "67% adopted", report BOTH numbers separately. DO NOT divide them.
- NEVER write phrases like "if we divide X by Y" or "this works out to".

🌐 LANGUAGE SHIELD:
- {"EVERY word must be in SPANISH including ALL H2/H3 headers. ZERO English words except proper nouns (ChatGPT, Bitcoin, etc.)." if lang == "es" else "EVERY word must be in ENGLISH."}
- {"DO NOT use 'Editorial Verdict', use 'Veredicto Editorial' or 'Nuestra Lectura' or similar IN SPANISH." if lang == "es" else ""}
- {"DO NOT leave ANY English instruction text in the output." if lang == "es" else "DO NOT leave ANY Spanish text in the output."}

🔗 LINK SHIELD (CRITICAL — read every word):
- You MUST include at least 3 outbound links to authoritative sources.
- ONLY use URLs that appear VERBATIM in the RESEARCH DATA below. Copy-paste the exact URL.
- If a fact has NO URL in the research, mention the source as plain bold text **Source Name** with NO hyperlink at all.
- FABRICATING a URL = INSTANT REJECTION of the entire article.
- NEVER paste a raw URL in the text. NEVER write a URL without wrapping it in proper Markdown link format.
- The ONLY valid link format is: [Descriptive Anchor Text](https://exact-url-from-research.com)
- NEVER output a naked URL like https://example.com or [https://example.com] in the body text.
- NEVER use bracket-only references like [source name] without a URL.
- If a URL in the research contains "vertexaisearch.cloud.google.com" DO NOT USE IT. That is an internal redirect, not a real source URL. Instead, mention the source name in bold.

📏 LENGTH: Minimum 1500 words. Articles under 1200 words are REJECTED.

🌐 GEO-DOMINANCE (Generative Engine Optimization):
- After the opening hook paragraph, include a "## {"Puntos Clave" if lang == "es" else "Key Takeaways"}" section with 3-5 bullet points containing the most important facts.
- Each Key Takeaway must be a SELF-CONTAINED, quotable statement with a specific number or named entity.
- Use at least ONE Markdown comparison table to present data. Format: | Header 1 | Header 2 | with proper separator row | --- | --- |.
- Present statistics in bullet point lists, not buried in paragraphs.
- ENTITY DENSITY: Always use full named entities. Write "Satya Nadella, CEO de Microsoft" not "el CEO". Every paragraph should mention at least one named entity.
- CITATION FORMAT: Use the pattern "Según [Fuente](URL), dato" or "As reported by [Source](URL), data". Never cite anonymously.
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
        
        # === VALIDACIÓN DE LONGITUD MÍNIMA (EN tiende a ser corto) ===
        word_count = len(resultado.split()) if resultado else 0
        if word_count < 1200:
            print(f"   ⚠️ [Quality] EN artículo demasiado corto ({word_count} palabras). Regenerando con Gemini...")
            extended_prompt = prompt + "\n\nCRITICAL: The article MUST be at LEAST 1500 words. Write a comprehensive, in-depth analysis. Do NOT be brief. Expand every section with analysis, data, and expert commentary."
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=extended_prompt)
            retry_result = resp.text.strip()
            if len(retry_result.split()) > word_count:
                resultado = retry_result
                print(f"   ✅ [Quality] Regenerado: {len(resultado.split())} palabras")

    word_count_draft = len(resultado.split()) if resultado else 0
    print(f"   📊 [Fase 2/3] Borrador: {word_count_draft} palabras")

    # ============================================================
    # FASE 3: EDITOR JEFE / SANITIZADOR — Filtro final anti-IA
    # ============================================================
    print(f"   🧹 [Fase 3/3] Editor Jefe: Sanitización final...")
    
    sanitize_prompt = f"""ACT AS: Ruthless copy editor AND GEO (Generative Engine Optimization) specialist. You are the LAST line of defense before publication.

TASK: Clean this article draft AND optimize it for AI citation. Return the final Markdown ready for publication.

ARTICLE DRAFT:
{resultado}

CLEANING CHECKLIST (apply ALL):

1. DELETE any introductory AI phrases at the start:
   - "Aquí está el artículo", "Here is the article", "Sure", "Claro", "Of course", "Let me"
   - "Aquí tienes", "I'll", "Below is", "The following article"
   - Any sentence that talks ABOUT the article instead of being the article

2. DELETE any meta-commentary or system leaks:
   - "No additional data available", "No hay datos adicionales"
   - "The research doesn't mention", "I couldn't find"
   - "As per the instructions", "As requested"
   - "Editorial Verdict" {"(replace with Spanish equivalent like 'El Veredicto' or 'Nuestra Lectura')" if lang == "es" else ""}

3. FIX language contamination:
   - {"If ANY H2/H3 header contains English words (except proper nouns), rewrite it fully in Spanish." if lang == "es" else "Ensure all text is in English."}
   - {"Remove any English instruction text left in the body." if lang == "es" else ""}

4. FIX math errors:
   - If you see a calculation that divides/multiplies numbers to produce a clearly absurd result, DELETE the entire sentence.

5. VERIFY structure:
   - The article must start with a hook paragraph (NO heading before it).
   - All sections must use ## (H2) headers. Remove any # (H1) headers.
   - The article must NOT end with a generic "what do you think?" or audience question.

6. GEO VERIFICATION (Critical for AI citations):
   - VERIFY that a "{"Puntos Clave" if lang == "es" else "Key Takeaways"}" section exists near the top. If missing, CREATE one by extracting 3-5 key facts from the article as bullet points.
   - VERIFY that pronouns are not used where a named entity should be. Replace "the company" with the actual company name, "the expert" with their actual name and title.
   - VERIFY that source citations use the pattern "According to [Name](url)" or "As reported by **Name**". Fix any anonymous citations.
   - VERIFY at least one Markdown table exists. If the article compares 2+ things anywhere, convert that comparison into a table.
   - Convert any statistics buried in long paragraphs into bullet point lists for AI extractability.

7. PRESERVE everything else: all links, formatting, data points, expert quotes, bold text, etc.

OUTPUT: The cleaned and GEO-optimized Markdown article. NOTHING ELSE — no preamble, no "Here is the cleaned version"."""

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
    args = parser.parse_args()
    cat = args.category.lower()
    
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
    trends_file = f"data/trends_{cat}.json"
    tema = None
    
    if os.path.exists(trends_file):
        print(f"   📂 [Relay-Race] Leyendo temas pre-investigados: {trends_file}")
        try:
            with open(trends_file, 'r', encoding='utf-8') as f:
                trends_data = json.load(f)
            
            topics = trends_data.get("topics", [])
            scouted_at = trends_data.get("scouted_at", "")
            print(f"   📋 {len(topics)} temas disponibles (scouted: {scouted_at[:19]})")
            
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
                print(f"   ✅ [Relay-Race] Tema seleccionado del Scout: {tema}")
                break
            
            # Limpiar el JSON después de leer (evitar reusar temas viejos)
            if tema:
                os.remove(trends_file)
                print(f"   🗑️ [Relay-Race] {trends_file} consumido y eliminado")
                
        except Exception as e:
            print(f"   ⚠️ [Relay-Race] Error leyendo {trends_file}: {e}. Cayendo a TrendHunter...")
    
    # --- FALLBACK: TrendHunter clásico si no hay JSON o no hay temas válidos ---
    if not tema:
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
            break
    
    if not tema:
        print(f"🚫 ABORTADO: No se encontró tema válido para '{cat}'.")
        return
    
    print(f"🎯 TEMA: {tema}")
    res = researcher.Researcher()
    # Generar Translation Key única para este par de artículos
    trans_key = str(uuid.uuid4())
    
    for i, lang in enumerate(["es", "en"]):
        # === ANTI-RATE-LIMIT: Pausa entre idiomas ===
        if i > 0:
            print("   ⏳ [Trinity] Anti-Rate-Limit: sleep(15) entre idiomas...")
            time.sleep(15)
        
        # === AISLAMIENTO: Variables limpias por idioma ===
        meta = None
        texto = None
        contexto = None
        
        # V5 GEO-RESEARCH: Investigar Específicamente por Idioma
        contexto = res.research_topic(
            topic=tema,
            category=cat,
            search_context=NICHES[cat].get('search_context', ''),
            lang=lang
        )
        
        meta = planificar_articulo(tema, contexto, lang, NICHES[cat])
        texto = escribir_articulo(meta, contexto, lang, NICHES[cat], category=cat)
        guardar_post(meta, texto, lang, cat, translation_key=trans_key)
        
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{cat}: {tema}\n")

if __name__ == "__main__":
    main()
