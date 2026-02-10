import requests
import feedparser
import os
import random
from datetime import datetime

class TrendHunter:
    @staticmethod
    def get_trend(category):
        """
        Obtiene UN titular de tendencia fresca.
        Si falla API -> Usa Backup Evergreen.
        """
        print(f"🏹 Trend Hunter activado para: {category}")
        
        trend = None
        try:
            if category == "crypto":
                trend = TrendHunter._get_crypto_trend()
            elif category == "ia":
                trend = TrendHunter._get_news_trend("artificial intelligence technology")
            elif category == "fitness":
                trend = TrendHunter._get_news_trend("fitness health science")
            elif category == "youtube":
                trend = TrendHunter._get_news_trend("creator economy youtube twitch")
            elif category == "viral":
                trend = TrendHunter._get_google_trends()
            else:
                print(f"⚠️ Categoría desconocida: {category}")
        except Exception as e:
            print(f"❌ Error API TrendHunter: {e}")
        
        if trend:
            return trend
            
        print("❄️ API falló. Activando COLD STORAGE (Backup)...")
        return TrendHunter._get_backup_trend(category)

    @staticmethod
    def _get_backup_trend(category):
        filepath = f"data/backups/{category}.txt"
        if not os.path.exists(filepath):
            return f"The future of {category} in 2026"
            
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
            
        if lines:
            return random.choice(lines)
        return f"Latest trends in {category}"

    @staticmethod
    def _get_crypto_trend():
        # CoinGecko Trending
        url = "https://api.coingecko.com/api/v3/search/trending"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            coins = data.get('coins', [])
            if coins:
                top_coin = coins[0]['item']['name']
                return f"Why is {top_coin} trending today in crypto?"
        return None # Force backup

    @staticmethod
    def _get_news_trend(query):
        # Google News RSS (Simple & Reliable)
        safe_q = requests.utils.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={safe_q}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries[0].title
        return None

    @staticmethod
    def _get_google_trends():
        # Fallback a RSS de Google Trends Daily
        rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries[0].title
        return None

if __name__ == "__main__":
    # Test rápido
    print("Crypto:", TrendHunter.get_trend("crypto"))
