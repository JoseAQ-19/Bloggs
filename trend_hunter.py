import os
import random
import requests
from dotenv import load_dotenv
from google import genai
from exa_py import Exa

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
EXA_KEY = os.getenv("EXA_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
exa = Exa(EXA_KEY) if EXA_KEY else None

# SEMILLAS (Seeds) para generar ideas combinatorias
SEEDS = {
    "ia": ["Cursor AI", "Make.com", "n8n", "Claude 3.5", "ChatGPT Team", "Midjourney v6", "Zapier", "AutoGPT", "LangChain", "Hugging Face"],
    "crypto": ["Solana", "Base Chain", "Arbitrum", "Uniswap", "Metamask", "Ledger Nano", "Staking ETH", "Memecoins", "Airdrops", "Lightning Network"],
    "fitness": ["Zone 2 Cardio", "Creatine Monohydrate", "Hyrox training", "Sleep tracking", "Cold plunge", "Sauna protocols", "VO2 Max", "Protein intake", "Intermittent Fasting", "Hypertrophy"],
    "youtube": ["OBS Studio", "DaVinci Resolve", "CapCut", "YouTube Shorts Algo", "Thumbnail design", "CTR optimization", "Sponsorships", "Affiliate Marketing", "Epidemic Sound", "TubeBuddy"],
    "viral": ["TikTok Trends", "Reddit Stories", "Twitter Drama", "Digital Nomad Lifestyle", "Remote Work", "AI Influencers", "Deepfakes", "Cybersecurity scams", "Tech layoffs", "Silicon Valley culture"]
}

TEMPLATES = [
    "Cómo solucionar el error {error} en {seed} 2026",
    "Mejores alternativas open source a {seed} para {use_case}",
    "{seed} vs {competitor}: Cuál es mejor para {avatar}",
    "Guía definitiva de {seed} para principiantes: Trucos ocultos",
    "Por qué {seed} está fallando en 2026: Análisis honesto",
    "Cómo configurar {seed} paso a paso sin saber programar",
    "La verdad sobre {seed} que nadie te cuenta",
    "Tutorial avanzado de {seed}: Automatiza tu trabajo"
]

class TrendHunter:
    @staticmethod
    def get_trend(category):
        """
        Genera un tema Long-Tail (Guerrilla SEO).
        Estrategia: Exa (Reddit/Quora) o LLM Combinatorio.
        """
        print(f"🎯 [Sniper] Buscando objetivo Long-Tail para: {category}...")
        
        # 50% Probabilidad: Buscar pregunta real en Reddit (Exa)
        if exa and random.random() > 0.5:
            try:
                topic = TrendHunter._get_reddit_question(category)
                if topic and len(topic.split()) >= 6: # Filtro longitud relajado para preguntas reales
                    return topic
            except Exception as e:
                print(f"   ⚠️ Fallo Exa Reddit: {e}")

        # 50% Probabilidad (o Fallback): Generación Combinatoria (Gemini)
        return TrendHunter._generate_long_tail_idea(category)

    @staticmethod
    def _get_reddit_question(category):
        print("   🧠 Cazando dudas en Reddit/Quora...")
        seed = random.choice(SEEDS.get(category, ["Technology"]))
        query = f"site:reddit.com OR site:quora.com problems with {seed} 2025"
        
        res = exa.search(
            query,
            num_results=3,
            type="neural",
            # use_autoprompt=True # REMOVED: Deprecated
        )
        
        if res.results:
            # Coger un título limpio
            title = random.choice(res.results).title
            # Limpiar basura tipo "Reddit - "
            clean = title.split(" - ")[0].split(" | ")[0]
            print(f"   ✅ Reddit encontrado: {clean}")
            return clean
        return None

    @staticmethod
    def _generate_long_tail_idea(category):
        print("   🎲 Generando Long-Tail sintético (LLM)...")
        seeds = SEEDS.get(category, ["Tech"])
        seed = random.choice(seeds)
        
        if not client:
            # Fallback sin IA: Plantilla simple
            return f"Guía completa sobre {seed} para expertos en 2026"

        prompt = f"""
        ACT AS: SEO Sniper.
        TASK: Generate 1 highly specific, long-tail blog post title about "{seed}" in the niche "{category}".
        
        RULES:
        1. MUST be a specific problem, comparison, or advanced guide. NO generic news.
        2. LENGTH: Minimum 8 words.
        3. FORMAT: Clickable but honest.
        4. LANGUAGE: English (Standard).
        
        EXAMPLES:
        - "How to fix connection timeout error in Metamask when using Ledger"
        - "Claude 3.5 Sonnet vs GPT-4o: Which is better for Python coding?"
        - "The hidden danger of using Creatine without proper hydration"
        
        OUTPUT ONLY THE TITLE. NO QUOTES.
        """
        
        try:
            resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            title = resp.text.strip().replace('"', '')
            if len(title.split()) < 6: # Sanity check
                return f"Advanced guide to {seed} and common mistakes in 2026"
            return title
        except:
            return f"Deep dive into {seed} usage and best practices 2026"

if __name__ == "__main__":
    # Dry Run
    print("\n--- SNIPER DRY RUN ---")
    print("IA:", TrendHunter.get_trend("ia"))
    print("Crypto:", TrendHunter.get_trend("crypto"))
    print("Fitness:", TrendHunter.get_trend("fitness"))
