import os
import json
import subprocess
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types

# Configuración
# En GitHub Actions (Linux) el binario suele estar en ~/.local/bin o en el PATH global
MCP_BINARY = "notebooklm-mcp" 

class NotebookMCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 0
        self.is_connected = False

    def connect(self):
        """Intenta conectar al servidor MCP. Falla rápido si no hay auth."""
        auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
        if not os.path.exists(auth_path):
            print("⚠️ [Capa 1] No se encontró auth.json. Saltando NotebookLM.")
            return False

        try:
            print(f"🔌 [Capa 1] Iniciando NotebookLM MCP ({MCP_BINARY})...")
            self.process = subprocess.Popen(
                [MCP_BINARY],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Handshake
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "researcher-v3", "version": "1.0"}
                },
                "id": self.request_id
            }
            self.send_request(init_req)
            resp = self.read_response()
            
            if not resp or "error" in resp:
                print(f"❌ [Capa 1] Error Handshake: {resp}")
                return False

            self.send_notification("notifications/initialized", {})
            self.is_connected = True
            print("✅ [Capa 1] Conexión Establecida.")
            return True
            
        except FileNotFoundError:
            print("❌ [Capa 1] Binario 'notebooklm-mcp' no encontrado en PATH.")
            return False
        except Exception as e:
            print(f"❌ [Capa 1] Error conexión: {e}")
            return False

    def send_request(self, req):
        if not self.process: return
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()
        self.request_id += 1

    def send_notification(self, method, params):
        if not self.process: return
        req = {"jsonrpc": "2.0", "method": method, "params": params}
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()

    def read_response(self, timeout=30):
        if not self.process: return None
        # Simple blocking read (en producción usaríamos threads/async para timeout real)
        try:
            line = self.process.stdout.readline()
            if not line: return None
            return json.loads(line)
        except Exception as e:
            print(f"Error lectura MCP: {e}")
            return None

    def call_tool(self, name, arguments):
        if not self.is_connected: return None
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
            "id": self.request_id
        }
        self.send_request(req)
        return self.read_response()

    def close(self):
        if self.process:
            self.process.terminate()

class ResearcherV3:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def research(self, keyword):
        print(f"\n🔍 INICIANDO INVESTIGACIÓN PROFUNDA PARA: '{keyword}'")
        
        # 🥇 CAPA 1: NOTEBOOKLM MCP
        result = self._layer_1_notebooklm(keyword)
        if result: return result
        
        # 🥈 CAPA 2: GEMINI GROUNDING
        result = self._layer_2_gemini_grounding(keyword)
        if result: return result
        
        # 🥉 CAPA 3: SCRAPING CLÁSICO
        return self._layer_3_classic_scraping(keyword)

    def _layer_1_notebooklm(self, keyword):
        print("\n🥇 CAPA 1: Intentando NotebookLM MCP...")
        mcp = NotebookMCPClient()
        if not mcp.connect():
            return None

        try:
            # 1. Crear Notebook
            title = f"Research-{keyword.replace(' ', '-')}-{int(time.time())}"
            print(f"   📓 Creando Notebook: {title}")
            mcp.call_tool("create_notebook", {"title": title})
            
            # 2. Buscar Fuentes (Simulado por ahora, o usamos un buscador simple para sacar URLs)
            # NotebookLM MCP suele tener herramienta de búsqueda o ingestión directa?
            # Si no, necesitamos URLs. Usaremos NewsFetcher para obtener las URLs primero.
            urls = self._get_news_urls(keyword, limit=5)
            
            if not urls:
                print("   ⚠️ No se encontraron URLs para alimentar NotebookLM.")
                return None

            # 3. Inyectar Fuentes
            for url in urls:
                print(f"   🔗 Inyectando: {url}")
                # Asumimos que 'add_source' acepta URLs. Si no, habría que scrapear texto.
                # La documentación del MCP suele permitir URLs o Texto. Probamos URL.
                resp = mcp.call_tool("add_source", {"source": url}) 
                # Si falla con URL, inyectamos texto scrapeado
                if resp and 'error' in resp:
                     print("      ⚠️ Fallo URL, inyectando texto raw...")
                     text = self._scrape_text_playwright(url)
                     if text: mcp.call_tool("add_source", {"source": text})

            # 4. Deep Query
            print("   🧠 Ejecutando Deep Query...")
            query = f"Genera un informe exhaustivo sobre '{keyword}'. Incluye: Hechos clave, Cifras financieras, Citas de expertos y Conflictos principales."
            resp = mcp.call_tool("query_notebook", {"query": query})
            
            content = ""
            if resp and "result" in resp:
                for block in resp["result"].get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
            
            mcp.close()
            
            if len(content) > 500:
                print("   ✅ ÉXITO CAPA 1: Informe generado.")
                return f"[FUENTE: NOTEBOOKLM]\n{content}"
            else:
                print("   ⚠️ CAPA 1 Falló: Respuesta vacía.")
                return None

        except Exception as e:
            print(f"   ❌ Error Capa 1: {e}")
            mcp.close()
            return None

    def _layer_2_gemini_grounding(self, keyword):
        print("\n🥈 CAPA 2: Intentando Gemini Grounding (Google Search)...")
        if not self.client: return None
        
        try:
            # Usamos el modelo con herramienta de búsqueda integrada
            prompt = f"""
            Investiga a fondo sobre: "{keyword}".
            Usa Google Search para encontrar datos recientes (últimas 24-48h).
            Genera un resumen técnico detallado con:
            - Estadísticas exactas.
            - Fechas clave.
            - Nombres de involucrados.
            """
            
            # Configuración de Grounding (Google Search Retrieval)
            # Nota: La sintaxis exacta depende de la versión del SDK. 
            # Usamos la configuración estándar de 'google_search_retrieval'.
            tool_config = types.Tool(google_search_retrieval=types.GoogleSearchRetrieval)
            
            resp = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(tools=[tool_config])
            )
            
            if resp.text and len(resp.text) > 300:
                print("   ✅ ÉXITO CAPA 2: Grounding completado.")
                return f"[FUENTE: GEMINI GROUNDING]\n{resp.text}"
            
        except Exception as e:
            print(f"   ⚠️ Error Capa 2: {e}")
        
        return None

    def _layer_3_classic_scraping(self, keyword):
        print("\n🥉 CAPA 3: Ejecutando Scraping Clásico (Playwright)...")
        urls = self._get_news_urls(keyword, limit=3)
        combined_text = ""
        
        for url in urls:
            text = self._scrape_text_playwright(url)
            if text:
                combined_text += f"\n--- FUENTE: {url} ---\n{text[:3000]}\n"
        
        if not combined_text:
            return "No research data available."
            
        return f"[FUENTE: CLASSIC SCRAPING]\n{combined_text}"

    def _get_news_urls(self, keyword, limit=3):
        """Helper para obtener URLs de Google News RSS."""
        try:
            safe_kw = requests.utils.quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=es-419&gl=US&ceid=US:es-419"
            resp = requests.get(rss_url, timeout=10)
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:limit]
            return [item.find("link").text for item in items]
        except:
            return []

    def _scrape_text_playwright(self, url):
        """Scraping Headless Stealth."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(1000)
                html = page.content()
                browser.close()
                
                soup = BeautifulSoup(html, 'lxml')
                for s in soup(["script", "style", "nav", "footer"]): s.extract()
                return soup.get_text(separator="\n").strip()
        except:
            return ""

# Interfaz compatible con main.py
class Researcher: # Wrapper para mantener compatibilidad
    def __init__(self):
        self.v3 = ResearcherV3()
    
    def research_topic(self, keyword):
        return self.v3.research(keyword)

if __name__ == "__main__":
    r = Researcher()
    print(r.research_topic("Caída de Bitcoin"))
