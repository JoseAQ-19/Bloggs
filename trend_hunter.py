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


# ============================================================
# QUALITY GATE: Information Gain Filter
# Descarta temas genéricos ANTES de gastar tokens de research
# ============================================================

def _quality_gate(topic):
    """
    Evalúa si un tema tiene potencial de 'Information Gain' real.
    Retorna True si pasa, False si es genérico/aburrido.
    """
    if not client:
        return True  # Sin IA, pasa todo

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


class TrendHunter:
    @staticmethod
    def get_trend(category):
        """
        Genera un tema Long-Tail (Guerrilla SEO) con Quality Gate.
        Intenta hasta 3 veces si el Quality Gate rechaza por genérico.
        """
        print(f"🎯 [Sniper] Buscando objetivo Long-Tail para: {category}...")
        
        for attempt in range(3):
            topic = None
            
            # 50% Probabilidad: Buscar pregunta real en Reddit (Exa)
            if exa and random.random() > 0.5:
                try:
                    topic = TrendHunter._get_reddit_question(category)
                    if topic and len(topic.split()) >= 6:
                        pass  # topic is set
                    else:
                        topic = None
                except Exception as e:
                    print(f"   ⚠️ Fallo Exa Reddit: {e}")

            # Fallback: Generación Combinatoria (Gemini) — SIEMPRE en inglés (se traduce el tema, no la semilla)
            if not topic:
                topic = TrendHunter._generate_long_tail_idea(category)
            
            # === QUALITY GATE ===
            if _quality_gate(topic):
                return topic
            else:
                print(f"   🔄 [Sniper] Intento {attempt+1}/3 descartado. Regenerando...")
        
        # Si 3 intentos fallan, devuelve el último (mejor algo que nada)
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
