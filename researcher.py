"""
researcher.py - Motor de Investigación Multinivel
Arquitectura: Trending Detection → NotebookLM MCP (Deep Research) → Fallback Scraping

Capas:
  1. TrendDetector     → Encuentra tendencias frescas de nicho (Google News RSS)
  2. NotebookResearcher → Crea Notebooks en NotebookLM, inyecta fuentes y hace RAG
  3. NewsFetcher        → Scraping dinámico con Playwright (Fallback robusto)
  4. Researcher         → Orquestador principal
"""

import os
import json
import re
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- Playwright: Importación segura ---
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️ Playwright no disponible. Scraping dinámico deshabilitado.")

# --- NotebookLM MCP: Importación condicional ---
# El MCP se usa como subprocess (stdio transport) cuando está disponible localmente.
# En GitHub Actions NO hay autenticación de Google, así que usamos fallback.
import subprocess

# ============================================================================
# CAPA 1: DETECTOR DE TENDENCIAS "CLICK-MAGNET"
# ============================================================================

class TrendDetector:
    """
    Detecta tendencias frescas (<24h) específicas del nicho.
    Prioriza titulares polémicos, datos duros y rupturas.
    """

    # Mapeo de categorías a fuentes especializadas de nicho
    NICHE_SOURCES = {
        "tech": [
            "https://news.google.com/rss/search?q=AI+artificial+intelligence+2026&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=Apple+Google+Microsoft+Meta+startup&hl=en&gl=US&ceid=US:en",
        ],
        "crypto": [
            "https://news.google.com/rss/search?q=Bitcoin+Ethereum+Solana+ETF+crypto&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=memecoin+DeFi+SEC+regulation+crypto&hl=en&gl=US&ceid=US:en",
        ],
        "geopolitics": [
            "https://news.google.com/rss/search?q=geopolitics+sanctions+trade+war&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=China+USA+Taiwan+BRICS+NATO&hl=en&gl=US&ceid=US:en",
        ],
        "fitness": [
            "https://news.google.com/rss/search?q=fitness+study+supplements+workout+controversy&hl=en&gl=US&ceid=US:en",
        ],
        "general": [
            "https://news.google.com/rss/search?q=technology+breakthrough+2026&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=AI+regulation+economy+disruption&hl=en&gl=US&ceid=US:en",
        ],
    }

    @staticmethod
    def detect_category(keyword):
        """Clasifica un keyword en una categoría de nicho."""
        kw = keyword.lower()
        if any(w in kw for w in ["crypto", "bitcoin", "ethereum", "solana", "memecoin", "defi", "nft", "blockchain"]):
            return "crypto"
        if any(w in kw for w in ["fitness", "gym", "workout", "creatine", "protein", "crossfit", "hyrox"]):
            return "fitness"
        if any(w in kw for w in ["war", "sanctions", "nato", "brics", "geopolit", "china", "taiwan"]):
            return "geopolitics"
        if any(w in kw for w in ["ai", "artificial", "tech", "apple", "google", "microsoft", "startup", "gpu", "chip"]):
            return "tech"
        return "general"

    @staticmethod
    def get_niche_trends(category="general", max_trends=5):
        """
        Busca tendencias CALIENTES del nicho via Google News RSS.
        Retorna lista de: {title, url, pub_date}
        """
        print(f"🔥 Buscando tendencias de nicho: [{category.upper()}]...")
        feeds = TrendDetector.NICHE_SOURCES.get(category, TrendDetector.NICHE_SOURCES["general"])

        all_items = []
        for rss_url in feeds:
            try:
                resp = requests.get(rss_url, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
                })
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for item in items:
                    title_el = item.find("title")
                    link_el = item.find("link")
                    pub_el = item.find("pubDate")
                    if title_el is not None and link_el is not None:
                        all_items.append({
                            "title": title_el.text or "",
                            "url": link_el.text or "",
                            "pub_date": pub_el.text if pub_el is not None else "",
                        })
            except Exception as e:
                print(f"   ⚠️ Error leyendo feed RSS: {e}")
                continue

        # Deduplicar por título similar y limitar
        seen_titles = set()
        unique = []
        for item in all_items:
            clean_title = re.sub(r'[^a-zA-Z0-9]', '', item['title'].lower())[:40]
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                unique.append(item)

        trends = unique[:max_trends]
        print(f"   📊 Encontradas {len(trends)} tendencias únicas")
        for i, t in enumerate(trends):
            print(f"   [{i+1}] {t['title'][:70]}...")
        return trends

    @staticmethod
    def get_trend_for_keyword(keyword):
        """
        Para un keyword dado, busca tendencias frescas relacionadas.
        Retorna la tendencia más relevante o None.
        """
        print(f"🎯 Buscando tendencia CLICK-MAGNET para: '{keyword}'")
        try:
            safe_kw = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return None

            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:3]  # Top 3

            trends = []
            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")
                if title_el is not None and link_el is not None:
                    trends.append({
                        "title": title_el.text or "",
                        "url": link_el.text or "",
                        "pub_date": pub_el.text if pub_el is not None else "",
                    })

            if trends:
                best = trends[0]
                print(f"   🏆 Tendencia seleccionada: {best['title'][:60]}...")
                return best
            return None

        except Exception as e:
            print(f"   ⚠️ Error buscando tendencia: {e}")
            return None


# ============================================================================
# CAPA 2: NOTEBOOKLM MCP RESEARCHER (Deep Research via MCP)
# ============================================================================

class NotebookResearcher:
    """
    Interfaz con el servidor MCP de NotebookLM.
    Funciona via subprocess (stdio transport) cuando está disponible.
    """

    MCP_PATH = os.getenv("MCP_NOTEBOOKLM_PATH", "/Users/manolo/.local/bin/notebooklm-mcp")

    def __init__(self):
        self.process = None
        self.request_id = 0
        self.is_connected = False
        self.notebook_id = None

    def connect(self):
        """Inicia el servidor MCP y realiza el handshake JSON-RPC."""
        # En GitHub Actions no hay MCP disponible
        if os.getenv("GITHUB_ACTIONS"):
            print("☁️ GitHub Actions detectado → MCP deshabilitado (no hay auth Google)")
            return False

        if not os.path.exists(self.MCP_PATH):
            print(f"⚠️ MCP binary no encontrado en: {self.MCP_PATH}")
            return False

        try:
            print(f"🔌 Conectando con NotebookLM MCP...")
            self.process = subprocess.Popen(
                [self.MCP_PATH],
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
                    "clientInfo": {"name": "novumworld-researcher", "version": "2.0"}
                },
                "id": self._next_id()
            }
            self._send(init_req)
            resp = self._read()

            if not resp or "error" in resp:
                print(f"❌ Handshake MCP falló: {resp}")
                return False

            # Notification: Initialized
            self._send_notification("notifications/initialized", {})

            self.is_connected = True
            print("✅ NotebookLM MCP conectado y listo.")
            return True

        except Exception as e:
            print(f"⚠️ Fallo al conectar MCP: {e}")
            return False

    def _next_id(self):
        self.request_id += 1
        return self.request_id

    def _send(self, req):
        if not self.process:
            return
        self.process.stdin.write(json.dumps(req) + "\n")
        self.process.stdin.flush()

    def _send_notification(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _read(self, timeout=30):
        if not self.process:
            return None
        try:
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
            print(f"   ❌ Error MCP tool '{tool_name}': {resp['error']}")
        return None

    def _extract_text(self, result):
        """Extrae texto de la respuesta MCP (formato content blocks)."""
        if not result:
            return ""
        content = result.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)

    # ----- FLUJO PRINCIPAL DE INVESTIGACIÓN -----

    def create_research_notebook(self, topic):
        """Crea un Notebook temporal para investigar un tema."""
        print(f"📓 Creando Notebook de investigación: '{topic}'...")
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        result = self.call_tool("notebook_create", {
            "title": f"Research: {topic} ({date_str})"
        })
        text = self._extract_text(result)
        # Intentar extraer el notebook_id del texto de respuesta
        try:
            # El MCP suele devolver el ID en la respuesta
            if "notebook_id" in text.lower() or "id" in text.lower():
                # Buscar patrón UUID
                uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text, re.IGNORECASE)
                if uuid_match:
                    self.notebook_id = uuid_match.group(0)
                    print(f"   ✅ Notebook creado: {self.notebook_id}")
                    return self.notebook_id
        except Exception:
            pass

        # Fallback: parsear JSON si viene así
        try:
            data = json.loads(text)
            self.notebook_id = data.get("notebook_id") or data.get("id")
            if self.notebook_id:
                print(f"   ✅ Notebook creado: {self.notebook_id}")
                return self.notebook_id
        except (json.JSONDecodeError, TypeError):
            pass

        print(f"   ⚠️ No se pudo extraer notebook_id. Respuesta: {text[:200]}")
        return None

    def inject_urls(self, notebook_id, urls):
        """Inyecta URLs como fuentes en el Notebook."""
        if not notebook_id:
            return 0

        injected = 0
        for url in urls:
            print(f"   📎 Inyectando fuente: {url[:60]}...")
            try:
                result = self.call_tool("notebook_add_url", {
                    "notebook_id": notebook_id,
                    "url": url
                })
                if result:
                    injected += 1
                time.sleep(1.5)  # Cortesía para no saturar
            except Exception as e:
                print(f"   ⚠️ Error inyectando URL: {e}")
                continue

        print(f"   📊 Fuentes inyectadas: {injected}/{len(urls)}")
        return injected

    def inject_text(self, notebook_id, text, title="Research Data"):
        """Inyecta texto como fuente en el Notebook."""
        if not notebook_id or not text:
            return False
        try:
            result = self.call_tool("notebook_add_text", {
                "notebook_id": notebook_id,
                "text": text[:50000],  # Límite seguro
                "title": title
            })
            return result is not None
        except Exception as e:
            print(f"   ⚠️ Error inyectando texto: {e}")
            return False

    def interrogate(self, notebook_id, category, keyword):
        """
        RAG: Interroga al Notebook con las fuentes cargadas.
        Extrae datos duros, controversias y conclusiones.
        """
        if not notebook_id:
            return ""

        print("🧠 Fase de INTERROGATORIO (RAG sobre fuentes inyectadas)...")

        query = f"""Actúa como un investigador experto en {category.upper()}.
Analiza TODAS las fuentes añadidas sobre '{keyword}'.

EXTRAE de forma ESTRUCTURADA:

1. **NOTICIA PRINCIPAL**: ¿Cuál es el evento/dato más importante? Resume en 2-3 frases.

2. **DATOS DUROS / CIFRAS**: Lista todos los números, porcentajes, montos, fechas y estudios científicos mencionados.

3. **ACTORES CLAVE**: Personas, empresas, instituciones involucradas y su posición.

4. **CONTROVERSIAS / OPINIONES ENCONTRADAS**: ¿Hay debate? ¿Qué dicen los críticos vs los defensores?

5. **CONCLUSIÓN PRÁCTICA**: ¿Qué debería saber el lector? ¿Qué impacto tiene esto?

IMPORTANTE: Basa TODO en las fuentes proporcionadas. No inventes datos. Si algo no aparece, di "No mencionado en fuentes"."""

        result = self.call_tool("notebook_query", {
            "notebook_id": notebook_id,
            "query": query
        })

        text = self._extract_text(result)
        if text:
            print(f"   ✅ Interrogatorio completado ({len(text)} chars)")
        else:
            print("   ⚠️ Interrogatorio no devolvió resultados")
        return text

    def deep_research(self, notebook_id, keyword):
        """
        Usa la función de Deep Research del MCP para buscar fuentes web.
        """
        if not notebook_id:
            return None

        print(f"🔬 Lanzando Deep Research MCP para: '{keyword}'...")
        try:
            result = self.call_tool("research_start", {
                "query": keyword,
                "source": "web",
                "mode": "fast",
                "notebook_id": notebook_id
            })
            text = self._extract_text(result)

            # Extraer task_id para polling
            task_id = None
            try:
                data = json.loads(text)
                task_id = data.get("task_id")
            except (json.JSONDecodeError, TypeError):
                uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text or "", re.IGNORECASE)
                if uuid_match:
                    task_id = uuid_match.group(0)

            if task_id:
                print(f"   ⏳ Research iniciado (task: {task_id}). Esperando...")
                # Poll status
                status_result = self.call_tool("research_status", {
                    "notebook_id": notebook_id,
                    "task_id": task_id,
                    "poll_interval": 10,
                    "max_wait": 120
                })
                status_text = self._extract_text(status_result)

                if status_text and "completed" in status_text.lower():
                    print("   ✅ Deep Research completado. Importando fuentes...")
                    self.call_tool("research_import", {
                        "notebook_id": notebook_id,
                        "task_id": task_id
                    })
                    time.sleep(3)
                    return True
                else:
                    print(f"   ⚠️ Research no completó a tiempo: {status_text[:100] if status_text else 'sin respuesta'}")

            return False

        except Exception as e:
            print(f"   ❌ Error en Deep Research: {e}")
            return False

    def cleanup(self, notebook_id=None):
        """Elimina el notebook temporal para no acumular basura."""
        if notebook_id:
            try:
                self.call_tool("notebook_delete", {
                    "notebook_id": notebook_id,
                    "confirm": True
                })
                print(f"   🗑️ Notebook temporal eliminado: {notebook_id}")
            except Exception:
                pass  # No es crítico

    def close(self):
        """Cierra la conexión MCP."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                pass


# ============================================================================
# CAPA 3: NEWS FETCHER (Scraping Dinámico - FALLBACK)
# ============================================================================

class NewsFetcher:
    """Scraping dinámico con Playwright como sistema de fallback."""

    @staticmethod
    def scrape_url_dynamic(url):
        """Renderiza JS con Playwright y extrae texto limpio."""
        if not HAS_PLAYWRIGHT:
            return NewsFetcher.scrape_url_static(url)

        print(f"   🕵️ Scraping dinámico: {url[:55]}...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/120.0.0.0 Safari/537.36"
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                html = page.content()
                browser.close()

                return NewsFetcher._extract_text_from_html(html)

        except Exception as e:
            print(f"   ⚠️ Error scraping dinámico: {e}")
            return NewsFetcher.scrape_url_static(url)

    @staticmethod
    def scrape_url_static(url):
        """Fallback: Scraping estático con requests + BS4."""
        print(f"   📄 Scraping estático: {url[:55]}...")
        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return ""
            return NewsFetcher._extract_text_from_html(resp.text)
        except Exception as e:
            print(f"   ⚠️ Error scraping estático: {e}")
            return ""

    @staticmethod
    def _extract_text_from_html(html):
        """Extrae párrafos limpios de HTML."""
        soup = BeautifulSoup(html, 'lxml')
        # Eliminar basura
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            junk.extract()

        paragraphs = soup.find_all('p')
        text_parts = []
        for p in paragraphs:
            txt = p.get_text().strip()
            if len(txt) > 50:  # Filtrar ruido corto
                text_parts.append(txt)

        return "\n\n".join(text_parts).strip()

    @staticmethod
    def get_news_sources(keyword, max_sources=5):
        """Busca noticias en Google News RSS y extrae texto FULL."""
        print(f"📰 Buscando noticias frescas: '{keyword}'")
        try:
            safe_kw = quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=en&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BlogBot/1.0)"
            })
            if resp.status_code != 200:
                return []

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

                # Scraping del contenido completo
                clean_text = NewsFetcher.scrape_url_dynamic(url)
                if not clean_text:
                    print(f"   ⚠️ Sin texto útil de: {title[:40]}. Saltando.")
                    continue

                clean_text = clean_text[:12000]  # Límite por fuente

                sources.append({
                    "title": title,
                    "url": url,
                    "pub_date": pub_date,
                    "content": clean_text,
                    "formatted": f"FECHA: {pub_date}\nTÍTULO: {title}\nURL: {url}\nCONTENIDO:\n{clean_text}"
                })

            print(f"   ✅ Fuentes extraídas: {len(sources)}/{len(items)}")
            return sources

        except Exception as e:
            print(f"⚠️ Error en NewsFetcher: {e}")
            return []


# ============================================================================
# CAPA 4: ORQUESTADOR DE INVESTIGACIÓN
# ============================================================================

class Researcher:
    """
    Orquesta la investigación completa:
    1. Detecta tendencia del nicho
    2. Intenta Deep Research via NotebookLM MCP
    3. Fallback a scraping directo
    4. Retorna contexto estructurado para Gemini
    """

    def __init__(self):
        self.mcp = NotebookResearcher()
        self.use_mcp = self.mcp.connect()
        self.notebook_id = None

    def research_topic(self, keyword):
        """
        Pipeline completo de investigación.
        Retorna un string de contexto rico para pasar a Gemini.
        """
        print(f"\n{'='*60}")
        print(f"🔬 INVESTIGACIÓN PROFUNDA: '{keyword}'")
        print(f"{'='*60}")

        category = TrendDetector.detect_category(keyword)
        print(f"📁 Categoría detectada: {category.upper()}")

        # --- DETECCIÓN DE TENDENCIA ---
        trend = TrendDetector.get_trend_for_keyword(keyword)
        trend_context = ""
        if trend:
            trend_context = f"TENDENCIA ACTUAL DETECTADA:\nTítulo: {trend['title']}\nFecha: {trend.get('pub_date', 'N/A')}\n"

        # --- RUTA A: NotebookLM MCP (Deep Research) ---
        mcp_research = ""
        if self.use_mcp:
            mcp_research = self._research_via_mcp(keyword, category, trend)

        # --- RUTA B: Fallback Scraping ---
        scraping_context = ""
        if not mcp_research:
            scraping_context = self._research_via_scraping(keyword)

        # --- COMPOSICIÓN DEL CONTEXTO FINAL ---
        final_context = self._compose_context(
            keyword=keyword,
            category=category,
            trend_context=trend_context,
            mcp_research=mcp_research,
            scraping_context=scraping_context
        )

        # Cleanup
        self._cleanup()

        print(f"\n✅ INVESTIGACIÓN COMPLETADA ({len(final_context)} chars)")
        return final_context

    def _research_via_mcp(self, keyword, category, trend):
        """Intenta investigación profunda via NotebookLM MCP."""
        print("\n--- RUTA MCP: NotebookLM Deep Research ---")
        try:
            # 1. Crear Notebook temporal
            nb_id = self.mcp.create_research_notebook(keyword)
            if not nb_id:
                print("   ❌ No se pudo crear Notebook. Usando fallback.")
                return ""
            self.notebook_id = nb_id

            # 2. Recoger URLs de noticias (para inyectar como fuentes)
            news = NewsFetcher.get_news_sources(keyword, max_sources=5)
            urls_to_inject = [s["url"] for s in news if s.get("url")]

            # 3. Inyectar URLs en el Notebook
            if urls_to_inject:
                injected = self.mcp.inject_urls(nb_id, urls_to_inject)
                if injected == 0:
                    # Fallback: inyectar como texto
                    print("   ↩️ Inyección de URLs falló. Inyectando como texto...")
                    for src in news[:3]:
                        self.mcp.inject_text(
                            nb_id,
                            src["formatted"],
                            title=src["title"][:60]
                        )
                        time.sleep(1)

            # 4. También intentar Deep Research del MCP (busca web automáticamente)
            self.mcp.deep_research(nb_id, keyword)

            # 5. Esperar a que las fuentes se indexen
            time.sleep(5)

            # 6. INTERROGATORIO (RAG)
            result = self.mcp.interrogate(nb_id, category, keyword)
            if result and len(result) > 100:
                return result

            print("   ⚠️ Interrogatorio devolvió poco contenido.")
            return ""

        except Exception as e:
            print(f"   ❌ Error en flujo MCP: {e}")
            return ""

    def _research_via_scraping(self, keyword):
        """Fallback: Investigación via scraping directo."""
        print("\n--- RUTA FALLBACK: Scraping Directo ---")
        news = NewsFetcher.get_news_sources(keyword, max_sources=5)

        if not news:
            print("   ⚠️ Sin noticias. Gemini usará conocimiento general.")
            return ""

        formatted_sources = []
        for i, src in enumerate(news):
            formatted_sources.append(
                f"--- FUENTE {i+1} ---\n"
                f"Título: {src['title']}\n"
                f"Fecha: {src['pub_date']}\n"
                f"URL: {src['url']}\n"
                f"Contenido:\n{src['content'][:6000]}\n"
            )

        return "\n\n".join(formatted_sources)

    def _compose_context(self, keyword, category, trend_context, mcp_research, scraping_context):
        """Compone el contexto final estructurado."""
        parts = [
            f"TEMA DE INVESTIGACIÓN: {keyword}",
            f"CATEGORÍA: {category.upper()}",
            f"FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        ]

        if trend_context:
            parts.append(f"\n{trend_context}")

        if mcp_research:
            parts.append(f"\n📓 INVESTIGACIÓN PROFUNDA (NotebookLM - Basada en fuentes reales):\n{mcp_research}")
        elif scraping_context:
            parts.append(f"\n📰 FUENTES RECIENTES (Scraping Directo):\n{scraping_context}")
        else:
            parts.append("\n⚠️ No se encontraron fuentes recientes. Usa conocimiento general actualizado.")

        return "\n".join(parts)

    def _cleanup(self):
        """Limpieza post-investigación."""
        # Eliminar notebook temporal (no acumular basura)
        if self.notebook_id and self.use_mcp:
            self.mcp.cleanup(self.notebook_id)
        self.mcp.close()


# ============================================================================
# PRUEBA UNITARIA
# ============================================================================

if __name__ == "__main__":
    print("🧪 TEST: Investigador Multinivel")
    r = Researcher()
    result = r.research_topic("Inteligencia Artificial en Medicina 2026")
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    print("="*60)
    print(result[:2000])
