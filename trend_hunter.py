import os
import random
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from google import genai
from google.genai import types
from exa_py import Exa

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
EXA_KEY = os.getenv("EXA_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
exa = Exa(EXA_KEY) if EXA_KEY else None

# SEMILLAS para nichos TÉCNICOS (IA, Crypto, Fitness)
SEEDS = {
    "ia": ["Cursor AI", "Make.com", "n8n", "Claude 3.5", "ChatGPT Team", "Midjourney v6", "Zapier", "AutoGPT", "LangChain", "Hugging Face"],
    "crypto": ["Solana", "Base Chain", "Arbitrum", "Uniswap", "Metamask", "Ledger Nano", "Staking ETH", "Memecoins", "Airdrops", "Lightning Network"],
    "fitness": ["Zone 2 Cardio", "Creatine Monohydrate", "Hyrox training", "Sleep tracking", "Cold plunge", "Sauna protocols", "VO2 Max", "Protein intake", "Intermittent Fasting", "Hypertrophy"],
}

# FUENTES DE NOTICIAS para nichos de ACTUALIDAD (YouTube, Viral)
NEWS_SOURCES = {
    "youtube": {
        "es": [
            "youtubers España polémica drama",
            "creadores contenido España tendencia",
            "Therians España viral TikTok",
            "Ibai Auronplay ElRubius drama",
            "YouTube España tendencia semanal",
        ],
        "en": [
            "YouTuber drama controversy this week",
            "MrBeast Logan Paul KSI news",
            "YouTube trending creator drama",
            "viral YouTube challenge reaction",
            "creator economy news layoff sponsor",
        ]
    },
    "viral": {
        "es": [
            "tendencia viral España esta semana TikTok",
            "polémica redes sociales España",
            "meme viral España trending",
            "cultura digital España generación Z",
            "escándalo influencer España",
        ],
        "en": [
            "viral trend this week TikTok Reddit",
            "internet culture controversy debate",
            "Gen Z trend going viral",
            "social media drama scandal this week",
            "meme culture viral moment",
        ]
    }
}


# ============================================================
# QUALITY GATE: Information Gain Filter
# ============================================================

def _quality_gate(topic, category="general"):
    """Evalúa si un tema tiene potencial de 'Information Gain' real."""
    if not client:
        return True

    # Quality gate adaptado para nichos de actualidad
    if category in ("youtube", "viral"):
        prompt = f"""ACT AS: Viral Content Editor for a trending news site.
EVALUATE this topic for a {category} article: "{topic}"

ANSWER ONLY "PASS" or "FAIL" followed by a 1-sentence reason.

RULES:
- PASS if the topic is about a CURRENT event, controversy, drama, or trending phenomenon
- PASS if the topic involves NAMED creators, celebrities, or specific viral moments
- PASS if the topic has strong emotional/opinion angles (debate, outrage, surprise)
- FAIL if the topic is a generic guide, tutorial, or how-to
- FAIL if the topic is about tools or software (OBS, CapCut, etc.)
- FAIL if the topic could have been written 2 years ago (not time-sensitive)

OUTPUT FORMAT: PASS|reason or FAIL|reason
"""
    else:
        prompt = f"""ACT AS: Ruthless SEO Quality Auditor.
EVALUATE this blog topic: "{topic}"

ANSWER ONLY "PASS" or "FAIL" followed by a 1-sentence reason.

RULES:
- FAIL if the topic is too generic (e.g., "What is Bitcoin", "Guide to fitness")
- FAIL if the topic has been covered by 100+ articles already (commodity content)
- FAIL if there is NO possible contrarian angle or fresh data to add
- PASS if the topic targets a specific problem, comparison, error, or niche audience
- PASS if the topic has a controversial or data-driven angle

OUTPUT FORMAT: PASS|reason or FAIL|reason
"""
    try:
        resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        answer = resp.text.strip().upper()
        if answer.startswith("PASS"):
            print(f"   ✅ [Quality Gate] APROBADO: {answer}")
            return True
        else:
            print(f"   🚫 [Quality Gate] RECHAZADO: {answer}")
            return False
    except Exception as e:
        print(f"   ⚠️ [Quality Gate] Error: {e}. Aprobando por defecto.")
        return True


# ============================================================
# GOOGLE NEWS RSS: Fuente de noticias reales en tiempo real
# ============================================================

def _get_google_news_headlines(query, lang="es", limit=5):
    """Busca titulares reales de Google News RSS."""
    try:
        safe_kw = requests.utils.quote(query)
        if lang == "es":
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=es-ES&gl=ES&ceid=ES:es"
        else:
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en-US&gl=US&ceid=US:en"
        
        resp = requests.get(rss_url, timeout=10)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:limit]
        
        headlines = []
        for item in items:
            title = item.find("title").text
            if title:
                # Limpiar el sufijo del medio (ej: "Título - El País")
                clean = title.split(" - ")[0].strip()
                if len(clean.split()) >= 4:
                    headlines.append(clean)
        
        return headlines
    except Exception as e:
        print(f"   ⚠️ Google News RSS error: {e}")
        return []


class TrendHunter:
    @staticmethod
    def get_trend(category):
        """
        Genera un tema con Quality Gate.
        - YouTube/Viral: Busca NOTICIAS REALES de actualidad
        - IA/Crypto/Fitness: Busca temas técnicos long-tail
        """
        print(f"🎯 [Sniper] Buscando objetivo para: {category}...")
        
        # === MODO NOTICIAS (YouTube, Viral) ===
        if category in ("youtube", "viral"):
            return TrendHunter._get_trending_news_topic(category)
        
        # === MODO TÉCNICO (IA, Crypto, Fitness) ===
        return TrendHunter._get_technical_topic(category)
    
    @staticmethod
    def _get_trending_news_topic(category):
        """
        Para YouTube y Viral: busca noticias REALES de tendencia.
        Usa Google News RSS + Gemini Grounding para encontrar lo que está pasando AHORA.
        """
        print(f"   📰 [News Mode] Buscando noticias de tendencia para {category}...")
        
        all_headlines = []
        
        # PASO 1: Google News RSS con múltiples queries
        news_queries = NEWS_SOURCES.get(category, {})
        for lang in ["es", "en"]:
            queries = news_queries.get(lang, [])
            query = random.choice(queries) if queries else f"trending {category}"
            headlines = _get_google_news_headlines(query, lang=lang, limit=3)
            for h in headlines:
                all_headlines.append({"title": h, "lang": lang})
        
        # PASO 1.5: Exa — buscar en sitios especializados de YouTube/Viral
        if exa and category == "youtube":
            print("   🔍 [Exa] Buscando en Dexerto, TubeFilter, SocialBlade...")
            try:
                exa_query = "trending YouTube creator drama controversy viral this week"
                res = exa.search(
                    exa_query,
                    num_results=5,
                    type="neural",
                    include_domains=["dexerto.com", "dexerto.es", "tubefilter.com", "socialblade.com", "dotesports.com", "as.com", "3djuegos.com"]
                )
                if res and res.results:
                    for r in res.results:
                        if r.title and len(r.title.split()) >= 4:
                            clean = r.title.split(" - ")[0].split(" | ")[0].strip()
                            # Detectar idioma por dominio
                            lang = "es" if any(d in (r.url or "") for d in [".es", "dexerto.es", "as.com", "3djuegos"]) else "en"
                            all_headlines.append({"title": clean, "lang": lang})
                    print(f"   ✅ [Exa] {len(res.results)} titulares de fuentes especializadas")
            except Exception as e:
                print(f"   ⚠️ [Exa] Error: {e}")
        
        # PASO 2: Gemini Grounding - buscar tendencias en TIEMPO REAL
        if client:
            print("   🌐 [Grounding] Buscando tendencias en tiempo real...")
            try:
                google_search_tool = types.Tool(google_search=types.GoogleSearch())
                
                if category == "youtube":
                    grounding_prompt = """Search for the MOST TALKED ABOUT YouTube/creator drama, controversy, or viral moment happening RIGHT NOW (this week).

Focus on:
- Creator beefs, controversies, or scandals
- Viral challenges or trends on YouTube/TikTok
- Creator milestones (subscriber records, revenue revelations)
- Platform policy changes affecting creators
- Trending games/movies that creators are reacting to

For SPANISH market: search in Spanish for YouTubers España, drama creadores, tendencias virales España this week.
For ENGLISH market: search for YouTube drama, trending creator news, viral moments this week.

OUTPUT: List 5 specific, time-sensitive headlines (not tutorials!) in this format:
[ES] headline in Spanish about Spain/LatAm creator scene
[ES] headline in Spanish about Spain/LatAm creator scene
[EN] headline in English about US/global creator scene
[EN] headline in English about US/global creator scene
[EN] headline in English about US/global creator scene
"""
                else:  # viral
                    grounding_prompt = """Search for the MOST VIRAL trends, memes, and cultural moments happening RIGHT NOW (this week).

Focus on:
- Viral TikTok/Instagram/Twitter moments
- Cultural debates and controversies
- Meme trends and internet phenomena
- Celebrity/influencer scandals
- Gen Z trends making headlines

For SPANISH market: search in Spanish for tendencias virales España, polémica redes sociales this week.
For ENGLISH market: search for viral trends, internet culture, going viral this week.

OUTPUT: List 5 specific, time-sensitive headlines (not evergreen!) in this format:
[ES] headline in Spanish about Spain/LatAm trends
[ES] headline in Spanish about Spain/LatAm trends
[EN] headline in English about US/global trends
[EN] headline in English about US/global trends
[EN] headline in English about US/global trends
"""
                
                resp = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=grounding_prompt,
                    config=types.GenerateContentConfig(tools=[google_search_tool])
                )
                
                if resp.text:
                    for line in resp.text.strip().split('\n'):
                        line = line.strip()
                        if line.startswith('[ES]'):
                            clean = line[4:].strip().lstrip('- ').strip()
                            if len(clean.split()) >= 4:
                                all_headlines.append({"title": clean, "lang": "es"})
                        elif line.startswith('[EN]'):
                            clean = line[4:].strip().lstrip('- ').strip()
                            if len(clean.split()) >= 4:
                                all_headlines.append({"title": clean, "lang": "en"})
                    print(f"   ✅ [Grounding] {len(all_headlines)} titulares encontrados")
                    
            except Exception as e:
                print(f"   ⚠️ [Grounding] Error: {e}")
        
        if not all_headlines:
            print("   ⚠️ No se encontraron noticias. Usando fallback LLM.")
            return TrendHunter._generate_news_topic_llm(category)
        
        # PASO 3: LLM selecciona el MEJOR titular y lo convierte en ángulo único
        print(f"   🧠 [Selector] Eligiendo mejor tema de {len(all_headlines)} candidatos...")
        
        headlines_text = "\n".join([f"[{h['lang'].upper()}] {h['title']}" for h in all_headlines])
        
        selector_prompt = f"""ACT AS: Viral Content Editor.

Here are real trending headlines I found for the "{category}" niche:

{headlines_text}

TASK: Pick the ONE headline that has the MOST viral potential and rewrite it as a compelling blog post title.

RULES:
1. Pick the most CONTROVERSIAL, DRAMATIC, or SURPRISING headline
2. Rewrite it with a strong opinion angle (not neutral reporting)
3. The title must make someone WANT TO CLICK to read the full analysis
4. Keep it in the SAME LANGUAGE as the original headline
5. Do NOT pick tutorials, guides, or how-to topics
6. PREFER time-sensitive, THIS WEEK news over evergreen topics

OUTPUT ONLY THE FINAL TITLE. No quotes, no explanation, no numbering.
"""
        
        try:
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=selector_prompt)
            topic = resp.text.strip().replace('"', '').split('\n')[0]
            if topic and len(topic.split()) >= 5:
                # Quality gate
                if _quality_gate(topic, category):
                    return topic
        except Exception as e:
            print(f"   ⚠️ [Selector] Error: {e}")
        
        # Fallback: usar un titular aleatorio directamente
        chosen = random.choice(all_headlines)
        return chosen["title"]
    
    @staticmethod
    def _generate_news_topic_llm(category):
        """Fallback: generar tema de noticias con LLM cuando no hay RSS/Grounding."""
        if not client:
            return f"Latest viral {category} controversy this week"
        
        if category == "youtube":
            prompt = """Generate 1 SPECIFIC, TIME-SENSITIVE blog post title about a current YouTube/creator event.

The title must be about:
- A specific named creator (MrBeast, Ibai, ElRubius, KSI, etc.)
- A specific controversy, drama, or viral moment
- Something that happened THIS WEEK or is trending NOW

Do NOT generate:
- Tutorials or how-to guides
- Generic guides about YouTube tools
- Evergreen content that could be written any time

EXAMPLES:
- "MrBeast's $1M Squid Game Elimination: Genius Marketing or Exploitation?"
- "Ibai Llanos se enfrenta a la polémica de las casas de apuestas"
- "Why Every Gaming YouTuber Is Playing Poppy Playtime 5 Right Now"

OUTPUT ONLY THE TITLE. English language. No quotes."""
        else:
            prompt = """Generate 1 SPECIFIC, TIME-SENSITIVE blog post title about a viral/trending cultural moment.

The title must be about:
- A specific viral trend, meme, or cultural phenomenon
- A controversy or debate happening on social media
- Something Gen Z or millennials are arguing about RIGHT NOW

Do NOT generate:
- Evergreen articles about "social media trends 2026"
- Generic think pieces
- Technology tutorials

OUTPUT ONLY THE TITLE. English language. No quotes."""
        
        try:
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            return resp.text.strip().replace('"', '').split('\n')[0]
        except:
            return f"The biggest {category} controversy no one is talking about"
    
    @staticmethod
    def _get_technical_topic(category):
        """Para IA, Crypto, Fitness: busca temas técnicos long-tail."""
        print(f"   🔬 [Tech Mode] Buscando tema técnico para {category}...")
        
        for attempt in range(3):
            topic = None
            
            # 50% Probabilidad: Buscar pregunta real en Reddit (Exa)
            if exa and random.random() > 0.5:
                try:
                    topic = TrendHunter._get_reddit_question(category)
                    if topic and len(topic.split()) >= 6:
                        pass
                    else:
                        topic = None
                except Exception as e:
                    print(f"   ⚠️ Fallo Exa Reddit: {e}")

            # Fallback: Generación Combinatoria (Gemini)
            if not topic:
                topic = TrendHunter._generate_long_tail_idea(category)
            
            # === QUALITY GATE ===
            if _quality_gate(topic, category):
                return topic
            else:
                print(f"   🔄 [Sniper] Intento {attempt+1}/3 descartado. Regenerando...")
        
        print("   ⚠️ [Quality Gate] 3 intentos rechazados. Usando último tema generado.")
        return topic

    @staticmethod
    def _get_reddit_question(category):
        print("   🧠 Cazando dudas en Reddit/Quora...")
        seed = random.choice(SEEDS.get(category, ["Technology"]))
        query = f"site:reddit.com OR site:quora.com problems with {seed} 2025"
        
        res = exa.search(
            query,
            num_results=3,
            type="neural",
        )
        
        if res.results:
            title = random.choice(res.results).title
            clean = title.split(" - ")[0].split(" | ")[0]
            print(f"   ✅ Reddit encontrado: {clean}")
            return clean
        return None

    @staticmethod
    def _generate_long_tail_idea(category):
        """Genera idea Long-Tail en inglés (el tema maestro es siempre EN)."""
        print("   🎲 Generando Long-Tail sintético (LLM)...")
        seeds = SEEDS.get(category, ["Tech"])
        seed = random.choice(seeds)
        
        if not client:
            return f"Advanced guide to {seed} and common mistakes in 2026"

        prompt = f"""ACT AS: SEO Sniper specialized in high-value content.
TASK: Generate 1 highly specific, long-tail blog post title about "{seed}" in the niche "{category}".

RULES:
1. MUST be a specific problem, comparison, error fix, or advanced niche guide. NO generic news.
2. MUST have a contrarian angle, a data-driven hook, or expose a hidden risk.
3. LENGTH: Minimum 8 words.
4. FORMAT: Clickable but honest. Must promise a unique insight.
5. LANGUAGE: English (Standard).

EXAMPLES OF HIGH-QUALITY TITLES:
- "How to fix connection timeout error in Metamask when using Ledger on Arbitrum"
- "Claude 3.5 Sonnet vs GPT-4o: Which hallucinates less for Python coding?"
- "The hidden danger of using Creatine without tracking kidney markers"
- "Why 73% of n8n automations fail in production and how to fix them"

OUTPUT ONLY THE TITLE. NO QUOTES. NO NUMBERING.
"""
        
        try:
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            title = resp.text.strip().replace('"', '').split('\n')[0]
            if len(title.split()) < 6:
                return f"Advanced guide to {seed} and common mistakes in 2026"
            return title
        except:
            return f"Deep dive into {seed} usage and best practices 2026"

if __name__ == "__main__":
    print("\n--- SNIPER DRY RUN ---")
    print("IA:", TrendHunter.get_trend("ia"))
    print("Crypto:", TrendHunter.get_trend("crypto"))
    print("Fitness:", TrendHunter.get_trend("fitness"))
    print("YouTube:", TrendHunter.get_trend("youtube"))
    print("Viral:", TrendHunter.get_trend("viral"))
