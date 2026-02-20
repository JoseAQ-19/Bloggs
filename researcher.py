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
MCP_BINARY = "notebooklm-mcp"


# ============================================================
# FASE 1: E-E-A-T RESEARCH QUERY CONSTRUCTOR
# Transforma un tema desnudo en un Brief de investigación
# estructurado que fuerza fuentes de alto valor.
# ============================================================

def build_research_query(topic, category, search_context="", lang="es"):
    """
    Construye un prompt de investigación profunda con ángulos E-E-A-T
    forzados, en lugar de lanzar keywords desnudas al buscador.
    """
    if lang == "es":
        geo_rules = """[GEO-RESEARCH: SPANISH / HISPANIC MARKET]
- AVOID basic machine translations of US sources. We want FRESH data from native Spain/LatAm sources.
- PRIORITIZE domains: .es, .mx, .ar, .co and high-authority Hispanic digital press.
- Internal search queries MUST be formulated in Spanish to capture local nuances."""
    else:
        geo_rules = """[GEO-RESEARCH: ENGLISH / GLOBAL MARKET]
- PRIORITIZE US and International high-authority sources.
- PRIORITIZE domains: .com, .io, .gov, .edu.
- Internal search queries MUST be formulated in advanced technical English."""

    return f"""DEEP RESEARCH BRIEF — Topic: "{topic}"
Category: {category}

{geo_rules}
Category: {category}

SEARCH OBJECTIVES (prioritized — ALL are MANDATORY):

1. PRIMARY SOURCES:
   - Official reports, white papers, peer-reviewed studies, or government data
   - SEC filings, earnings calls, regulatory documents if applicable
   - Statistics from named institutions (UN, OECD, IMF, WHO, PubMed, IEEE)

2. EXPERT VOICES (minimum 2 distinct named experts):
   - Named professionals with verifiable credentials (professors, CTOs, lead engineers, analysts)
   - Direct quotes from recent interviews, keynotes, or published articles
   - At least ONE contrarian expert who DISAGREES with the mainstream narrative

3. QUANTITATIVE DATA (minimum 3 distinct data points):
   - Market size, revenue, or growth rates with specific dollar/percentage figures
   - User adoption metrics (MAU, DAU, conversion rates, engagement)
   - Year-over-year comparisons (2024 vs 2025 vs 2026)
   - Named companies with specific investment or revenue figures

4. CONTROVERSY & RISK ANGLES:
   - Credible critics and their specific arguments
   - Lawsuits, regulatory actions, bans, or sanctions related to this topic
   - Failed implementations, cautionary tales, or post-mortem analyses

5. COMPETITIVE LANDSCAPE:
   - Named companies/products with their market positions
   - Recent pivots, acquisitions, layoffs, or shutdowns in this space
   - Comparative analysis (Company A vs Company B approach)

6. REAL-WORLD CASE STUDIES (minimum 1):
   - A specific company, city, or person whose real experience illustrates the topic
   - Include measurable outcomes (revenue change, user growth, failure cost)

QUALITY FILTERS:
- EXCLUDE generic listicles, SEO-farmed content, and rehashed press releases
- EXCLUDE any source without named authors or specific data
- PRIORITIZE sources from the last 90 days
- Additional context keywords: {search_context}
"""


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
                    "clientInfo": {"name": "researcher-v4-eeat", "version": "2.0"}
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
        
        import select
        
        reads, _, _ = select.select([self.process.stdout], [], [], timeout)
        
        if not reads:
            print(f"⚠️ Timeout lectura MCP ({timeout}s)")
            return None
            
        try:
            line = self.process.stdout.readline()
            if not line: return None
            return json.loads(line)
        except Exception as e:
            print(f"Error lectura MCP: {e}")
            return None

    def call_tool(self, name, arguments, timeout=60):
        if not self.is_connected: return None
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
            "id": self.request_id
        }
        self.send_request(req)
        return self.read_response(timeout=timeout)

    def close(self):
        if self.process:
            self.process.terminate()


class ResearcherV4:
    """
    Researcher V4 (E-E-A-T Edition)
    - Deep research mode with structured queries
    - Automatic notebook cleanup after extraction
    - Source-linked report generation
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def _find_mcp_binary(self):
        """Busca el binario notebooklm-mcp en rutas comunes."""
        candidates = [
            "notebooklm-mcp",
            os.path.expanduser("~/.local/bin/notebooklm-mcp"),
            os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-server/bin/notebooklm-mcp"),
            "/usr/local/bin/notebooklm-mcp",
        ]
        
        for cmd in candidates:
            if os.path.isabs(cmd):
                if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                    return cmd
            else:
                from shutil import which
                if which(cmd):
                    return cmd
        return None

    def research(self, topic, category="general", search_context="", lang="es"):
        """
        Pipeline de investigación con 3 capas de fallback.
        Ahora recibe topic, category y search_context por separado, Y IDIOMA (Geo-Research).
        """
        print(f"\n🔍 INICIANDO GEO-RESEARCH E-E-A-T PARA: '{topic}' [{lang.upper()}]")
        print(f"   Categoría: {category} | Contexto: {search_context[:60]}...")
        
        # Construir el Brief de investigación estructurado localizado
        research_brief = build_research_query(topic, category, search_context, lang=lang)
        
        # 🥇 CAPA 1: NOTEBOOKLM DEEP RESEARCH
        result = self._layer_1_notebooklm(topic, research_brief, lang)
        if result: return result
        
        # 🥈 CAPA 2: GEMINI GROUNDING (con brief E-E-A-T)
        result = self._layer_2_gemini_grounding(topic, research_brief, lang)
        if result: return result
        
        # 🥉 CAPA 3: SCRAPING CLÁSICO
        return self._layer_3_classic_scraping(topic, lang)

    def _layer_1_notebooklm(self, topic, research_brief, lang):
        print(f"\n🥇 CAPA 1: NotebookLM DEEP Research (E-E-A-T Mode) [{lang.upper()}]...")
        
        auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
        binary_path = self._find_mcp_binary()
        
        if not os.path.exists(auth_path) or not binary_path:
            print("⚠️ [Capa 1] Falta Auth o Binario MCP. Saltando.")
            return None

        mcp = NotebookMCPClient(binary_path)
        if not mcp.connect():
            return None

        notebook_id = None  # Track for cleanup

        try:
            # =============================================
            # PASO 1: INICIAR DEEP RESEARCH con Brief E-E-A-T
            # Modo "deep": ~5 min, ~40 fuentes de alta calidad
            # =============================================
            timestamp = int(time.time())
            print(f"   🚀 Iniciando DEEP research (modo profundo, ~40 fuentes)...")
            start_resp = mcp.call_tool("research_start", {
                "query": research_brief,
                "mode": "deep",
                "source": "web",
                "title": f"EEAT-{topic[:20].replace(' ', '-')}-{lang}-{timestamp}"
            })
            
            # Parsear respuesta
            data = {}
            if start_resp and "result" in start_resp:
                res = start_resp["result"]
                if "structuredContent" in res:
                    data = res["structuredContent"]
                elif "content" in res and res["content"]:
                    try:
                        data = json.loads(res["content"][0]["text"])
                    except:
                        pass
            
            notebook_id = data.get("notebook_id")
            task_id = data.get("task_id")
            
            if not notebook_id or not task_id:
                print(f"   ❌ Error al iniciar research: {data.get('message', 'Sin datos')}")
                return None
                
            print(f"   📓 Notebook ID: {notebook_id}")
            print(f"   🕵️ Task ID: {task_id} (Esperando Deep Research...")
            
            # =============================================
            # PASO 2: POLLING — Deep mode tarda ~5 minutos
            # =============================================
            max_retries = 24  # 24 × 15s = 6 min max
            completed = False
            
            for i in range(max_retries):
                time.sleep(15) 
                status_resp = mcp.call_tool("research_status", {
                    "task_id": task_id, 
                    "notebook_id": notebook_id
                })
                
                status_data = {}
                if status_resp and "result" in status_resp:
                     res = status_resp["result"]
                     if "structuredContent" in res:
                         status_data = res["structuredContent"]
                     elif "content" in res:
                         try:
                             status_data = json.loads(res["content"][0]["text"])
                         except: pass
                
                state = status_data.get("status", "unknown")
                sources_found = status_data.get("sources_found", "?")
                print(f"      ⏳ Estado ({i+1}/{max_retries}): {state} | Fuentes: {sources_found}")
                
                if state in ["completed", "success"]:
                    completed = True
                    break
                elif state == "failed":
                    print("      ❌ Research falló.")
                    break
            
            if not completed:
                print("   ⚠️ Timeout esperando deep research. Importando lo disponible...")

            # =============================================
            # PASO 3: IMPORTAR FUENTES DESCUBIERTAS
            # =============================================
            print("   📥 Importando fuentes descubiertas al notebook...")
            mcp.call_tool("research_import", {
                "notebook_id": notebook_id, 
                "task_id": task_id
            })
            
            # =============================================
            # PASO 4: EXTRACCIÓN — Prompt con E-E-A-T + Links
            # =============================================
            print("   🧠 Extrayendo informe E-E-A-T con enlaces a fuentes...")
            
            extraction_prompt = f"""Based EXCLUSIVELY on the imported research sources, write a comprehensive 
intelligence report about: '{topic}'.

MANDATORY STRUCTURE:

## Executive Summary
3-4 sentences capturing the core story with at least 1 specific number/statistic.

## Key Data Points
- List every specific statistic, dollar figure, percentage, date, and metric found in the sources.
- For EACH data point, cite which source it comes from using this format:
  [Source Name or Publication](URL if available)

## Expert Voices & Quotes
- List every named expert, analyst, CEO, or researcher mentioned in the sources.
- Include their exact quotes or paraphrased positions.
- Include their credentials/affiliation.
- Flag any experts who DISAGREE with the consensus.

## Controversy, Risks & Criticism
- What are the counterarguments, failures, or risks mentioned?
- Any lawsuits, regulatory actions, or public backlash?

## Case Studies & Real-World Examples
- Specific companies, products, or implementations discussed.
- Measurable outcomes (revenue, users, failure costs).

## Source URLs
List ALL source URLs discovered during research, formatted as:
- [Source Title](https://url)

CRITICAL RULES:
- Do NOT invent or hallucinate any data. Only report what the sources contain.
- Every claim must be traceable to a specific source.
- If a source provides a URL, ALWAYS include it.
"""
            
            query_resp = mcp.call_tool("notebook_query", {
                "notebook_id": notebook_id, 
                "query": extraction_prompt
            }, timeout=180)
            
            # Extraer respuesta
            final_content = ""
            if query_resp and "result" in query_resp and "content" in query_resp["result"]:
                for block in query_resp["result"]["content"]:
                    if block.get("type") == "text":
                        final_content += block.get("text", "")

            if len(final_content) > 500:
                print(f"   ✅ ÉXITO CAPA 1: Informe E-E-A-T generado ({len(final_content)} chars).")
                return {
                    "content": final_content,
                    "layer": "NotebookLM Deep Research (E-E-A-T V2)",
                    "notebook_id": notebook_id,
                    "sources": ["NotebookLM Deep Search — see Source URLs in report"]
                }
            else:
                print("   ⚠️ Informe vacío o demasiado corto. Saltando a Capa 2.")
                return None

        except Exception as e:
            print(f"❌ [Capa 1] Error Deep Research: {e}")
            return None
        finally:
            # =============================================
            # FASE 3: LIMPIEZA — Borrar notebook huérfano
            # =============================================
            if notebook_id:
                try:
                    print(f"   🧹 Limpieza: Eliminando notebook {notebook_id}...")
                    delete_resp = mcp.call_tool("notebook_delete", {
                        "notebook_id": notebook_id,
                        "confirm": True
                    }, timeout=30)
                    if delete_resp and "error" not in delete_resp:
                        print(f"   ✅ Notebook eliminado correctamente.")
                    else:
                        print(f"   ⚠️ No se pudo eliminar notebook (non-critical): {delete_resp}")
                except Exception as cleanup_err:
                    print(f"   ⚠️ Error limpieza notebook (non-critical): {cleanup_err}")
            
            mcp.close()


    def _layer_2_gemini_grounding(self, topic, research_brief, lang):
        print(f"\n🥈 CAPA 2: Gemini Grounding + Google Search (E-E-A-T) [{lang.upper()}]...")
        if not self.client: return None
        
        try:
            prompt = f"""You are a senior investigative journalist. Research the following topic using Google Search.

TOPIC: "{topic}"

RESEARCH REQUIREMENTS:
{research_brief}

OUTPUT FORMAT:
Write a structured research brief with:
1. Key statistics with specific numbers and their sources
2. Named experts and their positions (with quotes if found)
3. Controversy or risk angles
4. Source URLs for every major claim

Include markdown hyperlinks [text](url) for every source you reference.
Do NOT fabricate URLs — only include sources you actually found.
"""
            
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            
            resp = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(tools=[google_search_tool])
            )
            
            if resp.text and len(resp.text) > 300:
                print(f"   ✅ ÉXITO CAPA 2: Grounding completado ({len(resp.text)} chars).")
                return {
                    "content": f"[FUENTE: GEMINI GROUNDING E-E-A-T]\n{resp.text}",
                    "layer": "Gemini Grounding (E-E-A-T V2)",
                    "sources": ["Gemini Google Search Grounding"]
                }
            
        except Exception as e:
            print(f"   ⚠️ Error Capa 2: {e}")
        
        return None

    def _layer_3_classic_scraping(self, topic, lang):
        print(f"\n🥉 CAPA 3: Scraping Clásico (Playwright) [{lang.upper()}]...")
        urls = self._get_news_urls(topic, lang=lang, limit=5)  # Increased from 3 to 5
        combined_text = ""
        
        for url in urls:
            text = self._scrape_text_playwright(url)
            if text:
                combined_text += f"\n--- FUENTE: {url} ---\n{text[:4000]}\n"
        
        if not combined_text:
            return {
                "content": "No research data available.",
                "layer": "Fallback (no data)",
                "sources": []
            }
            
        return {
            "content": f"[FUENTE: CLASSIC SCRAPING]\n{combined_text}",
            "layer": "Classic Scraping",
            "sources": urls
        }

    def _get_news_urls(self, keyword, lang="es", limit=5):
        """Helper para obtener URLs de Google News RSS."""
        try:
            safe_kw = requests.utils.quote(keyword)
            if lang == "en":
                rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en-US&gl=US&ceid=US:en"
            else:
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
class Researcher:
    def __init__(self):
        self.v4 = ResearcherV4()
    
    def research_topic(self, topic, category="general", search_context="", lang="es"):
        """
        V4 API: Accepts topic, category, and search_context separately.
        Returns a dict with 'content', 'layer', 'sources'.
        """
        result = self.v4.research(topic, category, search_context, lang=lang)
        
        # Normalize output — always return a dict
        if isinstance(result, str):
            return {"content": result, "layer": "legacy", "sources": []}
        if isinstance(result, dict):
            return result
        return {"content": "No research data available.", "layer": "fallback", "sources": []}

if __name__ == "__main__":
    r = Researcher()
    print(r.research_topic("Caída de Bitcoin", category="crypto", search_context="cryptocurrency DeFi blockchain"))
