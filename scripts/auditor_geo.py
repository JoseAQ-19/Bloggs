import os
import glob
import re
import json
import random
import frontmatter
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

def scan_repository():
    files = glob.glob('content/**/*.md', recursive=True)
    stats = {
        'total': len(files),
        'has_json_ld': 0,
        'has_faq': 0,
        'has_external_links': 0,
        'has_internal_links': 0,
        'has_experts': 0,
        'latest_files': []
    }
    
    files.sort(key=os.path.getmtime, reverse=True)
    stats['latest_files'] = files[:5]
    
    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
            # Basic Regex checks
            if '<script type="application/ld+json">' in content:
                stats['has_json_ld'] += 1
            if '## Preguntas Frecuentes' in content or '## Frequently Asked Questions' in content or '## FAQ' in content:
                stats['has_faq'] += 1
            if re.search(r'\]\(http[s]?://', content):
                stats['has_external_links'] += 1
            if re.search(r'\]\(/', content):
                stats['has_internal_links'] += 1
            if re.search(r'(según|apunta|experto|director|CEO|investigador|professor|analyst|states|according to)', content, re.IGNORECASE):
                stats['has_experts'] += 1
                
    return stats

from openai import OpenAI

def evaluate_with_llm(filepaths):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        return "No API Key for Groq."
    
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    
    samples = ""
    for idx, f in enumerate(filepaths):
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            samples += f"\n\n--- SAMPLE {idx+1}: {os.path.basename(f)} ---\n{content[:5000]}"
            
    prompt = f"""EVALUATE AS CHIEF EDITOR (GSD PHASE 6 - CONTENT AUDIT).
You are to do a brutal, ruthless audit of the following generated articles from our AI blogger (Ralph Loop).
Rate the overall content on 4 pillars from 1 to 10. Give an average score for the whole system based on these samples:
1. SEO: H1-H3 hierarchy, keyword density, link logic, and JSON-LD schema presence.
2. E-E-A-T: Demonstrates Experience, Authority, Trust? Does it name experts and cite specific data, or sounds robotic?
3. GEO (Generative Engine Optimization): Is it easily indexable by Perplexity/SearchGPT? Does it use the 'chunking' rule (direct 1-sentence answer right after an H2/H3)?
4. REAL VALUE: Does it solve real search intents (like Reddit/Quora problems)? Or is it fluff/AI generic text?

OUTPUT FORMAT:
Return a Markdown report containing:
- Specific examples of failures and successes from the samples.
- The 4 Scores (1-10) clearly marked.
- EXACTLY what Ralph Loop must change in its code (`main.py`, `system_prompt`, `researcher.py`, etc.) tomorrow to get a 10/10. NO GENERIC ADVICE. Be extremely technical.

ARTICLES:
{samples}
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)



def main():
    print("Iniciando Escaneo Global de Ralph Loop...")
    stats = scan_repository()
    print(json.dumps(stats, indent=2))
    
    print("\nIniciando Evaluación de LLM Editor Jefe...")
    # Evaluate top 2 most recent + 2 random
    eval_files = stats['latest_files'][:1] + random.sample(stats['latest_files'], 1)
    
    report = evaluate_with_llm(eval_files)
    
    with open('content_auditor_phase6.md', 'w', encoding='utf-8') as f:
        f.write("# Auditoría de Contenido (Fase 6)\n")
        f.write("## Estadísticas de Repositorio\n")
        f.write(f"- Total artículos: {stats['total']}\n")
        f.write(f"- Con JSON-LD: {stats['has_json_ld']}\n")
        f.write(f"- Con sección FAQ: {stats['has_faq']}\n")
        f.write(f"- Con links externos: {stats['has_external_links']}\n")
        f.write(f"- Con links internos: {stats['has_internal_links']}\n")
        f.write("\n## Dictamen del Editor Jefe (LLM)\n")
        f.write(report)
        
    print("Reporte guardado en content_auditor_phase6.md")

if __name__ == '__main__':
    main()
