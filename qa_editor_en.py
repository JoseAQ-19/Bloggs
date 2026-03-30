"""
qa_editor_en.py — Editor Jefe QA para artículos en Inglés (US Market).

Cerebro nativo American English: lee un borrador .md generado por el Writer,
lo corrige (estilo TechCrunch, SEO US, frases vetadas, enlaces muertos,
fact-check via NotebookLM) y devuelve la versión final.

Uso:
    from qa_editor_en import run as run_editor_en
    result = run_editor_en(category="ia")
"""

import os
import re
import json
import glob
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === IMPORTS PROPIOS ===
from qa_link_validator import validate_links
from utils import ContentCleaner
from llm_router import LLMRouter

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
# TAREA C0: NICHE CONSTRAINTS (HYPER-NICHEABLE)
# =====================================================

NICHE_CONSTRAINTS_EN = {
    "fitness": "FITNESS MISSION: Demand medical and scientific rigor. Cite PubMed, WHO, or peer-reviewed journals. Purge 'bro-science'. Mandatory jargon: progressive overload, metabolic stress, hypertrophy, caloric deficit.",
    "crypto": "CRYPTO MISSION: Financial rigor and security. Always include a disclaimer (Not Financial Advice). Technical terms: on-chain data, decentralization, proof-of-stake, market cap, volatility.",
    "ia": "AI MISSION: Focus on technical architecture and ethics. Discuss foundation models, inference latency, RAG (Retrieval-Augmented Generation), and safety alignment.",
    "youtube": "MEDIA MISSION: Retention metrics and viewer psychology analysis. Discuss CTR, 3-second hooks, and the YouTube recommendation algorithm.",
    "viral": "VIRAL MISSION: Deep analysis of virality triggers (fear, ego, scarcity). Identify the psychological mechanics of the trend.",
    "tools": "PRODUCTIVITY MISSION: Cost-benefit and UX analysis. Evaluate the learning curve and enterprise-level integration (APIs, Webhooks).",
    "funds": "ECONOMY MISSION: Focus on investment funds and macro trends. Reference market data (S&P 500, Yield curves) and explain risk management strategies."
}

# =====================================================
# TAREA C1: SYSTEM PROMPT DEL EDITOR JEFE EN
# =====================================================

def get_system_prompt_en(category):
    niche_instruction = NICHE_CONSTRAINTS_EN.get(category.lower(), "GENERAL MISSION: Maintain a high standard of informative quality and journalistic rigor.")
    
    return f"""ROLE: You are the EDITOR-IN-CHIEF and CONTENT AUDITOR of NovumWorld, a premium US tech publication. Your mission is to receive a DRAFT article written by a junior writer and return it PERFECT for immediate publication.

YOUR PROFILE:
- Veteran tech journalist with 20 years at TechCrunch, The Verge, and Ars Technica.
- Cynical, demanding, allergic to corporate fluff and ChatGPT-flavored prose.
- Expert in US-market on-page SEO (.com) and Google AdSense compliance.

{niche_instruction}

NEW STRICT CONTENT AUDITOR RULES (MANDATORY):
1. Strict Contrast between Headline Promise and Body: This is the main barrier. You must read the title and look for immediate justification of that premise in the opening paragraphs. If the central theme of the title is not analytically developed or is barely mentioned in the body, REJECT the text immediately.
2. AI Automated Content Audit: Do not just check spelling. Audit the logical coherence of "The Machine". If the AI produces generic Wikipedia-like text instead of a deep financial/tech analysis linked to the title, INTERVÉN and demand a rewrite.
3. Systematic Fluff Removal (SEO): Prune the "fluff". Require 100% of the content to provide real analytical value to the human reader. Do not waste time with basic questions.
4. Cross-referenced Fact Checking: You are obligated to detect numerical claims (yields, dates, fees) and contrast them. If you detect hallucinations or outdated data, block publication.

YOUR MISSION (in this priority order):
1. GEO (GENERATE ENGINE OPTIMIZATION) - MANDATORY CHUNKING:
   Under EVERY heading (H2, H3), the FIRST sentence MUST be a direct, citable, and synthesized answer to the heading's premise. FORBIDDEN to start with filler like "In this section...", "Moving on...", or "It is critical to understand...". Get to the point from word 1.

2. METADATA PRESERVATION:
   If the draft contains <script type="application/ld+json"> blocks or "Related Articles" sections, you MUST KEEP THEM INTACT at the end of the document. Do not summarize, do not translate, do not remove.

3. PURE ENGLISH: If you find ANY sentence, heading, or paragraph in Spanish, TRANSLATE it to American English.

4. DEAD LINKS: I will provide a list of links that returned HTTP 404/timeout. You MUST:
   - Remove the broken markdown link: convert [text](dead_url) to **text** (bold, no link).
   - NEVER fabricate a new URL.

5. TECH JARGON & EEAT:
   Remove vague conclusions and existential reflections ("Only time will tell"). Replace generic vocabulary with industry jargon ("CPM", "CTR", "Retention metrics", "LTV", "Conversion Rate").

6. BANNED PHRASES: Find and REPLACE: "In the ever-evolving landscape of", "In summary", "A double-edged sword", "is revolutionizing", "driving innovation".

7. EXTERNAL LINKS (AUTHORITY): 
   The article MUST contain at least 2-3 outbound links to high-authority sources (e.g., PubMed, TechCrunch, Nature, government agencies, or leading industry publications). If the draft mentions a study, a law, or a news event without a link, you MUST find the real URL (or a reliable source citing it) and insert it. If the exact URL is missing, link to the official portal of the organization mentioned.

8. SEO: Ensure H2/H3 headings contain relevant English keywords. No more than one H1.

RESPONSE FORMAT (CRITICAL):
- Return ONLY the edited article text in pure Markdown.
- Do NOT include code blocks (```markdown), do NOT include meta-comments.
- Do NOT include raw JSON { ... } in the body of the article.
- Do NOT modify the YAML frontmatter. Only edit the content AFTER the second ---.
"""

# =====================================================
# TAREA C2: NOTEBOOKLM FACT-CHECK EN
# =====================================================

def _notebooklm_factcheck_en(body_text):
    """
    Uses NotebookLM MCP to fact-check the draft content in English.
    Returns: string with alerts, or "" if unavailable.
    """
    try:
        from researcher import NotebookMCPClient
    except ImportError:
        print("   ⚠️ [Editor EN] Could not import NotebookMCPClient")
        return ""

    auth_path = os.path.expanduser("~/.notebooklm-mcp/auth.json")
    if not os.path.exists(auth_path):
        print("   ⚠️ [Editor EN] NotebookLM auth not available. Skipping fact-check.")
        return ""

    mcp_client = NotebookMCPClient()
    alerts = ""

    try:
        if not mcp_client.connect():
            print("   ⚠️ [Editor EN] Could not connect to NotebookLM MCP.")
            return ""

        # Create temporary notebook
        nb_result = mcp_client.call_tool("notebook_create", {
            "title": f"QA Editor EN — {datetime.now().strftime('%Y%m%d_%H%M')}"
        })
        if not nb_result or not isinstance(nb_result, dict):
            return ""

        notebook_id = nb_result.get("notebook_id", "")
        if not notebook_id:
            return ""

        print(f"   📓 [NotebookLM EN] Temporary notebook created: {notebook_id[:12]}...")

        # Add draft as source
        mcp_client.call_tool("notebook_add_text", {
            "notebook_id": notebook_id,
            "title": "Article Draft",
            "content": body_text[:50000]
        })
        time.sleep(2)

        # Query 1: Suspicious claims
        q1 = mcp_client.call_tool("notebook_query", {
            "notebook_id": notebook_id,
            "query": "Which claims in this text are potentially incorrect, exaggerated, or not supported by verifiable sources? List the 3 most suspicious."
        })
        if q1 and isinstance(q1, dict):
            alert_text = q1.get("answer", "") or q1.get("text", "")
            if alert_text:
                alerts += f"VERIFICATION ALERTS (suspicious claims):\n{alert_text}\n\n"

        # Query 2: Fabricated numbers
        q2 = mcp_client.call_tool("notebook_query", {
            "notebook_id": notebook_id,
            "query": "Are there any numerical data points (percentages, dollar figures, statistics) in this text that appear fabricated, inconsistent, or impossible to verify? List the most suspicious."
        })
        if q2 and isinstance(q2, dict):
            alert_text = q2.get("answer", "") or q2.get("text", "")
            if alert_text:
                alerts += f"NUMERICAL DATA ALERTS:\n{alert_text}\n\n"

        # Cleanup
        try:
            mcp_client.call_tool("notebook_delete", {
                "notebook_id": notebook_id,
                "confirm": True
            })
            print(f"   🗑️ [NotebookLM EN] Temporary notebook deleted")
        except Exception:
            pass

        if alerts:
            print(f"   🔍 [NotebookLM EN] Fact-check complete: {len(alerts)} chars of alerts")
        else:
            print(f"   ✅ [NotebookLM EN] No significant alerts")

    except Exception as e:
        print(f"   ⚠️ [NotebookLM EN] Fact-check error: {e}")
    finally:
        try:
            mcp_client.close()
        except Exception:
            pass

    return alerts


# =====================================================
# TAREA C3: PIPELINE DE CORRECCIÓN EN
# =====================================================

def _call_llm_en_v3_core(prompt, system_prompt):
    """
    Original LLM cascade for Editor EN (Tier 1-4).
    """
    # Attempt 1: OpenRouter (DeepSeek V3)
    if OPEN_CORRECTOR_KEY:
        max_retries = 3
        backoff_seconds = [10, 25, 60]
        for attempt in range(max_retries):
            try:
                print(f"   🧠 [Editor EN] TIER 1: DeepSeek V3 via OpenRouter...")
                or_client = OpenAI(api_key=OPEN_CORRECTOR_KEY, base_url="https://openrouter.ai/api/v1")
                response = or_client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=16000
                )
                result = response.choices[0].message.content.strip()
                if result and len(result) > 500: return result
            except Exception as e:
                logging.warning(f"[Editor EN] TIER 1 DeepSeek V3 attempt {attempt+1} failed: {type(e).__name__}: {str(e)[:150]}")

    # Attempt 2: HF Serverless
    if CORRECTOR_HF_KEY:
        try:
            print(f"   🧠 [Editor EN] TIER 2: Qwen3-32B via HF Serverless...")
            hf_resp = requests.post(
                "https://router.huggingface.co/models/Qwen/Qwen3-32B/v1/chat/completions",
                headers={"Authorization": f"Bearer {CORRECTOR_HF_KEY}", "Content-Type": "application/json"},
                json={"model": "Qwen/Qwen3-32B", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 16000},
                timeout=120
            )
            if hf_resp.status_code == 200:
                result = hf_resp.json()["choices"][0]["message"]["content"].strip()
                if result and len(result) > 500: return result
        except Exception as e:
            logging.warning(f"[Editor EN] TIER 2 HF Qwen3-32B failed: {type(e).__name__}: {str(e)[:150]}")

    # Attempt 3: Groq
    if GROQ_API_KEY:
        try:
            print(f"   🚀 [Editor EN] TIER 3: Groq (Llama 3.3 70B)...")
            groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            response = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], temperature=0.4, max_tokens=8000)
            result = response.choices[0].message.content.strip()
            if result and len(result) > 500: return result
        except Exception as e:
            logging.warning(f"[Editor EN] TIER 3 Groq Llama-3.3-70B failed: {type(e).__name__}: {str(e)[:150]}")

    # Attempt 4: Gemini
    if GEMINI_KEY:
        try:
            print("   🚨 [Editor EN] TIER 4: Fallback to Gemini 2.0 Flash...")
            gemini_client = genai.Client(api_key=GEMINI_KEY)
            response = gemini_client.models.generate_content(model="gemini-2.0-flash", contents=f"{system_prompt}\n\n{prompt}")
            return response.text.strip()
        except Exception as e:
            logging.warning(f"[Editor EN] TIER 4 Gemini Flash failed: {type(e).__name__}: {str(e)[:150]}")
    return None


def _call_llm_en(prompt, system_prompt):
    """
    EN Router with Capa Cero.
    """
    return LLMRouter.route_call(
        prompt, 
        system_prompt, 
        _call_llm_en_v3_core, 
        model_type="reasoning"
    )


def _validate_output(edited_text, original_text):
    """
    Post-edit validation: word count, residual banned phrases.
    Returns: (is_valid, issues_list)
    """
    issues = []

    # Word count check
    original_words = len(original_text.split())
    edited_words = len(edited_text.split())
    if edited_words < 1200:
        issues.append(f"Word count too low: {edited_words} (minimum 1200)")
    if edited_words < original_words * 0.8:
        issues.append(f"Lost >20% content: {original_words} → {edited_words}")

    # Banned phrases check
    banned = [
        "in the ever-evolving landscape",
        "a double-edged sword",
        "navigating the complexities",
        "it's important to note",
        "it remains to be seen",
        "poised for explosive growth",
        "deep dive",
        "in today's digital landscape",
        "here is the rewritten text",
        "driving innovation",
        # AI artifact tokens (CRITICAL — AdSense blockers)
        "gemini grounding e-e-a-t",
        "gemini grounding",
        "according to **gemini",
        "as detailed by **gemini",
        "as reported by **gemini",
        "[source needed]",
        "[citation needed]",
        "insert source here",
        # Machine persona (signals AI authorship)
        "the machine's verdict",
        "the machine sees",
        "the machine believes",
    ]
    lower_text = edited_text.lower()
    for phrase in banned:
        if phrase in lower_text:
            issues.append(f"Banned phrase found: '{phrase}'")

    # Link presence check (EXTERNAL and INTERNAL)
    import re
    has_external_link = bool(re.search(r'\]\(https?://[^\)]+\)', edited_text))
    has_internal_link = bool(re.search(r'\]\((?!https?://)[^\)]+\)', edited_text))
    
    if not has_external_link:
        issues.append("CRITICAL ERROR: Missing Outbound Link.")
    if not has_internal_link:
        issues.append("CRITICAL ERROR: Missing Internal Link.")

    is_valid = len(issues) == 0
    return is_valid, issues

def _upgrade_low_authority_links(body_text, lang="en"):
    """
    Scans draft links, evaluates E-E-A-T authority, and if score < 70,
    uses Gemini Grounding + Google Search to find a high-authority replacement.
    """
    try:
        from expert_validator import extract_all_markdown_links, validate_citation_authority
    except ImportError:
        return body_text, []

    GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not GEMINI_KEY: return body_text, []
    
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=GEMINI_KEY)
    except Exception:
        return body_text, []

    links = extract_all_markdown_links(body_text)
    upgraded_count = 0
    replacement_log = []
    replaced_urls = set()

    for l in links:
        url = l['url']
        if url in replaced_urls: continue
        if any(x in url for x in ['localhost', 'novum', 'example.com', '.local']): continue
            
        val = validate_citation_authority(url)
        if val["authority_score"] < 70:
            print(f"      📉 [E-E-A-T] Low authority detected: {url} (Score: {val['authority_score']})")
            
            start_idx = max(0, l['start'] - 250)
            end_idx = min(len(body_text), l['end'] + 250)
            context = body_text[start_idx:end_idx]
            
            prompt = f"""You are a fact-checker enforcing Google's E-E-A-T guidelines. 
A writer used a low-authority source ({url}) for the following markdown claim context:
CONTEXT: "{context}"

Use Google Search to find a HIGH-AUTHORITY alternative public source (.gov, .edu, Reuters, Bloomberg, Official blogs, etc.) that validates the exact same claim or data point.
Return ONLY a valid JSON object:
{{"found": true, "better_url": "https://...", "reason": "Why it's better"}}
If you cannot find a better high-authority source, return {{"found": false}}. Do not hallucinate URLs!
"""
            try:
                google_search_tool = types.Tool(google_search=types.GoogleSearch())
                resp = gemini_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[google_search_tool],
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                if resp.text:
                    data = json.loads(resp.text)
                    if data.get("found") and data.get("better_url") and data.get("better_url").startswith("http"):
                        from urllib.parse import urlparse
                        new_url = data["better_url"]
                        print(f"         🔄 Upgraded {val['domain']} -> {urlparse(new_url).netloc.replace('www.','')}")
                        body_text = body_text.replace(url, new_url)
                        replaced_urls.add(url)
                        upgraded_count += 1
                        replacement_log.append(f"Replaced {url} -> {new_url}")
            except Exception as e:
                pass
                
    return body_text, replacement_log


def run(category, content_dir="content/en"):
    """
    Main pipeline for the EN Editor-in-Chief.

    1. Find the most recent .md draft in content/en/{category}/
    2. Run link validation
    3. Run NotebookLM fact-check
    4. Call LLM with full context
    5. Validate and overwrite the .md

    Returns: dict with result or None on failure
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dir = os.path.join(base_dir, content_dir, category)

    if not os.path.isdir(search_dir):
        print(f"   ❌ [Editor EN] Directory not found: {search_dir}")
        return None

    # A2: Find the most recent draft
    md_files = glob.glob(os.path.join(search_dir, "*.md"))
    if not md_files:
        print(f"   ❌ [Editor EN] No .md files in {search_dir}")
        return None

    md_files.sort(key=os.path.getmtime, reverse=True)
    draft_path = md_files[0]
    print(f"\n   📝 [Editor EN] Draft selected: {os.path.basename(draft_path)}")

    # Read draft
    with open(draft_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Separate frontmatter from body
    parts = raw_content.split('---', 2)
    if len(parts) < 3:
        print(f"   ❌ [Editor EN] Invalid YAML frontmatter in {draft_path}")
        return None

    frontmatter = f"---{parts[1]}---"
    body = parts[2].strip()

    if len(body) < 200:
        print(f"   ⚠️ [Editor EN] Body too short ({len(body)} chars). Skipping.")
        return None

    # Extraer el título del frontmatter
    title_match = re.search(r'^title:\s*"?([^"\n]+)"?', frontmatter, re.MULTILINE)
    article_title = title_match.group(1) if title_match else "No title"

    # STEP 1: Link Validation
    print(f"\n   🔗 [Editor EN] STEP 1: Dead link verification...")
    link_result = validate_links(body)
    dead_links_block = ""
    if link_result["dead"] or link_result["timeout"]:
        dead_urls = [l["url"] for l in link_result["dead"]] + [l["url"] for l in link_result["timeout"]]
        dead_links_block = (
            "\n\nDEAD LINKS DETECTED (you must remove these links from the text, "
            "converting [text](url) to **text** without a link):\n"
            + "\n".join([f"  - {u}" for u in dead_urls])
        )
        print(f"   ⚠️ {len(dead_urls)} dead/timeout links detected")
    else:
        print(f"   ✅ All links alive")

    # STEP 1.5: E-E-A-T Authority Upgrade
    print(f"\n   🏛️ [Editor EN] STEP 1.5: E-E-A-T Authority Score Audit...")
    body, upgrade_log = _upgrade_low_authority_links(body, lang="en")
    eeat_upgrade_block = ""
    if upgrade_log:
        eeat_upgrade_block = "\n\nE-E-A-T AUTHORITY UPGRADES:\n" + "\n".join([f"  - {u}" for u in upgrade_log])

    # STEP 2: NotebookLM Fact-Check
    print(f"\n   🔍 [Editor EN] STEP 2: Fact-check with NotebookLM...")
    factcheck_alerts = _notebooklm_factcheck_en(body)
    factcheck_block = ""
    if factcheck_alerts:
        factcheck_block = f"\n\n{factcheck_alerts}"

    # STEP 2.5: Global Content Audit
    print(f"\n   ⚖️ [Editor EN] STEP 2.5: Global Content Audit (Content Auditor)...")
    audit_prompt = f"""
Execute your role as CONTENT AUDITOR. Read the title and the draft body.
You must score from 1 to 10 the following 4 criteria based on YOUR 4 STRICT RULES:
1. SEO
2. E-E-A-T
3. GEO
4. Real Value

ARTICLE TITLE: {article_title}

DRAFT BODY:
{body[:15000]}

Return ONLY a valid JSON object with this exact format (no markdown blocks, starts with {{ and ends with }}):
{{
  "seo_score": 8,
  "eeat_score": 7,
  "geo_score": 9,
  "value_score": 8,
  "feedback": "What the writer (Ralph) must change to reach a 10 in all points."
}}
"""
    audit_raw = _call_llm_en(audit_prompt, get_system_prompt_en(category))
    if audit_raw:
        try:
            # Clean JSON formatting issues
            clean_json = audit_raw.strip()
            if clean_json.startswith("```json"): clean_json = clean_json[7:-3].strip()
            if clean_json.startswith("```"): clean_json = clean_json[3:-3].strip()
            start_idx = clean_json.find('{')
            end_idx = clean_json.rfind('}')
            if start_idx != -1 and end_idx != -1:
                clean_json = clean_json[start_idx:end_idx+1]
            
            audit_json = json.loads(clean_json)
            seo_s = float(audit_json.get("seo_score", 5))
            eeat_s = float(audit_json.get("eeat_score", 5))
            geo_s = float(audit_json.get("geo_score", 5))
            val_s = float(audit_json.get("value_score", 5))
            avg_score = (seo_s + eeat_s + geo_s + val_s) / 4.0
            
            feedback = audit_json.get('feedback', '')
            print(f"      📊 Scores -> SEO: {seo_s}, EEAT: {eeat_s}, GEO: {geo_s}, Real Value: {val_s}")
            print(f"      📈 Quality Average: {avg_score:.2f}/10")
            print(f"      💬 Feedback: {feedback}")
            
            if avg_score < 8.0:
                print(f"\n   ❌ [Editor EN] AUDIT FAILED (Average < 8). The article lacks coherence with the headline, lacks real value or E-E-A-T. Rejecting for a rewrite.")
                return {
                    "status": "rejected",
                    "reason": "Audit failed (Average < 8)",
                    "score": avg_score,
                    "feedback": feedback,
                    "filepath": draft_path
                }
        except Exception as e:
            print(f"   ⚠️ [Editor EN] Failed to parse JSON audit. Continuing assuming risk. Error: {e}")

    # STEP 3: Build LLM prompt
    print(f"\n   🧠 [Editor EN] STEP 3: Sending to LLM for editing...")
    user_prompt = (
        f"DRAFT TO EDIT:\n\n{body}"
        f"{dead_links_block}"
        f"{factcheck_block}"
        f"{eeat_upgrade_block}"
        f"\n\nReturn ONLY the edited article in pure Markdown. "
        f"No code blocks, no meta-comments."
    )

    edited_body = _call_llm_en(user_prompt, get_system_prompt_en(category))

    if not edited_body:
        print(f"   ⚠️ [Editor EN] LLM did not respond. Original draft preserved.")
        return {"status": "skipped", "reason": "LLM failure", "filepath": draft_path}

    # Clean possible markdown wrapping
    edited_body = edited_body.strip()
    if edited_body.startswith("```markdown"):
        edited_body = edited_body[len("```markdown"):].strip()
    if edited_body.startswith("```"):
        edited_body = edited_body[3:].strip()
    if edited_body.endswith("```"):
        edited_body = edited_body[:-3].strip()

    # STEP 4: Validation
    print(f"\n   ✅ [Editor EN] STEP 4: Post-edit validation...")
    is_valid, issues = _validate_output(edited_body, body)

    # If the word count is low, RETRY by asking the LLM to expand the text
    if not is_valid and any("Word count" in i or "Lost" in i for i in issues):
        current_words = len(edited_body.split())
        print(f"   🔄 [Editor EN] Low word count ({current_words}). Retrying with expansion prompt...")
        expand_prompt = (
            f"The following article has only {current_words} words and needs to be at least 1400 words long. "
            f"EXPAND the content: add more analysis, data, context, expert perspectives, "
            f"and dive deeper into existing points. DO NOT remove anything from the current text, only ADD.\n\n"
            f"ARTICLE TO EXPAND:\n\n{edited_body}\n\n"
            f"Return ONLY the expanded article in pure Markdown. No code blocks, no meta-comments."
        )
        expanded_body = _call_llm_en(expand_prompt, get_system_prompt_en(category))
        if expanded_body and len(expanded_body.split()) > current_words:
            # Clean wrapping
            expanded_body = expanded_body.strip()
            if expanded_body.startswith("```markdown"):
                expanded_body = expanded_body[len("```markdown"):].strip()
            if expanded_body.startswith("```"):
                expanded_body = expanded_body[3:].strip()
            if expanded_body.endswith("```"):
                expanded_body = expanded_body[:-3].strip()
            edited_body = expanded_body
            is_valid, issues = _validate_output(edited_body, body)
            print(f"   📊 [Editor EN] After expansion: {len(edited_body.split())} words")
        else:
            print(f"   ⚠️ [Editor EN] Expansion failed. Using available version.")

    if not is_valid:
        print(f"   ⚠️ [Editor EN] Validation with warnings (publishing anyway):")
        for issue in issues:
            print(f"      - {issue}")

    # A3: Guardar versión editada (preservar frontmatter y posibles bloques adicionales)
    # Rescue JSON-LD if LLM omitted it
    if '<script type="application/ld+json">' in body and '<script type="application/ld+json">' not in edited_body:
        print("   🩹 [Editor EN] Rescuing JSON-LD omitted by the LLM...")
        import re
        json_ld_match = re.search(r'(<script type="application/ld\+json">.*?</script>)', body, re.DOTALL)
        if json_ld_match:
            edited_body += f"\n\n{json_ld_match.group(1)}"

    final_body = ContentCleaner.ruthless_clean(edited_body)
    final_content = f"{frontmatter}\n\n{final_body}\n"
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    original_words = len(body.split())
    edited_words = len(edited_body.split())
    dead_fixed = len(link_result.get("dead", []))

    print(f"\n   🎉 [Editor EN] Article edited and saved!")
    print(f"      📊 Words: {original_words} → {edited_words} ({edited_words - original_words:+d})")
    print(f"      🔗 Dead links fixed: {dead_fixed}")
    print(f"      📄 File: {draft_path}")

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
    parser = argparse.ArgumentParser(description="Editor-in-Chief QA - English")
    parser.add_argument("--category", type=str, required=True)
    args = parser.parse_args()
    result = run(args.category)
    if result:
        print(f"\n{'='*60}")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
