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
from exa_py import Exa

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
        geo_rules = """[GEO-RESEARCH: SPAIN MARKET ONLY]
- TARGET AUDIENCE: Readers in SPAIN (Madrid, Barcelona, Valencia, Bilbao). NOT Latin America.
- AVOID basic machine translations of US sources. We want FRESH data from SPANISH (Spain) native sources.
- PRIORITIZE domains: .es (mandatory), xataka.com, elpais.com, elmundo.es, genbeta.com, elconfidencial.com.
- DO NOT prioritize .mx, .ar, .co, or LatAm sources. Spain-first always.
- Internal search queries MUST be formulated in Peninsular Spanish ("ordenador" not "computadora", "móvil" not "celular").
- REGULATORY CONTEXT: Reference EU regulations (AI Act, GDPR), CNMV for crypto, Agencia Española de Protección de Datos."""
    else:
        geo_rules = """[GEO-RESEARCH: SILICON VALLEY / WALL STREET MARKET]
- TARGET AUDIENCE: US tech professionals, VCs, and Wall Street analysts.
- PRIORITIZE US-based high-authority sources ONLY. No UK (BBC Tech, The Guardian) or generic international.
- PRIORITIZE domains: .com (TechCrunch, The Verge, Ars Technica, WSJ), .gov (SEC, FTC, NIST), .edu (Stanford, MIT, CMU).
- Internal search queries MUST be formulated in advanced technical American English.
- REGULATORY CONTEXT: Reference SEC filings, FTC actions, US executive orders on AI, CFPB rulings."""

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
            current_id = self.request_id
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "researcher-v4-eeat", "version": "2.0"}
                },
                "id": current_id
            }
            self.send_request(init_req)
            resp = self.read_response(expected_id=current_id)
            
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

    def read_response(self, expected_id, timeout=30):
        if not self.process: return None
        
        import select
        
        start_time = time.time()
        while True:
            remaining = timeout - (time.time() - start_time)
            if remaining <= 0:
                print(f"⚠️ Timeout lectura MCP ({timeout}s) para request {expected_id}")
                return None
                
            reads, _, _ = select.select([self.process.stdout], [], [], remaining)
            
            if not reads:
                continue
                
            line = self.process.stdout.readline()
            if not line: return None
            
            line = line.strip()
            if not line: continue
            
            try:
                resp = json.loads(line)
                # Ensure it's JSON-RPC and matches our expected ID
                if "jsonrpc" in resp and resp.get("id") == expected_id:
                    return resp
            except json.JSONDecodeError:
                # Omitir basura o logs no-JSON de STDOUT del server MCP
                continue

    def call_tool(self, name, arguments, timeout=60):
        if not self.is_connected: return None
        current_id = self.request_id
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
            "id": current_id
        }
        self.send_request(req)
        return self.read_response(expected_id=current_id, timeout=timeout)

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
        exa_key = os.getenv("EXA_API_KEY")
        self.exa = Exa(exa_key) if exa_key else None
        self._exa_urls = []

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

    def _mine_deep_keywords(self, topic, lang, category="general"):
        """
        PROTOCOLO DEEP-KEYWORD MINER & TRIFORCE RESEARCH
        1. Prospección rápida en "Pozos de Conocimiento" reales vía Exa.
        2. LLM extrae Jerga, Nombres Propios y Controversias.
        3. Construye el Super-Prompt Triforce (Tendencia + Pregunta + Señal Social).
        """
        print(f"   ⛏️ [Deep-Keyword Miner] Prospectando pozos de conocimiento para '{topic}'...")
        
        snippets = "No extra data."
        if self.exa:
            # 1. Identificación de Pozos de Conocimiento: Foros y Quejas (GEO/SEO 2026 Information Gain)
            if lang == "es":
                query = f"'{topic}' ('quejas' OR 'problemas' OR 'dudas reales' OR 'experiencias' OR 'vale la pena') (site:reddit.com OR site:es.quora.com OR site:forocoches.com OR site:bandaancha.eu)"
                auth_query = f"'{topic}' (informe OR estudio OR estadisticas OR BOE OR 'datos oficiales') (site:.gov OR site:.edu OR site:un.org OR site:reuters.com OR site:bloomberg.com)"
            else:
                query = f"'{topic}' ('complaints' OR 'issues' OR 'real experiences' OR 'worth it' OR 'problems') (site:reddit.com OR site:quora.com OR site:news.ycombinator.com)"
                auth_query = f"'{topic}' (report OR study OR statistics OR whitepaper) (site:.gov OR site:.edu OR site:ieee.org OR site:nist.gov OR site:gartner.com OR site:reuters.com)"
                
            try:
                from datetime import datetime, timedelta
                start_date = (datetime.now() - timedelta(hours=72)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                # Búsqueda de Fricción Social
                res = self.exa.search(query, num_results=5, type="neural", start_published_date=start_date)
                social_urls = []
                if res and res.results:
                    social_urls = [{"title": r.title, "url": r.url} for r in res.results]
                
                # Búsqueda de Autoridad (E-E-A-T)
                res_auth = self.exa.search(auth_query, num_results=3, type="neural")
                auth_urls = []
                if res_auth and res_auth.results:
                    auth_urls = [{"title": r.title, "url": r.url} for r in res_auth.results]

                # ESLABÓN PERDIDO FIX: Capturar URLs reales de Exa para el writer
                self._exa_urls = social_urls + auth_urls
                
                if self._exa_urls:
                    print(f"   🔗 [Exa Triforce] {len(social_urls)} sociales + {len(auth_urls)} autoridad capturadas.")
                    snippets = "\n".join([f"- {r['title']}" for r in self._exa_urls])
                
            except Exception as e:
                print(f"   ⚠️ Exa mining fallback: {e}")


        if not self.client:
            return topic

        print("   🧠 [Triforce LLM] Extrayendo Entidades de Poder y generando Super-Query...")
        
        # 2 y 3: Extracción de Entidades y Triforce Builder
        prompt_lang = "Spanish" if lang == "es" else "English"
        
        prompt = f"""ACT AS: Senior OSINT Intelligence Analyst & Master Prompt Engineer.
We need to turn a generic topic into an 'Ultra-Specific Triforce Research Query' for a deep web crawler.

GENERIC TOPIC: "{topic}"
LANGUAGE TARGET: {prompt_lang}

QUICK PROSPECTING RESULTS (Raw clues from Exa):
{snippets}

STEP 1: INTERNAL ANALYSIS (Do not output this part)
Identify from the topic and clues:
- Jargon: Technical terms only insiders use.
- Controversies: Current painful debates or complaints.
- Power Entities: High-profile names, companies, or researchers.

STEP 2: THE TRIFORCE FRAMEWORK (Your Output)
Construct exactly ONE powerful, highly optimized search query string using this 3-part formula:
[Trend Angle (novel/predictive)] + [Critical Question (deepest technical/user doubt)] + [Social Signal/Jargon (e.g. mention forums or controversies)].

ANTI-WIKIPEDIA VALIDATION RULE:
If the topic is generic like a dictionary definition, MUST add terms like "unpopular opinion", "technical breakdown", "expert debate", or "real-world failure case".

EXAMPLE OF TRIFORCE QUERY:
Bad: "Paneles Solares"
Good: "Degradación de paneles solares perovskita a 10 años merece la pena la inversión frente a silicio quejas mantenimiento Reddit r/solar"

OUTPUT FORMAT:
Return ONLY the final string. NO quotation marks. NO markdown. NO explanations. MUST be in {prompt_lang}.
"""
        try:
            resp = self.client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            super_query = resp.text.strip().replace('"', '').split('\n')[0]
            if len(super_query) > 10:
                print(f"   🔥 [Triforce Query] -> {super_query[:100]}...")
                return super_query
        except Exception as e:
            print(f"   ⚠️ Gemini Triforce fallback: {e}")

        return topic + (" technical debate Reddit" if lang == "en" else " debate técnico Reddit")

    def research(self, topic, category="general", search_context="", lang="es"):
        """
        Pipeline de investigación con 3 capas de fallback.
        Ahora recibe topic, category y search_context por separado, Y IDIOMA (Geo-Research).
        """
        print(f"\n🔍 INICIANDO GEO-RESEARCH E-E-A-T PARA: '{topic}' [{lang.upper()}]")
        print(f"   Categoría: {category} | Contexto: {search_context[:60]}...")
        
        # Reset state
        self._exa_urls = []

        # --- NUEVO: DEEP-KEYWORD MINER & TRIFORCE ---
        super_topic = self._mine_deep_keywords(topic, lang, category)
        
        # Construir el Brief de investigación estructurado localizado
        research_brief = build_research_query(super_topic, category, search_context, lang=lang)
        
        # 🥇 CAPA 1: NOTEBOOKLM DEEP RESEARCH
        result = self._layer_1_notebooklm(super_topic, research_brief, lang, category=category)
        if result: return result
        
        # 🥈 CAPA 2: GEMINI GROUNDING (con brief E-E-A-T)
        result = self._layer_2_gemini_grounding(super_topic, research_brief, lang)
        if result: return result
        
        # 🥉 CAPA 3: SCRAPING CLÁSICO (pasamos el topic simple original para evitar romper Google News RSS)
        return self._layer_3_classic_scraping(topic, lang)

    # =============================================
    # SUBQUERIES ESPECIALIZADAS POR NICHO
    # Cada nicho busca datos en el idioma de su industria
    # =============================================
    NICHE_SUBQUERIES = {
        "ia": {
            "en": [
                "{topic} API pricing context window benchmark Llama-3 Claude-3.5 GPT-4o parameters",
                "{topic} technical architecture GPU compute cost H100 inference latency",
                "{topic} GitHub issues limitations criticism real-world failure production bugs"
            ],
            "es": [
                "{topic} precio API tokens benchmark Llama Claude GPT-4o parámetros comparativa",
                "{topic} arquitectura técnica hardware contexto GPU consumo eléctrico coste inferencia",
                "{topic} problemas reales limitaciones GitHub producción fallos críticas técnicas"
            ]
        },
        "crypto": {
            "en": [
                "{topic} on-chain data TVL whale movement Dune Analytics",
                "{topic} tokenomics vesting schedule insider selling funding",
                "{topic} SEC regulation lawsuit risk class action"
            ],
            "es": [
                "{topic} datos on-chain TVL movimiento ballenas Dune Analytics",
                "{topic} tokenomics calendario vesting venta insiders financiación",
                "{topic} regulación SEC demanda riesgo legal"
            ]
        },
        "fitness": {
            "en": [
                "{topic} randomized controlled trial pubmed meta-analysis sample size",
                "{topic} real athlete protocol training program sets reps dosage",
                "{topic} side effects contraindication risk long-term safety"
            ],
            "es": [
                "{topic} ensayo clínico controlado pubmed meta-análisis muestra",
                "{topic} protocolo atleta entrenamiento programa series repeticiones dosis",
                "{topic} efectos secundarios contraindicación riesgo seguridad largo plazo"
            ]
        },
        "youtube": {
            "en": [
                "{topic} subscriber count views revenue earnings socialblade",
                "{topic} brand deal sponsor controversy backlash response",
                "{topic} audience reaction community post comment sentiment"
            ],
            "es": [
                "{topic} suscriptores visualizaciones ingresos estimados",
                "{topic} acuerdo marca patrocinio polémica reacción respuesta",
                "{topic} reacción audiencia comentarios sentimiento comunidad"
            ]
        },
        "viral": {
            "en": [
                "{topic} Google Trends data spike origin first post",
                "{topic} sociological analysis Gen Z behavior Pew Research",
                "{topic} criticism backlash dying trend counter movement"
            ],
            "es": [
                "{topic} Google Trends datos pico origen primer post",
                "{topic} análisis sociológico generación Z comportamiento Pew Research",
                "{topic} crítica reacción contra tendencia declive"
            ]
        }
    }

    def _layer_1_notebooklm(self, topic, research_brief, lang, category="general"):
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
            # PASO 1: MULTIPLE FAST RESEARCH QUERIES
            # Subqueries especializadas por nicho + idioma
            # =============================================
            niche_queries = self.NICHE_SUBQUERIES.get(category, self.NICHE_SUBQUERIES.get("ia", {}))
            lang_queries = niche_queries.get(lang, niche_queries.get("en", [
                "{topic} specific data statistics",
                "{topic} expert opinion case study",
                "{topic} criticism risk controversy"
            ]))
            
            subqueries = [q.format(topic=topic[:100]) for q in lang_queries]
            print(f"   🎯 [Niche Research] Categoría: {category} | {len(subqueries)} subqueries especializadas")
            
            timestamp = int(time.time())
            
            for index, sq in enumerate(subqueries):
                print(f"   🚀 [{index+1}/{len(subqueries)}] Iniciando FAST research ({sq[:60]}...)...")
                start_params = {
                    "query": sq,
                    "mode": "fast",
                    "source": "web"
                }
                
                if notebook_id:
                    start_params["notebook_id"] = notebook_id
                else:
                    start_params["title"] = f"EEAT-{topic[:20].replace(' ', '-')}-{lang}-{timestamp}"
                
                start_resp = mcp.call_tool("research_start", start_params)
                
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
                
                if not notebook_id:
                    notebook_id = data.get("notebook_id")
                    if notebook_id: print(f"   📓 Notebook ID: {notebook_id}")
                
                task_id = data.get("task_id")
                
                if not notebook_id or not task_id:
                    print(f"      ❌ Error al iniciar subquery: {data.get('message', 'Sin datos')}")
                    continue
                    
                print(f"      🕵️ Esperando Fast Research (Task: {task_id[:8]}...)")
                
                # POLLING LIGERO
                max_retries = 15  # 15 * 5s = 75s (Fast es ~30s)
                completed = False
                
                for i in range(max_retries):
                    time.sleep(5)
                    status_resp = mcp.call_tool("research_status", {
                        "task_id": task_id, 
                        "notebook_id": notebook_id,
                        "max_wait": 0
                    }, timeout=15)
                    
                    status_data = {}
                    if status_resp and "result" in status_resp:
                         res = status_resp["result"]
                         if "structuredContent" in res:
                             status_data = res["structuredContent"]
                         elif "content" in res:
                             try:
                                 status_data = json.loads(res["content"][0]["text"])
                             except: pass
                    
                    research_obj = status_data.get("research", {})
                    state = research_obj.get("status", status_data.get("status", "unknown"))
                    sources = research_obj.get("source_count", "?")
                    print(f"         ⏳ Estado: {state} | Fuentes encontradas: {sources}")
                    
                    if state in ["completed", "success"]:
                        completed = True
                        break
                    elif state == "failed":
                        break
                        
                if not completed:
                    print("      ⚠️ Timeout fast research. Importando de todas formas...")

                # =============================================
                # PASO 2: IMPORTAR FUENTES DESCUBIERTAS
                # =============================================
                print("      📥 Importando fuentes descubiertas al notebook...")
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
            }, timeout=300)
            
            # Extraer respuesta
            final_content = ""
            if query_resp and "result" in query_resp and "content" in query_resp["result"]:
                for block in query_resp["result"]["content"]:
                    if block.get("type") == "text":
                        final_content += block.get("text", "")

            if len(final_content) > 500:
                # ESLABÓN PERDIDO FIX: Append Exa URLs to Layer 1 output
                exa_urls = getattr(self, '_exa_urls', [])
                if exa_urls:
                    exa_block = "\n\n### FUENTES VALIDADAS DISPONIBLES:\n"
                    for src in exa_urls:
                        exa_block += f"- [{src['title']}]({src['url']})\n"
                    final_content += exa_block
                    print(f"   🔗 [Exa→Layer1] {len(exa_urls)} URLs inyectadas en informe NotebookLM.")
                
                print(f"   ✅ ÉXITO CAPA 1: Informe E-E-A-T generado ({len(final_content)} chars).")
                return {
                    "content": final_content,
                    "layer": "NotebookLM Deep Research (E-E-A-T V2)",
                    "notebook_id": notebook_id,
                    "sources": [s['url'] for s in exa_urls] if exa_urls else ["NotebookLM Deep Search — see Source URLs in report"]
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
CRITICAL: Do NEVER output internal Google Search links (like vertexaisearch.cloud.google.com). You MUST extract and provide the direct, ORIGINAL public URL to the website (e.g. https://www.bloomberg.com/..., https://www.nature.com/articles/...). Do NOT fabricate URLs — only include REAL public sources you actually found. If you cannot find a public URL, include the plaintext source name.
"""
            
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            
            resp = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(tools=[google_search_tool])
            )
            
            if resp.text and len(resp.text) > 300:
                # ESLABÓN PERDIDO FIX: Extraer URLs reales de grounding_metadata
                grounding_urls = []
                try:
                    for candidate in resp.candidates:
                        gm = getattr(candidate, 'grounding_metadata', None)
                        if gm:
                            chunks = getattr(gm, 'grounding_chunks', None) or []
                            for chunk in chunks:
                                web = getattr(chunk, 'web', None)
                                if web:
                                    uri = getattr(web, 'uri', '')
                                    title = getattr(web, 'title', '') or getattr(web, 'domain', '')
                                    if uri and 'vertexaisearch' not in uri:
                                        grounding_urls.append({"title": title, "url": uri})
                except Exception as e:
                    print(f"   ⚠️ Grounding metadata extraction warning: {e}")
                
                # Construir bloque de fuentes validadas
                sources_block = ""
                seen = set()
                if grounding_urls:
                    sources_block = "\n\n### FUENTES VALIDADAS DISPONIBLES:\n"
                    for src in grounding_urls:
                        if src['url'] not in seen:
                            sources_block += f"- [{src['title']}]({src['url']})\n"
                            seen.add(src['url'])
                    print(f"   🔗 [Grounding URLs] {len(seen)} URLs reales extraídas de grounding_metadata.")
                
                # También agregar URLs de Exa si existen
                exa_urls = getattr(self, '_exa_urls', [])
                if exa_urls:
                    if not sources_block:
                        sources_block = "\n\n### FUENTES VALIDADAS DISPONIBLES:\n"
                    for src in exa_urls:
                        if src['url'] not in seen:
                            sources_block += f"- [{src['title']}]({src['url']})\n"
                            seen.add(src['url'])
                    print(f"   🔗 [Exa URLs] URLs de Exa agregadas al bloque de fuentes.")
                
                print(f"   ✅ ÉXITO CAPA 2: Grounding completado ({len(resp.text)} chars).")

                # Combinar fuentes para el reporte
                all_sources = [s['url'] for s in grounding_urls]
                all_sources.extend([s['url'] for s in exa_urls])

                return {
                    "content": f"{resp.text}{sources_block}",
                    "layer": "Gemini Grounding (E-E-A-T V2)",
                    "sources": all_sources[:15] if all_sources else ["Gemini Google Search Grounding"]
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
                rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=es-ES&gl=ES&ceid=ES:es"
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
