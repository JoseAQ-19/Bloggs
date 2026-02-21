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
    print(f"✍️ Escribiendo ({lang}): {meta['titulo']}...")
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
    # FASE 1: OUTLINE — Extraer datos concretos de la investigación
    # Esto reduce alucinaciones porque la IA "pre-digiere" los datos
    # ============================================================
    print(f"   📋 [Fase 1] Generando outline con datos concretos...")
    
    outline_prompt = f"""ACT AS: Senior Editorial Strategist.

TASK: Analyze the research data below and create a DETAILED article outline for: "{meta['titulo']}"
LANGUAGE: {lang}

RESEARCH DATA:
{research_text[:8000]}

OUTPUT a structured outline with EXACTLY this format:

## HOOK (Opening paragraph)
- Key shocking fact or statistic to open with: [extract from research]
- Contrarian angle to hook the reader: [specify]

## SECTION 1: [Title]
- Key data point: [specific number/stat from research with source name]
- Expert voice: [name + credential + their position]
- Contrarian take: [what's wrong with the mainstream view]

## SECTION 2: [Title]  
- Key data point: [specific number/stat from research with source name]
- Case study or real example: [specific company/person/event]
- Source URL to cite: [exact URL from research if available]

## SECTION 3: [Title]
- Key data point: [specific number/stat from research with source name]
- Practical insight: [what the reader can actually DO with this info]

## SECTION 4: [Title — Editorial Verdict]
- Author's definitive stance: [not "time will tell" — pick a side]
- Actionable recommendation: [specific, concrete, executable]
- Closing provocative line: [memorable one-liner]

## VERIFIED URLS FROM RESEARCH
List ALL real URLs found in the research data that can be cited in the article.

RULES:
- ONLY use facts, stats, names, and URLs that exist in the RESEARCH DATA above.
- Do NOT invent any data point. If the research lacks data for a section, write "NO DATA AVAILABLE".
- Include at least 3 specific numbers/statistics.
- Include at least 2 named experts/sources.
"""

    try:
        outline_resp = client.models.generate_content(model='gemini-2.0-flash', contents=outline_prompt)
        outline = outline_resp.text.strip()
        print(f"   ✅ [Fase 1] Outline generado ({len(outline)} chars)")
    except Exception as e:
        print(f"   ⚠️ [Fase 1] Error generando outline: {e}. Usando modo legacy.")
        outline = ""

    # ============================================================
    # FASE 2: REDACCIÓN — Escribir artículo usando outline + research
    # ============================================================
    print(f"   ✍️ [Fase 2] Redactando artículo completo...")
    
    outline_section = ""
    if outline:
        outline_section = f"\n\nARTICLE OUTLINE (follow this structure strictly — do NOT deviate):\n{outline}\n"
    
    prompt = (
        f"{prompt_persona}\n"
        f"{SYSTEM_FORMAT_RULES}\n"
        f"{EEAT_LINK_RULES}\n"
        f"{spiderweb_instruction}\n"
        f"WRITE ARTICLE: {meta['titulo']}\n"
        f"{outline_section}"
        f"ORIGINAL RESEARCH DATA (use as factual foundation — cite sources with links):\n{research_text}\n"
        f"TEMPLATE: {structure}\n"
        f"MINIMUM LENGTH: 1500 words. Articles under 1200 words are REJECTED.\n"
        f"LANG: {lang}"
    )

    # === CEREBRO ESPAÑOL: GEMINI ===
    if lang == "es":
        print("   🇪🇸 [Fase 2] Motor ES: Gemini 2.0 Flash")
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        resultado = resp.text.strip()
    # === CEREBRO INGLÉS: GLM → OpenRouter → Gemini Emergency ===
    else:
        print("   🇬🇧 [Fase 2] Motor EN: GLM-4-Flash → OpenRouter → Gemini")
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

    word_count_final = len(resultado.split()) if resultado else 0
    print(f"   📊 [Resultado] {word_count_final} palabras generadas")
    
    # === POST-PROCESADO: Limpieza de artefactos de IA ===
    resultado = _clean_article_content(resultado)
    return resultado


def _clean_article_content(text):
    """Post-procesador que limpia artefactos de IA del contenido generado."""
    if not text:
        return text
    
    # 1. ELIMINAR [cite: X] markers de NotebookLM
    text = re.sub(r'\s*\[cite:\s*\d+(?:,\s*\d+)*\]', '', text)
    
    # 2. ELIMINAR URLs de Google Grounding API (vertexaisearch redirects)
    #    Patrón: [anchor text](https://vertexaisearch.cloud.google.com/...)
    #    Reemplazar con solo el anchor text en negrita
    text = re.sub(
        r'\[([^\]]+)\]\(https://vertexaisearch\.cloud\.google\.com[^)]*\)',
        r'**\1**',
        text
    )
    
    # 3. ELIMINAR URLs de Google Search/Scholar usadas como placeholder
    text = re.sub(
        r'\[([^\]]+)\]\(https?://(?:scholar\.)?google\.com/search[^)]*\)',
        r'**\1**',
        text
    )
    
    # 4. ELIMINAR links con URLs vacías o inválidas
    text = re.sub(
        r'\[([^\]]+)\]\(\s*\)',
        r'\1',
        text
    )
    
    # 5. ELIMINAR links donde el href es texto plano (no URL)
    #    Ejemplo: [texto](Título de otro artículo que no es URL)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: m.group(0) if m.group(2).startswith(('http', '/', '#')) else m.group(1),
        text
    )
    
    # 6. LIMPIAR H1 sueltos (solo debería haber H2+)
    text = re.sub(r'^# \s*$', '', text, flags=re.MULTILINE)
    
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
    
    # --- FENIX V4: TOPIC DISCOVERY CON REINTENTOS ---
    # Intenta hasta 5 veces encontrar un tema no redundante y seguro
    tema = None
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
        # ¡Tema válido encontrado!
        tema = candidate
        break
    
    if not tema:
        print(f"🚫 ABORTADO: 5 intentos fallidos para encontrar tema no redundante en '{cat}'. Revisa completed.txt o seeds.")
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
