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
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# NotebookLM MCP
MCP_BINARY = "notebooklm-mcp"

# =====================================================
# TAREA C1: SYSTEM PROMPT DEL EDITOR JEFE EN
# =====================================================

SYSTEM_PROMPT_EDITOR_EN = """ROLE: You are the EDITOR-IN-CHIEF of NovumWorld, a premium US tech publication. Your mission is to receive a DRAFT article written by a junior writer and return it PERFECT for immediate publication.

YOUR PROFILE:
- Veteran tech journalist with 20 years at TechCrunch, The Verge, and Ars Technica.
- Cynical, demanding, allergic to corporate fluff and ChatGPT-flavored prose.
- Expert in US-market on-page SEO (.com).
- Your English is impeccable American English. You know the difference between "colour" and "color", "analyse" and "analyze".

YOUR MISSION (in this priority order):
1. PURE ENGLISH: If you find ANY sentence, heading, or paragraph in Spanish, TRANSLATE it to American English. Exception: proper nouns that are inherently Spanish (names of Spanish companies, etc.).
2. DEAD LINKS: I will provide a list of links that returned HTTP 404/timeout. You MUST:
   - Remove the broken markdown link: convert [text](dead_url) to **text** (bold, no link).
   - NEVER fabricate a new URL. If you don't have the real link, leave it in bold.
3. BANNED PHRASES: Find and REPLACE (with equivalent but more original content) these phrases:
   - "In the ever-evolving landscape of..."
   - "In summary / In conclusion"
   - "A double-edged sword"
   - "Navigating the complexities of..."
   - "It's important to note that..."
   - "It remains to be seen"
   - "Game-changer" (without data)
   - "poised for explosive growth"
   - "deep dive"
   - "in today's digital landscape"
   - "is revolutionizing"
   - "driving innovation"
   - "Here is the rewritten text"
4. FACT-CHECK: If I provide verification alerts (from NotebookLM), review the flagged claims and:
   - If a data point is clearly fabricated, remove it or replace with a verifiable generalization.
   - If a data point is suspicious but plausible, add a qualifier ("according to market estimates").
5. SEO: Ensure H2/H3 headings contain relevant English keywords. No more than one H1.
6. LENGTH: The EDITED article must have at least 1200 words. If you remove content, you MUST add equivalent content to compensate.

RESPONSE FORMAT (CRITICAL):
- Return ONLY the edited article text in pure Markdown.
- Do NOT include code blocks (```markdown), do NOT include meta-comments, do NOT explain your changes.
- Do NOT modify the YAML frontmatter (---.....---). Only edit the content AFTER the second ---.
- The first character of your response should be the start of the article (usually ![image]...).
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

def _call_llm_en(prompt, system_prompt):
    """
    LLM cascade for Editor EN: OpenRouter GLM → Gemini Flash.
    Returns: string with corrected article, or None on failure.
    """
    # Attempt 1: OpenRouter (GLM-4.5-Air)
    if OPENROUTER_KEY:
        try:
            print("   🧠 [Editor EN] Trying OpenRouter GLM-4.5-Air...")
            or_client = OpenAI(
                api_key=OPENROUTER_KEY,
                base_url="https://openrouter.ai/api/v1"
            )
            response = or_client.chat.completions.create(
                model="z-ai/glm-4.5-air:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=16000
            )
            result = response.choices[0].message.content.strip()
            if result and len(result) > 500:
                print(f"   ✅ [Editor EN] OpenRouter responded: {len(result)} chars")
                return result
        except Exception as e:
            print(f"   ⚠️ [Editor EN] OpenRouter failed: {e}")

    # Attempt 2: Gemini 2.0 Flash
    if GEMINI_KEY:
        try:
            print("   🧠 [Editor EN] Fallback to Gemini 2.0 Flash...")
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
                print(f"   ✅ [Editor EN] Gemini responded: {len(result)} chars")
                return result
        except Exception as e:
            print(f"   ⚠️ [Editor EN] Gemini failed: {e}")

    print("   ❌ [Editor EN] All LLMs failed.")
    return None


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
    ]
    lower_text = edited_text.lower()
    for phrase in banned:
        if phrase in lower_text:
            issues.append(f"Banned phrase found: '{phrase}'")

    is_valid = len(issues) == 0
    return is_valid, issues


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

    # STEP 1: Link Validation
    print(f"\n   🔗 [Editor EN] STEP 1: Link verification...")
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

    # STEP 2: NotebookLM Fact-Check
    print(f"\n   🔍 [Editor EN] STEP 2: Fact-check with NotebookLM...")
    factcheck_alerts = _notebooklm_factcheck_en(body)
    factcheck_block = ""
    if factcheck_alerts:
        factcheck_block = f"\n\n{factcheck_alerts}"

    # STEP 3: Build LLM prompt
    print(f"\n   🧠 [Editor EN] STEP 3: Sending to LLM for editing...")
    user_prompt = (
        f"DRAFT TO EDIT:\n\n{body}"
        f"{dead_links_block}"
        f"{factcheck_block}"
        f"\n\nReturn ONLY the edited article in pure Markdown. "
        f"No code blocks, no meta-comments."
    )

    edited_body = _call_llm_en(user_prompt, SYSTEM_PROMPT_EDITOR_EN)

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
        expanded_body = _call_llm_en(expand_prompt, SYSTEM_PROMPT_EDITOR_EN)
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

    # A3: Save edited version (preserve frontmatter)
    final_content = f"{frontmatter}\n\n{edited_body}\n"
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
