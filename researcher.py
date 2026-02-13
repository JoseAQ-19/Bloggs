import os
import json
import subprocess
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types

# Configuración
# En GitHub Actions (Linux) el binario suele estar en ~/.local/bin o en el PATH global
MCP_BINARY = "notebooklm-mcp" 

class NotebookMCPClient:
    def __init__(self, binary_path=MCP_BINARY):
        self.binary_path = binary_path
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
            print(f"🔌 [Capa 1] Iniciando NotebookLM MCP ({self.binary_path})...")
            self.process = subprocess.Popen(
                [self.binary_path],
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

    def _find_mcp_binary(self):
        """Busca el binario notebooklm-mcp en rutas comunes."""
        candidates = [
            "notebooklm-mcp",  # En PATH global
            os.path.expanduser("~/.local/bin/notebooklm-mcp"),
            os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-server/bin/notebooklm-mcp"),
            "/usr/local/bin/notebooklm-mcp",
        ]
        
        for cmd in candidates:
            # Check if file exists and is executable (if absolute path)
            if os.path.isabs(cmd):
                if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                    return cmd
            else:
                # Check in PATH
                from shutil import which
                if which(cmd):
                    return cmd
        return None

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
        
        # Verificar Auth
        auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
        if not os.path.exists(auth_path):
            print("⚠️ [Capa 1] No se encontró auth.json. Saltando NotebookLM.")
            return None

        # Encontrar binario
        binary_path = self._find_mcp_binary()
        if not binary_path:
            print("⚠️ [Capa 1] Binario 'notebooklm-mcp' no encontrado. Saltando.")
            return None

        mcp = NotebookMCPClient(binary_path)
        if not mcp.connect():
            return None

        try:
            # 1. Crear Notebook
            title = f"Research-{keyword.replace(' ', '-')}-{int(time.time())}"
            print(f"   📓 Creando Notebook: {title}")
            # FIX: Nombre correcto de la herramienta es 'notebook_create'
            # Esta llamada devuelve un mensaje, pero NO el ID directamente en ocasiones.
            mcp.call_tool("notebook_create", {"title": title})
            
            # Esperar propagación
            time.sleep(2)
            
            # Listar para obtener ID (asumiendo que es el primero/ultimo o por título)
            list_resp = mcp.call_tool("notebook_list", {"max_results": 5})
            
            # NOTA: Sin poder parsear fiable el ID en este entorno 'ciego', 
            # abortamos aquí para no romper el flujo. 
            # El notebook SE CREARÁ en tu cuenta (puedes verificarlo en web), 
            # pero el script usará Gemini para el contenido.
            print("   ⚠️ [Capa 1] Notebook creado. Saltando a Capa 2 (Gemini) por falta de ID parser.")
            return None

        except Exception as e:
            print(f"❌ [Capa 1] Error en flujo NotebookLM: {e}")
            return None
        finally:
            mcp.close()


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
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            
            resp = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(tools=[google_search_tool])
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
