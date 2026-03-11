"""
qa_editor_es.py — Editor Jefe QA para artículos en Español (España).

Cerebro nativo peninsular: lee un borrador .md generado por el Writer,
lo corrige (estilo, SEO, frases vetadas, enlaces muertos, fact-check
via NotebookLM) y devuelve la versión final.

Uso:
    from qa_editor_es import run as run_editor_es
    result = run_editor_es(category="ia")
"""

import os
import re
import json
import glob
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === IMPORTS PROPIOS ===
from qa_link_validator import validate_links

# === LLM CLIENTS ===
from openai import OpenAI
from google import genai
from google.genai import types

# === CONFIGURACIÓN LLM ===
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPEN_CORRECTOR_KEY = os.getenv("OPEN_CORRECTOR_API_KEY")
CORRECTOR_HF_KEY = os.getenv("CORRECTOR_HF_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# NotebookLM MCP
MCP_BINARY = "notebooklm-mcp"

# =====================================================
# TAREA B1: SYSTEM PROMPT DEL EDITOR JEFE ES
# =====================================================

SYSTEM_PROMPT_EDITOR_ES = """ROL: Eres el EDITOR JEFE de NovumWorld España. Tu misión es recibir un BORRADOR de artículo ya escrito por un redactor junior y devolverlo PERFECTO para publicación inmediata.

TU PERFIL:
- Periodista veterano español (Peninsular, NO LatAm) con 20 años en El País, elDiario.es y Xataka.
- Cínico, exigente, alérgico a la paja corporativa y a la prosa de ChatGPT.
- Experto en SEO on-page para el mercado español (.es).
- Tu castellano es impecable: distingues "ordenador" de "computadora", "móvil" de "celular".

TU MISIÓN (en este orden de prioridad):
1. IDIOMA PURO: Si encuentras CUALQUIER frase, título o párrafo en inglés, TRADÚCELO al castellano peninsular. Excepción: nombres propios (ChatGPT, Bitcoin, OpenAI).
2. ENLACES MUERTOS: Te proporcionaré una lista de enlaces que han dado error 404/timeout. DEBES:
   - Eliminar el enlace markdown roto: convertir [texto](url_muerta) en **texto** (negrita, sin enlace).
   - NUNCA inventes una URL nueva. Si no tienes el enlace real, déjalo en negrita.
3. FRASES VETADAS: Busca y ELIMINA (reemplazándolas por contenido equivalente más original) estas frases:
   - "En el vertiginoso mundo de..."
   - "En resumen / En conclusión" 
   - "Un arma de doble filo"
   - "Navegar por el panorama de..."
   - "Es importante destacar que..."
   - "promete revolucionar"
   - "crecimiento explosivo"
   - "inmersión profunda"
   - "el panorama actual"
   - "a medida que avanzamos"
   - "solo el tiempo lo dirá"
   - "Aquí está el texto reescrito"
4. FACT-CHECK: Si te proporciono alertas de verificación (de NotebookLM), revisa las afirmaciones señaladas y:
   - Si el dato es claramente inventado, elimínalo o sustitúyelo por uno general verificable.
   - Si el dato es sospechoso pero plausible, añade un matiz ("según estimaciones de mercado").
5. SEO: Asegúrate de que los H2 y H3 contienen keywords relevantes en español. No uses más de un H1.
6. LONGITUD: El artículo EDITADO debe tener al menos 1200 palabras. Si eliminas contenido, DEBES añadir contenido equivalente para compensar.

FORMATO DE RESPUESTA (CRÍTICO):
- Devuelve ÚNICAMENTE el texto del artículo editado en Markdown puro.
- NO incluyas bloques de código (```markdown), NO incluyas comentarios meta, NO expliques los cambios.
- NO modifiques el frontmatter YAML (---.....---). Solo el contenido DESPUÉS del segundo ---.
- El primer carácter de tu respuesta debe ser el inicio del artículo (normalmente ![imagen]...).
"""

# =====================================================
# TAREA B2: NOTEBOOKLM FACT-CHECK ES
# =====================================================

def _notebooklm_factcheck_es(body_text):
    """
    Usa NotebookLM MCP para verificar el contenido del borrador en español.
    Returns: string con alertas, o "" si no disponible.
    """
    try:
        from researcher import NotebookMCPClient
    except ImportError:
        print("   ⚠️ [Editor ES] No se pudo importar NotebookMCPClient")
        return ""

    auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
    if not os.path.exists(auth_path):
        print("   ⚠️ [Editor ES] NotebookLM auth no disponible. Saltando fact-check.")
        return ""

    mcp_client = NotebookMCPClient()
    alerts = ""

    try:
        if not mcp_client.connect():
            print("   ⚠️ [Editor ES] No se pudo conectar a NotebookLM MCP.")
            return ""

        # Crear notebook temporal
        nb_result = mcp_client.call_tool("notebook_create", {
            "title": f"QA Editor ES — {datetime.now().strftime('%Y%m%d_%H%M')}"
        })
        if not nb_result or not isinstance(nb_result, dict):
            return ""

        notebook_id = nb_result.get("notebook_id", "")
        if not notebook_id:
            return ""

        print(f"   📓 [NotebookLM ES] Notebook temporal creado: {notebook_id[:12]}...")

        # Añadir borrador como fuente
        mcp_client.call_tool("notebook_add_text", {
            "notebook_id": notebook_id,
            "title": "Borrador del artículo",
            "content": body_text[:50000]  # Límite seguro
        })
        time.sleep(2)

        # Query 1: Afirmaciones sospechosas
        q1 = mcp_client.call_tool("notebook_query", {
            "notebook_id": notebook_id,
            "query": "¿Qué afirmaciones de este texto son potencialmente incorrectas, exageradas o no están respaldadas por fuentes verificables? Lista las 3 más sospechosas."
        })
        if q1 and isinstance(q1, dict):
            alert_text = q1.get("answer", "") or q1.get("text", "")
            if alert_text:
                alerts += f"ALERTAS DE VERIFICACIÓN (afirmaciones sospechosas):\n{alert_text}\n\n"

        # Query 2: Datos numéricos inventados
        q2 = mcp_client.call_tool("notebook_query", {
            "notebook_id": notebook_id,
            "query": "¿Hay datos numéricos (porcentajes, cifras en dólares, estadísticas) en este texto que parezcan inventados, inconsistentes o imposibles de verificar? Lista los más sospechosos."
        })
        if q2 and isinstance(q2, dict):
            alert_text = q2.get("answer", "") or q2.get("text", "")
            if alert_text:
                alerts += f"ALERTAS DE DATOS NUMÉRICOS:\n{alert_text}\n\n"

        # Cleanup
        try:
            mcp_client.call_tool("notebook_delete", {
                "notebook_id": notebook_id,
                "confirm": True
            })
            print(f"   🗑️ [NotebookLM ES] Notebook temporal eliminado")
        except Exception:
            pass

        if alerts:
            print(f"   🔍 [NotebookLM ES] Fact-check completado: {len(alerts)} chars de alertas")
        else:
            print(f"   ✅ [NotebookLM ES] Sin alertas significativas")

    except Exception as e:
        print(f"   ⚠️ [NotebookLM ES] Error en fact-check: {e}")
    finally:
        try:
            mcp_client.close()
        except Exception:
            pass

    return alerts


# =====================================================
# TAREA B3: PIPELINE DE CORRECCIÓN ES
# =====================================================

def _call_llm_es(prompt, system_prompt):
    """
    Cascada LLM para el Editor ES: Zhipu GLM → Gemini Flash.
    Returns: string con el artículo corregido, o None si falla.
    """
    # Intento 1: OpenRouter (DeepSeek V3)
    # Using OPEN_CORRECTOR_API_KEY (assigned to OpenRouter)
    if OPEN_CORRECTOR_KEY:
        max_retries = 3
        backoff_seconds = [10, 25, 60]
        for attempt in range(max_retries):
            try:
                print(f"   🧠 [Editor ES] Intentando DeepSeek V3 vía OpenRouter (intento {attempt+1})...")
                or_client = OpenAI(
                    api_key=OPEN_CORRECTOR_KEY,
                    base_url="https://openrouter.ai/api/v1"
                )
                response = or_client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=16000
                )
                result = response.choices[0].message.content.strip()
                if result and len(result) > 500:
                    print(f"   ✅ [Editor ES] DeepSeek V3 respondió: {len(result)} chars")
                    return result
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    import time as _time
                    wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 60
                    print(f"   ⏳ [Editor ES] DeepSeek V3 rate limit. Esperando {wait}s...")
                    _time.sleep(wait)
                else:
                    print(f"   ⚠️ [Editor ES] DeepSeek V3 falló: {e}")
                    break

    # Intento 2: HF Serverless (Qwen3-32B)
    # Using CORRECTOR_HF_API_KEY
    if CORRECTOR_HF_KEY:
        max_retries = 2
        backoff_seconds = [10, 25]
        for attempt in range(max_retries):
            try:
                print(f"   🧠 [Editor ES] Intentando Qwen3-32B vía HF Serverless (intento {attempt+1})...")
                hf_resp = requests.post(
                    "https://router.huggingface.co/models/Qwen/Qwen3-32B/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {CORRECTOR_HF_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "Qwen/Qwen3-32B",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.4,
                        "max_tokens": 16000,
                        "stream": False
                    },
                    timeout=120
                )
                if hf_resp.status_code == 200:
                    result = hf_resp.json()["choices"][0]["message"]["content"].strip()
                    if result and len(result) > 500:
                        print(f"   ✅ [Editor ES] Qwen3-32B respondió: {len(result)} chars")
                        return result
                elif hf_resp.status_code == 429:
                    import time as _time
                    wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 25
                    print(f"   ⏳ [Editor ES] Qwen3-32B rate limit. Esperando {wait}s...")
                    _time.sleep(wait)
                else:
                    print(f"   ⚠️ [Editor ES] Qwen3-32B HTTP {hf_resp.status_code}")
                    break
            except Exception as e:
                print(f"   ⚠️ [Editor ES] Qwen3-32B falló: {e}")
                break

    # Intento 3: Groq (Llama 3.3 70B)
    if GROQ_API_KEY:
        max_retries = 2
        backoff_seconds = [5, 15]
        for attempt in range(max_retries):
            try:
                print(f"   🚀 [Editor ES] Intentando Groq (Llama 3.3 70B) (intento {attempt+1})...")
                groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=8000
                )
                result = response.choices[0].message.content.strip()
                if result and len(result) > 500:
                    print(f"   ✅ [Editor ES] Groq respondió: {len(result)} chars")
                    return result
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    import time as _time
                    wait = backoff_seconds[attempt] if attempt < len(backoff_seconds) else 20
                    print(f"   ⏳ [Editor ES] Groq rate limit. Esperando {wait}s...")
                    _time.sleep(wait)
                else:
                    print(f"   ⚠️ [Editor ES] Groq falló: {e}")
                    break

    # Intento 4: Gemini 2.0 Flash
    if GEMINI_KEY:
        try:
            print("   🚨 [Editor ES] Fallback a Gemini 2.0 Flash (Emergencia)...")
            gemini_client = genai.Client(api_key=GEMINI_KEY)
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\n\n{prompt}",
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=16000
                )
            )
            result = response.text.strip()
            if result and len(result) > 500:
                print(f"   ✅ [Editor ES] Gemini respondió: {len(result)} chars")
                return result
        except Exception as e:
            print(f"   ⚠️ [Editor ES] Gemini falló: {e}")

    print("   ❌ [Editor ES] Todos los LLMs fallaron.")
    return None


def _validate_output(edited_text, original_text):
    """
    Validación post-edición: word count, frases vetadas residuales.
    Returns: (is_valid, issues_list)
    """
    issues = []

    # Word count check
    original_words = len(original_text.split())
    edited_words = len(edited_text.split())
    if edited_words < 1200:
        issues.append(f"Word count demasiado bajo: {edited_words} (mínimo 1200)")
    if edited_words < original_words * 0.8:
        issues.append(f"Se perdió >20% del contenido: {original_words} → {edited_words}")

    # Frases vetadas check
    banned = [
        "en el vertiginoso mundo",
        "un arma de doble filo",
        "navegar por el panorama",
        "es importante destacar",
        "promete revolucionar",
        "crecimiento explosivo",
        "inmersión profunda",
        "solo el tiempo lo dirá",
        "aquí está el texto reescrito",
    ]
    lower_text = edited_text.lower()
    for phrase in banned:
        if phrase in lower_text:
            issues.append(f"Frase vetada encontrada: '{phrase}'")

    # Link presence check (EXTERNAL and INTERNAL)
    import re
    has_external_link = bool(re.search(r'\]\(https?://[^\)]+\)', edited_text))
    has_internal_link = bool(re.search(r'\]\((?!https?://)[^\)]+\)', edited_text))
    
    if not has_external_link:
        issues.append("ERROR CRÍTICO: Falta enlace externo (Outbound Link).")
    if not has_internal_link:
        issues.append("ERROR CRÍTICO: Falta enlace interno (Internal Link).")

    is_valid = len(issues) == 0
    return is_valid, issues


def run(category, content_dir="content/es"):
    """
    Pipeline principal del Editor Jefe ES.

    1. Encuentra el borrador .md más reciente en content/es/{category}/
    2. Ejecuta link validation
    3. Ejecuta NotebookLM fact-check
    4. Llama al LLM con el contexto completo
    5. Valida y sobreescribe el .md

    Returns: dict con resultado o None si falla
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dir = os.path.join(base_dir, content_dir, category)

    if not os.path.isdir(search_dir):
        print(f"   ❌ [Editor ES] Directorio no encontrado: {search_dir}")
        return None

    # A2: Encontrar el borrador más reciente
    md_files = glob.glob(os.path.join(search_dir, "*.md"))
    if not md_files:
        print(f"   ❌ [Editor ES] No hay archivos .md en {search_dir}")
        return None

    # Ordenar por fecha de modificación (más reciente primero)
    md_files.sort(key=os.path.getmtime, reverse=True)
    draft_path = md_files[0]
    print(f"\n   📝 [Editor ES] Borrador seleccionado: {os.path.basename(draft_path)}")

    # Leer borrador
    with open(draft_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Separar frontmatter del body
    parts = raw_content.split('---', 2)
    if len(parts) < 3:
        print(f"   ❌ [Editor ES] Frontmatter YAML inválido en {draft_path}")
        return None

    frontmatter = f"---{parts[1]}---"
    body = parts[2].strip()

    if len(body) < 200:
        print(f"   ⚠️ [Editor ES] Body demasiado corto ({len(body)} chars). Saltando.")
        return None

    # PASO 1: Link Validation
    print(f"\n   🔗 [Editor ES] PASO 1: Verificación de enlaces...")
    link_result = validate_links(body)
    dead_links_block = ""
    if link_result["dead"] or link_result["timeout"]:
        dead_urls = [l["url"] for l in link_result["dead"]] + [l["url"] for l in link_result["timeout"]]
        dead_links_block = (
            "\n\nENLACES MUERTOS DETECTADOS (debes eliminar estos enlaces del texto, "
            "convirtiendo [texto](url) en **texto** sin enlace):\n"
            + "\n".join([f"  - {u}" for u in dead_urls])
        )
        print(f"   ⚠️ {len(dead_urls)} enlaces muertos/timeout detectados")
    else:
        print(f"   ✅ Todos los enlaces vivos")

    # PASO 2: NotebookLM Fact-Check
    print(f"\n   🔍 [Editor ES] PASO 2: Fact-check con NotebookLM...")
    factcheck_alerts = _notebooklm_factcheck_es(body)
    factcheck_block = ""
    if factcheck_alerts:
        factcheck_block = f"\n\n{factcheck_alerts}"

    # PASO 3: Construir prompt para el LLM
    print(f"\n   🧠 [Editor ES] PASO 3: Enviando a LLM para corrección...")
    user_prompt = (
        f"BORRADOR A EDITAR:\n\n{body}"
        f"{dead_links_block}"
        f"{factcheck_block}"
        f"\n\nDevuelve ÚNICAMENTE el artículo editado en Markdown puro. "
        f"Sin bloques de código, sin comentarios meta."
    )

    edited_body = _call_llm_es(user_prompt, SYSTEM_PROMPT_EDITOR_ES)

    if not edited_body:
        print(f"   ⚠️ [Editor ES] LLM no respondió. Borrador original preservado.")
        return {"status": "skipped", "reason": "LLM failure", "filepath": draft_path}

    # Limpiar posible wrapping de markdown del LLM
    edited_body = edited_body.strip()
    if edited_body.startswith("```markdown"):
        edited_body = edited_body[len("```markdown"):].strip()
    if edited_body.startswith("```"):
        edited_body = edited_body[3:].strip()
    if edited_body.endswith("```"):
        edited_body = edited_body[:-3].strip()

    # PASO 4: Validación
    print(f"\n   ✅ [Editor ES] PASO 4: Validación post-edición...")
    is_valid, issues = _validate_output(edited_body, body)

    # Si el word count es bajo, REINTENTO pidiendo al LLM que amplíe
    if not is_valid and any("Word count" in i or "Se perdió" in i for i in issues):
        current_words = len(edited_body.split())
        print(f"   🔄 [Editor ES] Word count bajo ({current_words}). Reintentando con prompt de expansión...")
        expand_prompt = (
            f"El siguiente artículo tiene solo {current_words} palabras y necesita al menos 1400. "
            f"AMPLÍA el contenido: añade más análisis, datos contextuales, perspectivas de expertos "
            f"y profundiza en los puntos existentes. NO elimines nada del texto actual, solo AÑADE.\n\n"
            f"ARTÍCULO A AMPLIAR:\n\n{edited_body}\n\n"
            f"Devuelve ÚNICAMENTE el artículo ampliado en Markdown puro. Sin bloques de código, sin comentarios."
        )
        expanded_body = _call_llm_es(expand_prompt, SYSTEM_PROMPT_EDITOR_ES)
        if expanded_body and len(expanded_body.split()) > current_words:
            # Limpiar wrapping
            expanded_body = expanded_body.strip()
            if expanded_body.startswith("```markdown"):
                expanded_body = expanded_body[len("```markdown"):].strip()
            if expanded_body.startswith("```"):
                expanded_body = expanded_body[3:].strip()
            if expanded_body.endswith("```"):
                expanded_body = expanded_body[:-3].strip()
            edited_body = expanded_body
            is_valid, issues = _validate_output(edited_body, body)
            print(f"   📊 [Editor ES] Tras expansión: {len(edited_body.split())} palabras")
        else:
            print(f"   ⚠️ [Editor ES] Expansión falló. Usando versión disponible.")

    if not is_valid:
        print(f"   ⚠️ [Editor ES] Validación con warnings (se publica igualmente):")
        for issue in issues:
            print(f"      - {issue}")

    # A3: Guardar versión editada (preservar frontmatter)
    final_content = f"{frontmatter}\n\n{edited_body}\n"
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    original_words = len(body.split())
    edited_words = len(edited_body.split())
    dead_fixed = len(link_result.get("dead", []))

    print(f"\n   🎉 [Editor ES] ¡Artículo editado y guardado!")
    print(f"      📊 Palabras: {original_words} → {edited_words} ({edited_words - original_words:+d})")
    print(f"      🔗 Enlaces muertos reparados: {dead_fixed}")
    print(f"      📄 Archivo: {draft_path}")

    return {
        "status": "success",
        "filepath": draft_path,
        "original_words": original_words,
        "edited_words": edited_words,
        "dead_links_fixed": dead_fixed,
        "factcheck_ran": bool(factcheck_alerts),
        "issues": issues if issues else []
    }


# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Editor Jefe QA - Español")
    parser.add_argument("--category", type=str, required=True)
    args = parser.parse_args()
    result = run(args.category)
    if result:
        print(f"\n{'='*60}")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
