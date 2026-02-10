"""
researcher.py - Motor de Investigación Híbrido v3
Arquitectura de 3 Capas con Fallback Automático:

  CAPA 1: NotebookLM MCP  (Deep Research Premium - Prioridad Máxima)
  CAPA 2: Gemini Search    (Google Search Grounding - Fallback Inteligente)
  CAPA 3: Scraping Directo (Google News RSS + Playwright - Último Recurso)
"""

import os
import json
import re
import shutil
import time
import subprocess
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

# --- BS4: Importación segura ---
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# --- Playwright: Importación segura ---
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# --- Gemini: Importación segura ---
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


# ============================================================================
# CAPA 1: NOTEBOOKLM MCP RESEARCHER (Prioridad Máxima)
# ============================================================================

class NotebookResearcher:
    """
    Interfaz con NotebookLM via MCP (subprocess stdio).
    Funciona cuando:
      - El binary notebooklm-mcp existe
      - El archivo auth.json existe (local o inyectado via GitHub Secret)
    """

    AUTH_PATH = os.path.expanduser("~/.notebooklm-mcp/auth.json")

    def __init__(self):
        self.process = None
        self.request_id = 0
        self.is_connected = False
        self.notebook_id = None
        self.mcp_binary = self._find_mcp_binary()

    @staticmethod
    def _find_mcp_binary():
        """Busca el binary de notebooklm-mcp en el sistema."""
        # 1. Variable de entorno explícita
        env_path = os.getenv("MCP_NOTEBOOKLM_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # 2. En PATH del sistema (pip install / pipx)
        found = shutil.which("notebooklm-mcp")
        if found:
            return found

        # 3. Ubicación conocida (Mac local con uv)
        local_path = os.path.expanduser("~/.local/bin/notebooklm-mcp")
        if os.path.exists(local_path):
            return local_path

        return None

    @staticmethod
    def is_auth_available():
        """Verifica si hay tokens de auth disponibles."""
        auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
        if not os.path.exists(auth_path):
            return False
        try:
            with open(auth_path, 'r') as f:
                data = json.load(f)
            # Verificar que tiene las claves necesarias
            return all(k in data for k in ["cookies", "csrf_token", "session_id"])
        except Exception:
            return False

    def connect(self):
        """Inicia el servidor MCP y realiza el handshake JSON-RPC."""
        if not self.mcp_binary:
            print("⚠️ NotebookLM MCP binary no encontrado.")
            return False

        if not self.is_auth_available():
            print("⚠️ NotebookLM auth.json no disponible o incompleto.")
            return False

        try:
            print(f"🔌 Conectando con NotebookLM MCP: {self.mcp_binary}")
            self.process = subprocess.Popen(
                [self.mcp_binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )

            # Handshake: Initialize
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "novumworld-v3", "version": "3.0"}
                },
                "id": self._next_id()
            }
            self._send(init_req)
            resp = self._read(timeout=15)

            if not resp or "error" in resp:
                print(f"❌ Handshake MCP falló: {resp}")
                self.close()
                return False

            # Notification: Initialized
            self._send_notification("notifications/initialized", {})

            self.is_connected = True
            print("✅ NotebookLM MCP conectado y autenticado.")
            return True

        except Exception as e:
            print(f"⚠️ Error conectando MCP: {e}")
            self.close()
            return False

    def _next_id(self):
        self.request_id += 1
        return self.request_id

    def _send(self, req):
        if not self.process or not self.process.stdin:
            return
        try:
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            self.is_connected = False

    def _send_notification(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _read(self, timeout=30):
        if not self.process or not self.process.stdout:
            return None
        try:
            # Simple readline (blocking but with process timeout)
            line = self.process.stdout.readline()
            if not line:
                return None
            return json.loads(line.strip())
        except Exception as e:
            print(f"   Error leyendo MCP: {e}")
            return None

    def call_tool(self, tool_name, arguments):
        """Llama a una herramienta MCP y retorna el resultado."""
        if not self.is_connected:
            return None

        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": self._next_id()
        }
        self._send(req)
        resp = self._read()

        if resp and "result" in resp:
            return resp["result"]
        elif resp and "error" in resp:
            err = resp["error"]
            print(f"   ❌ MCP Error '{tool_name}': {err}")
            # Detectar auth expirada
            err_str = str(err).lower()
            if "auth" in err_str or "401" in err_str or "forbidden" in err_str:
                print("   🔒 AUTH EXPIRADA → Desactivando MCP para esta ejecución")
                self.is_connected = False
        return None

    def _extract_text(self, result):
        """Extrae texto plano de la respuesta MCP."""
        if not result:
            return ""
        content = result.get("content", [])
        if isinstance(content, str):
            return content
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)

    def _extract_uuid(self, text):
        """Busca un UUID en un texto."""
        if not text:
            return None
        match = re.search(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            text, re.IGNORECASE
        )
        return match.group(0) if match else None

    # ---- FLUJO DE INVESTIGACIÓN COMPLETO ----

    def research(self, keyword, category="general"):
        """
        Flujo completo de investigación via NotebookLM MCP:
        1. Crear notebook temporal
        2. Inyectar fuentes (URLs de noticias)
        3. Deep Research (búsqueda web del MCP)
        4. RAG: Interrogar las fuentes
        5. Limpiar notebook temporal

        Retorna: string con el resultado de la investigación, o "" si falla.
        """
        if not self.is_connected:
            return ""

        print("\n📓 === INVESTIGACIÓN via NotebookLM MCP ===")

        try:
            # 1. CREAR NOTEBOOK TEMPORAL
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            result = self.call_tool("notebook_create", {
                "title": f"Research: {keyword} ({date_str})"
            })
            text = self._extract_text(result)
            nb_id = self._extract_uuid(text)

            if not nb_id:
                # Intentar parsear JSON
                try:
                    data = json.loads(text) if text else {}
                    nb_id = data.get("notebook_id") or data.get("id")
                except (json.JSONDecodeError, TypeError):
                    pass

            if not nb_id:
                print("   ❌ No se pudo crear Notebook. Auth posiblemente expirada.")
                return ""

            self.notebook_id = nb_id
            print(f"   ✅ Notebook creado: {nb_id[:12]}...")

            # 2. BUSCAR URLs DE NOTICIAS FRESCAS
            news_urls = self._get_news_urls(keyword, max_urls=7)

            # 3. INYECTAR URLs COMO FUENTES
            injected = 0
            for url in news_urls:
                print(f"   📎 Inyectando: {url[:55]}...")
                r = self.call_tool("notebook_add_url", {
                    "notebook_id": nb_id,
                    "url": url
                })
                if r:
                    injected += 1
                time.sleep(1.5)

            print(f"   📊 Fuentes inyectadas: {injected}/{len(news_urls)}")

            # 4. DEEP RESEARCH (MCP busca más fuentes automáticamente)
            if injected < 3:
                print("   🔬 Pocas fuentes inyectadas. Lanzando Deep Research MCP...")
                self._run_deep_research(nb_id, keyword)

            # 5. Esperar indexación
            print("   ⏳ Esperando indexación de fuentes...")
            time.sleep(5)

            # 6. INTERROGATORIO RAG
            research_text = self._interrogate(nb_id, keyword, category)

            # 7. CLEANUP
            self._cleanup_notebook(nb_id)

            if research_text and len(research_text) > 200:
                print(f"   ✅ Investigación MCP completada ({len(research_text)} chars)")
                return research_text
            else:
                print("   ⚠️ Resultado MCP insuficiente.")
                return ""

        except Exception as e:
            print(f"   ❌ Error en flujo MCP: {e}")
            if self.notebook_id:
                self._cleanup_notebook(self.notebook_id)
            return ""

    def _get_news_urls(self, keyword, max_urls=7):
        """Obtiene URLs de noticias de Google News RSS."""
        try:
            safe_kw = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return []

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:max_urls]

            urls = []
            for item in items:
                link_el = item.find("link")
                if link_el is not None and link_el.text:
                    urls.append(link_el.text)

            return urls
        except Exception as e:
            print(f"   ⚠️ Error obteniendo URLs: {e}")
            return []

    def _run_deep_research(self, nb_id, keyword):
        """Ejecuta Deep Research del MCP (búsqueda web automática)."""
        try:
            result = self.call_tool("research_start", {
                "query": keyword,
                "source": "web",
                "mode": "fast",
                "notebook_id": nb_id
            })
            text = self._extract_text(result)
            task_id = self._extract_uuid(text)

            if task_id:
                print(f"   ⏳ Deep Research iniciado (task: {task_id[:12]}...)")
                status_result = self.call_tool("research_status", {
                    "notebook_id": nb_id,
                    "task_id": task_id,
                    "poll_interval": 10,
                    "max_wait": 90
                })
                status_text = self._extract_text(status_result)

                if status_text and "completed" in status_text.lower():
                    self.call_tool("research_import", {
                        "notebook_id": nb_id,
                        "task_id": task_id
                    })
                    print("   ✅ Deep Research completado y fuentes importadas")
                    time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Deep Research falló: {e}")

    def _interrogate(self, nb_id, keyword, category):
        """RAG: Interroga al Notebook con las fuentes cargadas."""
        print("   🧠 Interrogando Notebook (RAG)...")

        query = f"""Act as an expert researcher in {category.upper()}.
Analyze ALL the sources added about '{keyword}'.

Extract in a STRUCTURED format:

1. **MAIN NEWS**: What is the most important event/data? Summarize in 2-3 sentences.

2. **HARD DATA / FIGURES**: List all numbers, percentages, amounts, dates, and scientific studies mentioned.

3. **KEY PLAYERS**: People, companies, institutions involved and their position.

4. **CONTROVERSIES / CONFLICTING OPINIONS**: Is there a debate? What do critics vs defenders say?

5. **PRACTICAL CONCLUSION**: What should the reader know? What impact does this have?

IMPORTANT: Base EVERYTHING on the provided sources. Do NOT invent data. If something is not mentioned, say "Not found in sources"."""

        result = self.call_tool("notebook_query", {
            "notebook_id": nb_id,
            "query": query
        })
        return self._extract_text(result)

    def _cleanup_notebook(self, nb_id):
        """Elimina el notebook temporal."""
        try:
            self.call_tool("notebook_delete", {
                "notebook_id": nb_id,
                "confirm": True
            })
            print(f"   🗑️ Notebook temporal eliminado")
        except Exception:
            pass

    def close(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass
            self.process = None


# ============================================================================
# CAPA 2: GEMINI SEARCH GROUNDING (Fallback Inteligente)
# ============================================================================

class GeminiSearchResearcher:
    """
    Usa Gemini 2.0 Flash con Google Search Grounding.
    Busca fuentes REALES de internet y razona sobre ellas.
    Solo necesita la API Key (funciona en GitHub Actions).
    """

    def __init__(self):
        self.client = None
        self.is_available = False
        self._init_client()

    def _init_client(self):
        """Inicializa el cliente de Gemini."""
        if not HAS_GENAI:
            print("⚠️ google-genai no disponible para Gemini Search.")
            return

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("⚠️ No hay API Key para Gemini Search.")
            return

        try:
            self.client = genai.Client(api_key=api_key)
            self.is_available = True
        except Exception as e:
            print(f"⚠️ Error inicializando Gemini: {e}")

    def research(self, keyword, category="general"):
        """
        Investigación con Gemini + Google Search Grounding.
        Gemini busca en internet en tiempo real y devuelve datos verificados.
        """
        if not self.is_available:
            return ""

        print("\n🔍 === INVESTIGACIÓN via Gemini Search Grounding ===")

        prompt = f"""You are an expert researcher in {category.upper()}.

TASK: Research the topic "{keyword}" using current web sources.

REQUIREMENTS:
1. Find the LATEST news and developments (last 48 hours if possible)
2. Include HARD DATA: numbers, percentages, dates, study names
3. Identify KEY PLAYERS: companies, people, institutions
4. Note any CONTROVERSIES or conflicting opinions
5. Provide a PRACTICAL CONCLUSION

FORMAT your response as a structured research briefing:

## Main Finding
[2-3 sentence summary of the most important development]

## Key Data Points
- [Bullet points with specific numbers, dates, facts]

## Key Players
- [Who is involved and their position]

## Controversy / Debate
- [Different opinions if they exist]

## Practical Takeaway
[What should someone writing about this topic know?]

IMPORTANT: Only include information you can verify from web sources. Cite source names when possible."""

        try:
            # Gemini con Google Search Grounding
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                )
            )

            result = response.text.strip() if response.text else ""

            # Extraer fuentes de grounding si disponibles
            sources_info = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                grounding = getattr(candidate, 'grounding_metadata', None)
                if grounding and hasattr(grounding, 'grounding_chunks'):
                    chunks = grounding.grounding_chunks or []
                    if chunks:
                        sources_info = "\n\n## Fuentes Verificadas:\n"
                        for i, chunk in enumerate(chunks[:10]):
                            web = getattr(chunk, 'web', None)
                            if web:
                                title = getattr(web, 'title', 'N/A')
                                uri = getattr(web, 'uri', 'N/A')
                                sources_info += f"- [{title}]({uri})\n"

            full_result = result + sources_info

            if full_result and len(full_result) > 200:
                print(f"   ✅ Gemini Search completado ({len(full_result)} chars)")
                return full_result
            else:
                print("   ⚠️ Resultado Gemini Search insuficiente.")
                return ""

        except Exception as e:
            print(f"   ❌ Error en Gemini Search: {e}")
            return ""


# ============================================================================
# CAPA 3: SCRAPING DIRECTO (Último Recurso)
# ============================================================================

class ScrapingResearcher:
    """
    Scraping directo de Google News RSS + Playwright/BS4.
    Siempre disponible como último recurso.
    """

    @staticmethod
    def scrape_url(url):
        """Extrae texto de una URL. Intenta Playwright primero, luego estático."""
        if HAS_PLAYWRIGHT:
            text = ScrapingResearcher._scrape_dynamic(url)
            if text:
                return text

        return ScrapingResearcher._scrape_static(url)

    @staticmethod
    def _scrape_dynamic(url):
        """Scraping dinámico con Playwright."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                               "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                html = page.content()
                browser.close()
                return ScrapingResearcher._extract_text(html)
        except Exception:
            return ""

    @staticmethod
    def _scrape_static(url):
        """Scraping estático con requests."""
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code == 200:
                return ScrapingResearcher._extract_text(resp.text)
        except Exception:
            pass
        return ""

    @staticmethod
    def _extract_text(html):
        """Extrae párrafos limpios de HTML."""
        if not HAS_BS4:
            return ""
        soup = BeautifulSoup(html, 'lxml')
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            junk.extract()
        paragraphs = soup.find_all('p')
        parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50]
        return "\n\n".join(parts)

    @staticmethod
    def research(keyword, max_sources=5):
        """Investigación completa via scraping."""
        print("\n📰 === INVESTIGACIÓN via Scraping Directo (Fallback) ===")
        try:
            safe_kw = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return ""

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:max_sources]

            sources = []
            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")

                if title_el is None or link_el is None:
                    continue

                title = title_el.text or ""
                url = link_el.text or ""
                pub_date = pub_el.text if pub_el is not None else ""

                print(f"   🕵️ Scraping: {title[:50]}...")
                content = ScrapingResearcher.scrape_url(url)

                if not content:
                    continue

                sources.append(
                    f"--- FUENTE ---\n"
                    f"Título: {title}\n"
                    f"Fecha: {pub_date}\n"
                    f"URL: {url}\n"
                    f"Contenido:\n{content[:6000]}\n"
                )

            if sources:
                result = "\n\n".join(sources)
                print(f"   ✅ Scraping completado: {len(sources)} fuentes")
                return result

        except Exception as e:
            print(f"   ❌ Error en scraping: {e}")

        return ""


# ============================================================================
# DETECTOR DE TENDENCIAS
# ============================================================================

class TrendDetector:
    """Detecta tendencias frescas por nicho via Google News RSS."""

    NICHE_FEEDS = {
        "tech": "AI+artificial+intelligence+Apple+Google+Microsoft+startup+2026",
        "crypto": "Bitcoin+Ethereum+Solana+ETF+crypto+SEC+memecoin",
        "geopolitics": "geopolitics+sanctions+trade+war+China+USA+BRICS",
        "fitness": "fitness+study+supplements+workout+controversy",
        "general": "technology+breakthrough+AI+economy+disruption+2026",
    }

    @staticmethod
    def detect_category(keyword):
        """Clasifica un keyword en una categoría."""
        kw = keyword.lower()
        if any(w in kw for w in ["crypto", "bitcoin", "ethereum", "solana", "defi", "nft", "blockchain"]):
            return "crypto"
        if any(w in kw for w in ["fitness", "gym", "workout", "creatine", "protein", "crossfit"]):
            return "fitness"
        if any(w in kw for w in ["war", "sanctions", "nato", "brics", "geopolit", "china", "taiwan"]):
            return "geopolitics"
        if any(w in kw for w in ["ai", "artificial", "tech", "apple", "google", "microsoft", "gpu", "chip"]):
            return "tech"
        return "general"

    @staticmethod
    def get_niche_trends(category="general", max_trends=5):
        """Busca tendencias del nicho via Google News RSS."""
        print(f"🔥 Buscando tendencias [{category.upper()}]...")
        query = TrendDetector.NICHE_FEEDS.get(category, TrendDetector.NICHE_FEEDS["general"])

        try:
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return []

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")

            seen = set()
            trends = []
            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")

                if title_el is None or link_el is None:
                    continue

                title = title_el.text or ""
                clean = re.sub(r'[^a-zA-Z0-9]', '', title.lower())[:40]
                if clean in seen:
                    continue
                seen.add(clean)

                trends.append({
                    "title": title,
                    "url": link_el.text or "",
                    "pub_date": pub_el.text if pub_el is not None else "",
                })

                if len(trends) >= max_trends:
                    break

            for i, t in enumerate(trends):
                print(f"   [{i+1}] {t['title'][:65]}...")

            return trends
        except Exception as e:
            print(f"   ⚠️ Error detectando tendencias: {e}")
            return []


# ============================================================================
# ORQUESTADOR PRINCIPAL
# ============================================================================

class Researcher:
    """
    Orquesta la investigación con 3 capas de fallback:
      1. NotebookLM MCP  (cuando hay auth disponible)
      2. Gemini Search    (cuando hay API Key)
      3. Scraping Directo (siempre disponible)
    """

    def __init__(self):
        # Capa 1: NotebookLM MCP
        self.mcp = NotebookResearcher()
        self.use_mcp = self.mcp.connect()

        # Capa 2: Gemini Search
        self.gemini = GeminiSearchResearcher()

    def research_topic(self, keyword):
        """
        Pipeline de investigación con fallback automático.
        Retorna string con contexto rico para pasar a Gemini Writer.
        """
        print(f"\n{'='*60}")
        print(f"🔬 INVESTIGACIÓN PROFUNDA: '{keyword}'")
        print(f"{'='*60}")

        category = TrendDetector.detect_category(keyword)
        print(f"📁 Categoría: {category.upper()}")
        print(f"🔌 MCP: {'✅ Conectado' if self.use_mcp else '❌ No disponible'}")
        print(f"🔍 Gemini Search: {'✅ Disponible' if self.gemini.is_available else '❌ No disponible'}")

        research_result = ""
        research_source = ""

        # --- CAPA 1: NotebookLM MCP (Prioridad máxima) ---
        if self.use_mcp:
            research_result = self.mcp.research(keyword, category)
            if research_result:
                research_source = "NotebookLM Deep Research (Fuentes verificadas)"

        # --- CAPA 2: Gemini Search Grounding (Fallback inteligente) ---
        if not research_result and self.gemini.is_available:
            print("\n↩️ MCP no disponible/falló → Usando Gemini Search Grounding...")
            research_result = self.gemini.research(keyword, category)
            if research_result:
                research_source = "Gemini Search Grounding (Fuentes web verificadas)"

        # --- CAPA 3: Scraping Directo (Último recurso) ---
        if not research_result:
            print("\n↩️ Gemini Search falló → Usando Scraping Directo...")
            research_result = ScrapingResearcher.research(keyword)
            if research_result:
                research_source = "Scraping Directo (Google News RSS)"

        # --- COMPOSICIÓN DEL CONTEXTO FINAL ---
        context = self._build_context(keyword, category, research_result, research_source)

        # Cleanup
        self.mcp.close()

        source_emoji = "📓" if "NotebookLM" in research_source else "🔍" if "Gemini" in research_source else "📰" if research_source else "⚠️"
        print(f"\n{source_emoji} FUENTE FINAL: {research_source or 'Conocimiento general (sin fuentes)'}")
        print(f"✅ Contexto generado: {len(context)} chars")

        return context

    def _build_context(self, keyword, category, research, source):
        """Compone el contexto final estructurado."""
        header = (
            f"RESEARCH BRIEFING\n"
            f"Topic: {keyword}\n"
            f"Category: {category.upper()}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Source: {source or 'General knowledge (no external sources available)'}\n"
            f"{'='*50}\n\n"
        )

        if research:
            return header + research
        else:
            return header + (
                f"No external research was available for this topic.\n"
                f"Write the article based on your general knowledge about: {keyword}\n"
                f"Focus on recent developments and practical insights."
            )


# ============================================================================
# PRUEBA UNITARIA
# ============================================================================

if __name__ == "__main__":
    print("🧪 TEST: Motor de Investigación Híbrido v3\n")
    r = Researcher()
    result = r.research_topic("AI in Medicine 2026")
    print("\n" + "="*60)
    print("RESULTADO FINAL (primeros 2000 chars):")
    print("="*60)
    print(result[:2000])
