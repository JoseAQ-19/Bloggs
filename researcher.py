import os
import json
import subprocess
import requests
import xml.etree.ElementTree as ET
import re
import time
from datetime import datetime

# Configuración
MCP_PATH = "/Users/manolo/.local/bin/notebooklm-mcp"

class NotebookMCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 0
        self.is_connected = False

    def connect(self):
        """Inicia el proceso del servidor MCP y realiza el handshake."""
        try:
            print(f"🔌 Conectando al servidor MCP en: {MCP_PATH}...")
            self.process = subprocess.Popen(
                [MCP_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0 # Unbuffered para comunicación tiempo real
            )
            
            # 1. Handshake: Initialize
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "blog-automator", "version": "1.0"}
                },
                "id": self.request_id
            }
            self.send_request(init_req)
            resp = self.read_response()
            
            if not resp or "error" in resp:
                print(f"❌ Error en handshake MCP: {resp}")
                return False

            # 2. Handshake: Initialized Notification
            self.send_notification("notifications/initialized", {})
            
            self.is_connected = True
            print("✅ Conexión MCP Establecida (NotebookLLM).")
            return True
            
        except Exception as e:
            print(f"⚠️ Fallo al conectar con MCP (Modo Fallback Activado): {e}")
            return False

    def send_request(self, req):
        if not self.process: return
        json_str = json.dumps(req)
        self.process.stdin.write(json_str + "\n")
        self.process.stdin.flush()
        self.request_id += 1

    def send_notification(self, method, params):
        if not self.process: return
        req = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        json_str = json.dumps(req)
        self.process.stdin.write(json_str + "\n")
        self.process.stdin.flush()

    def read_response(self):
        if not self.process: return None
        try:
            line = self.process.stdout.readline()
            if not line: return None
            return json.loads(line)
        except Exception as e:
            print(f"Error leyendo respuesta MCP: {e}")
            return None

    def call_tool(self, name, arguments):
        if not self.is_connected: return None
        
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            },
            "id": self.request_id
        }
        self.send_request(req)
        return self.read_response()

    def close(self):
        if self.process:
            self.process.terminate()

class NewsFetcher:
    @staticmethod
    def get_trending_content(keyword):
        """Busca noticias en Google News RSS y extrae texto básico."""
        print(f"📰 Buscando noticias frescas sobre: {keyword}")
        try:
            # 1. Buscar en Google News RSS (Gratis)
            safe_kw = requests.utils.quote(keyword)
            rss_url = f"https://news.google.com/rss/search?q={safe_kw}&hl=es-419&gl=US&ceid=US:es-419"
            
            resp = requests.get(rss_url, timeout=10)
            if resp.status_code != 200: return []
            
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")[:3] # Top 3 noticias
            
            sources = []
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                pub_date = item.find("pubDate").text
                
                # 2. Intentar extraer contenido (Scraping ligero)
                print(f"   📥 Descargando: {title[:40]}...")
                try:
                    article_resp = requests.get(link, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                    # Limpieza muy básica de HTML a Texto
                    clean_text = re.sub(r'<[^>]+>', ' ', article_resp.text)
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    # Recortar para no saturar
                    clean_text = clean_text[:10000] 
                    
                    sources.append({
                        "title": title,
                        "url": link,
                        "content": f"FECHA: {pub_date}\nTÍTULO: {title}\nURL: {link}\nCONTENIDO:\n{clean_text}"
                    })
                except:
                    print(f"   ⚠️ No se pudo descargar contenido de {link}, saltando.")
            
            return sources
            
        except Exception as e:
            print(f"⚠️ Error en NewsFetcher: {e}")
            return []

class Researcher:
    def __init__(self):
        self.mcp = NotebookMCPClient()
        self.use_mcp = self.mcp.connect()

    def research_topic(self, keyword):
        """Orquesta la investigación: News -> Notebook -> RAG."""
        
        # 1. Obtener Fuentes Vivas (News)
        news_sources = NewsFetcher.get_trending_content(keyword)
        if not news_sources:
            print("⚠️ No se encontraron noticias recientes. Usando conocimiento general.")
        
        notebook_id = None
        research_summary = ""

        # 2. Inyectar en NotebookLLM (Si MCP funciona)
        if self.use_mcp and news_sources:
            try:
                # A. Crear Notebook
                print(f"📓 Creando Cuaderno de Investigación para '{keyword}'...")
                resp = self.mcp.call_tool("create_notebook", {"title": f"Investigación: {keyword} ({datetime.now().strftime('%Y-%m-%d')})"})
                
                # Manejo de respuesta MCP (puede variar según implementación del server)
                # Asumimos que devuelve el ID o un objeto notebook
                # DEBUG: Imprimir respuesta cruda para depuración si falla
                # print(f"DEBUG MCP CREATE: {resp}") 
                
                # Si la respuesta es exitosa (result -> content -> text/json)
                if resp and "result" in resp:
                    # Intentar parsear el ID del notebook de la respuesta (placeholder logic)
                    # La implementación actual de notebooklm-mcp devuelve texto confirmando.
                    # Asumiremos que el contexto activo se mantiene en el servidor o devuelve ID.
                    pass 
                
                # B. Añadir Fuentes
                for src in news_sources:
                    print(f"   📎 Añadiendo fuente al cuaderno: {src['title'][:30]}...")
                    # Usamos 'upload_source_text' o similar si existe, o pegamos texto
                    # Nota: La herramienta estándar suele ser 'add_source' o 'add_url'
                    # Vamos a probar pasarle el texto crudo como "copiado"
                    self.mcp.call_tool("add_source", {"source": src['content']})
                    time.sleep(1) # Cortesía

                # C. RAG (Interrogatorio)
                print("🧠 Interrogando al Cuaderno (RAG)...")
                query = f"""
                Analiza las fuentes proporcionadas sobre '{keyword}'.
                Genera un RESUMEN EJECUTIVO con:
                1. Los 5 Hechos más importantes.
                2. 3 Controversias o debates actuales.
                3. Lista de actores clave (empresas/personas).
                Cita las fuentes si es posible.
                """
                rag_resp = self.mcp.call_tool("query_notebook", {"query": query})
                
                if rag_resp and "result" in rag_resp:
                    # Extraer texto de la respuesta MCP
                    content_blocks = rag_resp["result"].get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            research_summary += block.get("text", "")
                            
                print("✅ Investigación MCP Completada.")

            except Exception as e:
                print(f"❌ Error durante flujo MCP: {e}. Usando fallback.")
                self.use_mcp = False # Desactivar para el resto
        
        self.mcp.close()

        # 3. Fallback / Construcción Final del Contexto
        if not research_summary:
            print("⚠️ Usando Fallback (Raw News + Gemini Knowledge).")
            # Concatenar las noticias crudas para que Gemini las procese directamente
            raw_text = "\n\n".join([s['content'] for s in news_sources])
            research_summary = f"RESUMEN DE NOTICIAS RECIENTES (SIN PROCESAR POR NOTEBOOKLM):\n{raw_text}"

        return research_summary

if __name__ == "__main__":
    # Prueba Unitaria
    r = Researcher()
    print(r.research_topic("Inteligencia Artificial en Medicina"))
