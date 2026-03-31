import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import logging
import random
import time

logging.basicConfig(level=logging.INFO)

class DailyNewsFetcher:
    """
    Fetcher de noticias diarias 100% gratuito basado en RSS de Google News
    y DuckDuckGo News (vía scrapeo ligero).
    """

    def get_google_news(self, query, lang="es", limit=5):
        """Obtiene noticias vía RSS de Google News."""
        try:
            safe_query = requests.utils.quote(query)
            if lang == "en":
                url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-US&gl=US&ceid=US:en"
            else:
                url = f"https://news.google.com/rss/search?q={safe_query}&hl=es-ES&gl=ES&ceid=ES:es"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: return []
            
            root = ET.fromstring(resp.content)
            results = []
            for item in root.findall(".//item")[:limit]:
                results.append({
                    "title": item.find("title").text,
                    "link": item.find("link").text,
                    "pubDate": item.find("pubDate").text,
                    "source": "Google News"
                })
            return results
        except Exception as e:
            logging.error(f"❌ Error en Google News RSS: {e}")
            return []

    def get_duckduckgo_news(self, query, limit=5):
        """
        Obtiene noticias de DuckDuckGo News (experimental, scrapeo).
        Es útil para evitar bloqueos de Google.
        """
        try:
            # DuckDuckGo HTML simple search (no JS)
            url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}&iar=news"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: return []
            
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            # Buscamos los resultados de noticias en la versión HTML
            links = soup.find_all("a", class_="result__a")[:limit]
            for link in links:
                results.append({
                    "title": link.get_text(),
                    "link": link["href"],
                    "source": "DuckDuckGo"
                })
            return results
        except Exception as e:
            logging.error(f"❌ Error en DuckDuckGo News: {e}")
            return []

    def fetch_featured_news(self, query, lang="es"):
        """Devuelve un bloque de texto con noticias frescas para el LLM."""
        g_news = self.get_google_news(query, lang=lang, limit=3)
        ddg_news = self.get_duckduckgo_news(query, limit=2)
        
        all_news = g_news + ddg_news
        if not all_news:
            return "No se han encontrado noticias de última hora para este tema."
            
        report = "### 📰 HOT NEWS & TRENDS (DIARIO)\n"
        for i, article in enumerate(all_news):
            report += f"{i+1}. **{article['title']}** - [Link]({article['link']})\n"
            
        return report

if __name__ == "__main__":
    fetcher = DailyNewsFetcher()
    print(fetcher.fetch_featured_news("Euribor hoy España", lang="es"))
