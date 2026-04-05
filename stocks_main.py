#!/usr/bin/env python3
"""
STOCKS_MAIN.PY — Orquestador del Pipeline de Fondos de Inversión
=================================================================
Pipeline independiente: Scout → Writer para ambos idiomas (ES y EN).
Crea los directorios content/es/funds/ y content/en/funds/ y guarda
los artículos .md generados con timestamp en el nombre.

REGLA DE ORO: Este archivo NO importa ni modifica NADA del núcleo existente.
"""

import os
import sys
import re
import json
import time
import hashlib
import argparse
import logging
import random
import glob
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Asegurar que los módulos de stocks bajo scripts/ son importables
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Imports del módulo stocks (aislados)
from stocks_scout import scout_funds
from stocks_writer import write_fund_article
from stocks_instructions import DISCLAIMERS, NICHE_CONFIG

# NotebookLM MCP — Deep Research Layer (importado del núcleo)
try:
    from researcher import NotebookMCPClient, build_research_query
    HAS_NOTEBOOK_MCP = True
except ImportError:
    HAS_NOTEBOOK_MCP = False

# Gemini para meta description (opcional)
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    from google import genai
    gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
except Exception:
    gemini_client = None

# Imagen por defecto (se intentará usar novum_visual si está disponible)
try:
    from novum_visual import get_image
    HAS_VISUAL = True
except ImportError:
    HAS_VISUAL = False

# Google Indexing API (si está disponible)
try:
    import indexing_api
    HAS_INDEXING = True
except ImportError:
    HAS_INDEXING = False

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ============================================================
# CONSTANTES
# ============================================================

CONTENT_DIR_ES = "content/es/funds"
CONTENT_DIR_EN = "content/en/funds"
COMPLETED_FILE = "data/completed.txt"

# ============================================================
# UTILIDADES
# ============================================================

def _ensure_directories():
    """Crea los directorios de contenido si no existen."""
    os.makedirs(CONTENT_DIR_ES, exist_ok=True)
    os.makedirs(CONTENT_DIR_EN, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    print("   Directorios verificados:")
    print(f"      OK {CONTENT_DIR_ES}")
    print(f"      OK {CONTENT_DIR_EN}")


def _create_index_files():
    """Crea archivos _index.md para Hugo si no existen."""
    for lang, content_dir in [("es", CONTENT_DIR_ES), ("en", CONTENT_DIR_EN)]:
        index_path = os.path.join(content_dir, "_index.md")
        if not os.path.exists(index_path):
            if lang == "es":
                index_content = """---
title: "Fondos de Inversión y Stocks"
description: "Análisis profesional de fondos de inversión, ETFs y mercados financieros. Comparativas de rendimiento, comisiones y opiniones de expertos."
---
"""
            else:
                index_content = """---
title: "Investment Funds & Stocks"
description: "Professional analysis of mutual funds, ETFs, and financial markets. Performance comparisons, fees, and expert opinions."
---
"""
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            print(f"   Creado: {index_path}")


def _generate_translation_key(title):
    """Genera una clave de traducción determinista basada en el título."""
    raw = title.strip().lower()
    t_hash = hashlib.md5(raw.encode('utf-8')).hexdigest()
    return f"{t_hash[:8]}-{t_hash[8:12]}-{t_hash[12:16]}-{t_hash[16:20]}-{t_hash[20:]}"


def _get_image(title, content, slug, category="funds"):
    """Intenta generar imagen con novum_visual, fallback a default."""
    if HAS_VISUAL:
        try:
            img = get_image(title, content, slug, category)
            if img and not img.startswith("http"):
                return img
        except Exception as e:
            logging.warning(f"novum_visual error: {e}")
    
    return f"/images/defaults/default-funds.jpg"


def _build_funds_footer(current_slug, lang, body_text):
    """Genera un footer determinista para fondos (metodología, fuentes, relacionados).

    - Respeta el disclaimer ya inyectado por stocks_writer (no añade otro).
    - Solo añade bloques si no existen ya marcadores de footer en el cuerpo.
    """
    try:
        import frontmatter
    except ImportError:
        # Sin frontmatter omitimos relacionados pero aún podemos devolver metodología/fuentes.
        frontmatter = None

    # Evitar doble inyección si ya existe footer estructurado
    footer_markers = [
        "## Metodología y Fuentes",
        "## Methodology and Sources",
        "## Artículos Relacionados",
        "## Related Articles",
    ]
    if any(marker in body_text for marker in footer_markers):
        return ""

    parts = []

    # 1) Metodología (copiado de content_engine_pro.generate_footer)
    meth_es = "\n\n## Metodología y Fuentes\nEste artículo fue analizado y validado por el equipo de investigadores de NovumWorld. Los datos provienen estrictamente de métricas actualizadas, regulaciones institucionales y canales de análisis autorizados para asegurar que el contenido cumpla con el estándar más alto de calidad y autoridad (E-E-A-T) de la industria."
    meth_en = "\n\n## Methodology and Sources\nThis article was analyzed and validated by the NovumWorld research team. The data strictly originates from updated metrics, institutional regulations, and authoritative analytical channels to ensure the content meets the industry's highest quality and authority standard (E-E-A-T)."
    methodology = meth_es if lang == "es" else meth_en
    parts.append(methodology)

    # 2) Fuentes específicas desde el Link Deposit (data/source_links_{lang}.json)
    sources_block = ""
    sources_file = f"data/source_links_{lang}.json"
    urls = []
    try:
        if os.path.exists(sources_file):
            with open(sources_file, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
                urls = data.get(current_slug, []) or []
    except Exception:
        urls = []

    if urls:
        # Limitar a las 5 primeras para no saturar el footer
        limited = urls[:5]
        if lang == "es":
            header = "\n\n### Fuentes utilizadas en este análisis\n"
            intro = "A continuación se listan algunas de las fuentes verificadas utilizadas para este artículo:\n"
        else:
            header = "\n\n### Sources used for this analysis\n"
            intro = "Below are some of the verified sources used for this article:\n"
        lines = "".join([f"- {u}\n" for u in limited])
        sources_block = header + intro + lines
        parts.append(sources_block)

    # 3) Artículos relacionados internos (solo si hay suficientes candidatos)
    related_block = ""
    if frontmatter is not None:
        content_dir = CONTENT_DIR_ES if lang == "es" else CONTENT_DIR_EN
        pattern = os.path.join(content_dir, "*.md")
        candidates = []

        for path in glob.glob(pattern):
            base = os.path.basename(path)
            if base.startswith("_index"):
                continue
            try:
                post = frontmatter.load(path)
            except Exception:
                continue

            slug = post.get("slug") or os.path.splitext(base)[0]
            if not slug or slug == current_slug:
                continue

            title = post.get("title") or post.get("titulo") or slug.replace("-", " ").title()
            if not title:
                continue

            candidates.append((title, slug))

        random.shuffle(candidates)
        selected = candidates[:3]

        # Requerimos al menos 2 artículos para que la sección tenga sentido
        if len(selected) >= 2:
            if lang == "es":
                header = "\n\n## Artículos Relacionados\n"
            else:
                header = "\n\n## Related Articles\n"

            links_lines = []
            for title, slug in selected:
                if lang == "es":
                    url = f"/es/funds/{slug}/"
                else:
                    # En inglés el path público de fondos es /funds/slug/
                    url = f"/funds/{slug}/"
                links_lines.append(f"- [{title}]({url})")

            related_block = header + "\n".join(links_lines) + "\n"
            parts.append(related_block)

    if not parts:
        return ""

    return "".join(parts) + "\n"


def _save_article(writer_output, lang):
    """
    Guarda el artículo generado como archivo .md con frontmatter Hugo.
    Incluye timestamp en el nombre del archivo.
    """
    if not writer_output:
        return None

    meta = writer_output["meta"]
    content = writer_output["content"]
    
    # Directorio de destino
    output_dir = CONTENT_DIR_ES if lang == "es" else CONTENT_DIR_EN
    
    # Nombre con timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{meta['slug']}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Imagen
    imagen = _get_image(meta["titulo"], content, meta["slug"])
    
    # Fecha con backdating ligero (como hace main.py)
    now = datetime.now()
    backdate = random.randint(15, 30) if lang == "es" else random.randint(2, 10)
    date_str = (now - timedelta(minutes=backdate)).strftime("%Y-%m-%dT%H:%M:%S")
    
    # Translation key
    trans_key = _generate_translation_key(meta["titulo"])
    
    # Description
    description = meta.get("description", "")
    if not description:
        description = re.sub(r'[#*\[\]]', '', content)[:154].replace('\n', ' ').strip() + '.'
    
    clean_title = meta['titulo'].replace('"', '').replace('\\$', '$').replace('\\[', '[').replace('\\]', ']')
    clean_desc = description.replace('"', "'").replace('\\$', '$').replace('\\[', '[').replace('\\]', ']')
    
    # Frontmatter YAML original
    front_matter = f"""---
title: "{clean_title}"
date: {date_str}
draft: false
description: "{clean_desc}"
featured_image: "{imagen}"
tags: ["Funds & Stocks"]
categories: ["funds"]
type: "funds"
language: "{lang}"
translationKey: "{trans_key}"
---
"""
    
    # VALIDACIÓN ESTRICTA DEL YAML ANTES DE GUARDADO (P0)
    import yaml
    try:
        yaml_content = front_matter.strip().strip('-').strip()
        yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        print(f"   [YAML ERROR] Se detectó bloque corrupto: {e}. Auto-regenerando seguro...")
        safe_meta = {
            "title": clean_title,
            "date": date_str,
            "draft": False,
            "description": clean_desc,
            "featured_image": imagen,
            "tags": ["Funds & Stocks"],
            "categories": ["funds"],
            "type": "funds",
            "language": lang,
            "translationKey": trans_key
        }
        yaml_str = yaml.dump(safe_meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
        front_matter = f"---\n{yaml_str}---\n"

    clean_titulo = meta['titulo'].replace('\"', '')

    # Footer blindado específico para fondos (metodología, fuentes, relacionados)
    footer = _build_funds_footer(meta["slug"], lang, content)
    final_body = content + footer

    final_content = f"{front_matter}\n![{clean_titulo}]({imagen})\n\n{final_body}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"   Guardado: {filepath}")
    print(f"   Translation Key: {trans_key}")
    
    # Notificar a Google Indexing API
    if HAS_INDEXING:
        if lang == "es":
            final_url = f"https://novumworld.com/es/funds/{meta['slug']}/"
        else:
            final_url = f"https://novumworld.com/funds/{meta['slug']}/"
        try:
            indexing_api.notify_google(final_url)
        except Exception as e:
            logging.warning(f"Indexing API error: {e}")
    
    return filepath


def _mark_completed(topic, category="funds"):
    """Marca el tema como completado en el registro."""
    os.makedirs("data", exist_ok=True)
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{category}: {topic}\n")

def _guardar_fuentes(slug, sources, lang="es"):
    """Link Deposit local para funds."""
    if not sources: return
    try:
        os.makedirs("data", exist_ok=True)
        # DECOUPLED: Usar fichero por idioma
        file_path = f"data/source_links_{lang}.json"
        data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try: data = json.load(f)
                except: pass
        data[slug] = sources
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"   [Link Deposit] {len(sources)} fuentes guardadas para {slug} [{lang}]")
    except Exception as e:
        print(f"   [Link Deposit] Error: {e}")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run_pipeline(lang=None):
    """
    Ejecuta el pipeline completo Scout → Writer para fondos de inversión.
    
    Args:
        lang: 'es', 'en', o None (ambos idiomas)
    """
    print("\n" + "=" * 70)
    print("STOCKS/FUNDS PIPELINE — Orquestador Independiente")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Idioma: {lang.upper() if lang else 'AMBOS (ES + EN)'}")
    print("=" * 70)

    # Crear directorios y archivos de índice
    _ensure_directories()
    _create_index_files()

    # Determinar idiomas a procesar
    languages = [lang] if lang else ["es", "en"]
    results = []

    for current_lang in languages:
        print(f"\n{'-' * 50}")
        print(f"PROCESANDO: {current_lang.upper()}")
        print(f"{'-' * 50}")

        # === FASE 1: SCOUT ===
        print(f"\n   [FASE 1] Ejecutando Scout Financiero ({current_lang.upper()})...")
        try:
            scout_data = scout_funds(lang=current_lang)
        except Exception as e:
            print(f"   [Scout] Error fatal: {e}")
            if os.environ.get("GITHUB_ACTIONS") == "true":
                print("   Ejecución en GitHub Actions. EXIT 1.")
                sys.exit(1)
            continue

        if not scout_data or not scout_data.get("topics"):
            print(f"   [Scout] No se encontraron temas para {current_lang.upper()}. Saltando...")
            continue

        # === FASE 1.5: NOTEBOOKLM DEEP RESEARCH (NEW) ===
        notebook_research = ""
        notebook_urls = []
        if HAS_NOTEBOOK_MCP:
            topic_title = scout_data["topics"][0]["title"]
            print(f"\n   [FASE 1.5] NotebookLM Deep Research: '{topic_title[:60]}...'")
            mcp_client = NotebookMCPClient()
            try:
                if mcp_client.connect():
                    # Build a financial research brief
                    finance_queries = [
                        f"{topic_title} mutual fund ETF performance data {current_lang}",
                        f"{topic_title} expert analysis Morningstar ratings fees",
                        f"{topic_title} risks controversy regulatory impact"
                    ]
                    
                    # Create temporary notebook
                    ts = datetime.now().strftime('%H%M%S')
                    nb_title = f"FUNDS-{topic_title[:30]}-{current_lang}-{ts}"
                    nb_result = mcp_client.call_tool("notebook_create", {"title": nb_title})
                    notebook_id = None
                    if nb_result and isinstance(nb_result, dict):
                        notebook_id = nb_result.get("notebook_id") or nb_result.get("id")
                    
                    if notebook_id:
                        print(f"   📓 Notebook creado: {notebook_id[:16]}...")
                        
                        # Execute research queries
                        for q in finance_queries:
                            try:
                                mcp_client.call_tool("research_start", {
                                    "notebook_id": notebook_id,
                                    "query": q,
                                    "source": "web",
                                    "mode": "fast"
                                })
                                # Poll for completion (max 60s per query)
                                for _ in range(12):
                                    time.sleep(5)
                                    status = mcp_client.call_tool("research_poll", {
                                        "notebook_id": notebook_id
                                    })
                                    if status and isinstance(status, dict):
                                        if status.get("status") in ["complete", "done", "COMPLETE"]:
                                            # Import discovered sources
                                            sources = status.get("sources", [])
                                            if sources:
                                                mcp_client.call_tool("research_import", {
                                                    "notebook_id": notebook_id,
                                                    "task_id": status.get("task_id", ""),
                                                    "sources": sources
                                                })
                                                # Extract URLs from sources
                                                for src in sources:
                                                    url = src.get("url", "") if isinstance(src, dict) else ""
                                                    if url and url.startswith("http"):
                                                        notebook_urls.append(url)
                                            break
                                print(f"   Research query completada: '{q[:50]}...'")
                            except Exception as qe:
                                print(f"   Research query error: {qe}")
                        
                        # Extract E-E-A-T financial report
                        eeat_prompt = f"""Provide a comprehensive investment research report on: {topic_title}

Include:
1. EXECUTIVE SUMMARY: Key findings with specific data points
2. PERFORMANCE DATA: Fund/ETF returns, Sharpe ratios, expense ratios with exact numbers
3. EXPERT OPINIONS: Named analysts and their specific recommendations
4. RISKS & CONTROVERSIES: Regulatory concerns, hidden fees, underperformance
5. VERIFIED SOURCE URLS: List all URLs from the sources you found

Be specific. Include real numbers, names, and dates. No vague statements."""
                        
                        try:
                            query_result = mcp_client.call_tool("notebook_query", {
                                "notebook_id": notebook_id,
                                "query": eeat_prompt
                            })
                            if query_result and isinstance(query_result, dict):
                                notebook_research = query_result.get("answer", "") or query_result.get("text", "")
                                if notebook_research:
                                     print(f"   [NotebookLM] E-E-A-T report: {len(notebook_research)} chars")
                        except Exception as qe:
                             print(f"   [NotebookLM] Query error: {qe}")
                        
                        # Cleanup: delete temporary notebook
                        try:
                            mcp_client.call_tool("notebook_delete", {
                                "notebook_id": notebook_id,
                                "confirm": True
                            })
                            print(f"   Notebook temporal eliminado")
                        except Exception:
                            pass
                    else:
                        print(f"   [NotebookLM] No se pudo crear notebook")
                else:
                    print(f"   [NotebookLM] Sin auth o binario. Saltando Capa 1.")
            except Exception as e:
                print(f"   [NotebookLM] Error: {e}. Continuando sin Capa 1.")
            finally:
                try:
                    mcp_client.close()
                except Exception:
                    pass
        else:
            print(f"   [NotebookLM] No disponible. Usando solo datos del Scout.")
        
        # Enrich scout_data with NotebookLM research
        if notebook_research:
            scout_data["notebooklm_research"] = notebook_research
            scout_data["verified_urls"] = notebook_urls
            print(f"   Scout enriquecido con {len(notebook_research)} chars de NotebookLM + {len(notebook_urls)} URLs")

        # === FASE 2: WRITER ===
        print(f"\n   [FASE 2] Ejecutando Writer Financiero ({current_lang.upper()})...")
        try:
            writer_output = write_fund_article(scout_data, lang=current_lang)
        except Exception as e:
            print(f"   [Writer] Error fatal: {e}")
            continue

        if not writer_output:
            print(f"   [Writer] No se generó artículo para {current_lang.upper()}.")
            continue

        # === FASE 3: GUARDAR ===
        print(f"\n   [FASE 3] Guardando artículo ({current_lang.upper()})...")
        
        # Guardar Link Deposit
        if "verified_urls" in scout_data and scout_data["verified_urls"]:
            _guardar_fuentes(writer_output["meta"]["slug"], scout_data["verified_urls"], lang=current_lang)
            
        filepath = _save_article(writer_output, current_lang)

        if filepath:
            _mark_completed(writer_output["meta"]["titulo"], category="funds")
            results.append({
                "lang": current_lang,
                "title": writer_output["meta"]["titulo"],
                "slug": writer_output["meta"]["slug"],
                "filepath": filepath,
                "word_count": writer_output["word_count"],
                "disclaimer": writer_output["disclaimer_injected"]
            })
            print(f"\n   [{current_lang.upper()}] ¡Artículo publicado exitosamente!")
        else:
            print(f"   Error guardando el artículo para {current_lang.upper()}.")

    # === RESUMEN FINAL ===
    print(f"\n{'=' * 70}")
    print("RESUMEN DE EJECUCIÓN")
    print(f"{'=' * 70}")
    
    if results:
         for r in results:
             disclaimer_status = "Disclaimer inyectado" if r["disclaimer"] else "SIN DISCLAIMER"
             print(f"   [{r['lang'].upper()}] {r['title']}")
             print(f"         {r['filepath']}")
             print(f"         {r['word_count']} palabras | {disclaimer_status}")
    else:
         print("   No se generaron artículos en esta ejecución.")
    
    print(f"\n{'=' * 70}")
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stocks/Funds Pipeline — Orquestador Independiente"
    )
    parser.add_argument(
        '--lang', type=str, choices=['es', 'en'], default=None,
        help='Force language: es (Spain) or en (US). Default: both.'
    )
    args = parser.parse_args()

    run_pipeline(lang=args.lang)
