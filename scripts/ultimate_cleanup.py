import os
import glob
import re
import time
import frontmatter
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Emojis regex
EMOJI_PATTERN = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u26ff]|[\u2700-\u27bf]', flags=re.UNICODE)

STATS = {
    "cleaned_emojis": 0,
    "cleaned_leaks": 0,
    "merged_disclaimers": 0,
    "regenerated": 0,
    "total": 0
}

def clean_text_surgical(content):
    # 1. Remove Emojis
    cleaned = EMOJI_PATTERN.sub('', content)
    if cleaned != content: STATS["cleaned_emojis"] += 1
    
    # 2. Remove Metadata Leaks (title:, slug:, etc. at start of lines)
    leaks = [r'^title:.*$', r'^slug:.*$', r'^description:.*$', r'^translationKey:.*$', r'^categories:.*$', r'^language:.*$']
    new_cleaned = cleaned
    for p in leaks:
        new_cleaned = re.sub(p, '', new_cleaned, flags=re.MULTILINE | re.IGNORECASE)
    if new_cleaned != cleaned: STATS["cleaned_leaks"] += 1
    cleaned = new_cleaned

    # 3. Purge Redundant Disclaimers
    # Identify patterns: ⚠️, [!IMPORTANT], old YMYL blocks
    bad_disclaimers = [
        r'⚠️.*?DISCLAIMER.*?\n',
        r'\[!IMPORTANT\].*?Aviso Editorial.*?\n',
        r'\[!IMPORTANT\].*?Editorial Disclosure.*?\n',
        r'\*YMYL Disclaimer:.*?\*',
        r'\*Aviso YMYL:.*?\*'
    ]
    for p in bad_disclaimers:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    cleaned = cleaned.strip()
    return cleaned

def is_article_broken(content):
    # Check for truncation: doesn't end with a period or closing section
    content = content.strip()
    if not content: return True
    
    # Truncation signals
    if not (content.endswith('.') or content.endswith('!') or content.endswith('"') or content.endswith('*')):
        return True
    
    # Structure signals (Mandatory sections missing)
    if '## Methodology' not in content and '## Metodología' not in content:
        return True
    if 'Key Insights' not in content and 'En Breve' not in content and 'Resumen Ejecutivo' not in content:
        return True
        
    # Word count check (< 800 words is considered "Thin")
    words = content.split()
    if len(words) < 800:
        return True

    return False

def rewrite_article(path, post):
    if not client: return False
    
    title = post.get('title', 'Unknown')
    lang = post.get('language', 'en')
    orig_content = post.content
    
    prompt = f"""TÍTULO: {title}
IDIOMA: {lang.upper()}

Eres un Editor Jefe de NovumWorld. Reescribe este contenido con profundidad absoluta (2500+ palabras).
REGLAS INQUEBRANTABLES:
- CERO EMOJIS. CERO METADATOS EN EL TEXTO.
- ESTRUCTURA: ## Key Insights (o En Breve) -> Cuerpo Denso -> ## Methodology and Sources.
- EL DISCLAIMER YMYL DEBE IR AL FINAL.

CONTENIDO BASE:
{orig_content}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)
        )
        new_text = response.text.strip()
        if new_text.startswith('```'):
            new_text = '\n'.join(new_text.split('\n')[1:-1]).strip()
        
        post.content = clean_text_surgical(new_text)
        return True
    except Exception as e:
        print(f"Error regenerando {path}: {e}")
        return False

def process_file(path):
    STATS["total"] += 1
    with open(path, 'r', encoding='utf-8') as f:
        try:
            post = frontmatter.load(f)
        except:
            return
            
    original_content = post.content
    cleaned_content = clean_text_surgical(original_content)
    
    # Unified Disclaimer logic
    lang = post.get('language', 'en')
    ymyl = "*Aviso Editorial: La información de este artículo es educativa y no constituye asesoramiento profesional. Consulte a un especialista certificado antes de tomar decisiones financieras o de salud.*" if lang == 'es' else "*Editorial Disclosure: This article is for informational purposes only and does not constitute professional advice. Always consult a certified specialist before making financial or health-related decisions.*"
    
    # Check if we should regenerate
    if is_article_broken(cleaned_content):
        if rewrite_article(path, post):
            STATS["regenerated"] += 1
            cleaned_content = post.content # Content was updated in rewrite
        else:
            # Fallback cleanup even if rewrite fails
            post.content = cleaned_content
    else:
        # Just normalize the disclaimer at the bottom
        # Locate Methodology or Related Articles
        cutoff_patterns = [r'## Methodology', r'## Metodología', r'## Related Articles', r'## Artículos Relacionados']
        found_cutoff = False
        for p in cutoff_patterns:
            match = re.search(p, cleaned_content, flags=re.IGNORECASE)
            if match:
                # Insert before
                start = match.start()
                cleaned_content = cleaned_content[:start].strip() + f"\n\n{ymyl}\n\n" + cleaned_content[start:]
                found_cutoff = True
                STATS["merged_disclaimers"] += 1
                break
        
        if not found_cutoff:
            cleaned_content += f"\n\n{ymyl}"
            STATS["merged_disclaimers"] += 1
            
        post.content = cleaned_content

    with open(path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

if __name__ == "__main__":
    files = glob.glob('content/**/*.md', recursive=True)
    # Console output must stay ASCII-only to avoid encoding issues
    print(f"[SCAN] Escaneando {len(files)} archivos...")
    for f in files:
        if '_index.md' in f or any(x in f for x in ['contact', 'privacy', 'about', 'terms']): continue
        process_file(f)
        
    print("\n" + "="*40)
    print("      RESUMEN DE CIRUGIA REPOSITORIO")
    print("="*40)
    print(f"Archivos procesados: {STATS['total']}")
    print(f"Emojis extirpados: {STATS['cleaned_emojis']}")
    print(f"Fugas de metadata purgadas: {STATS['cleaned_leaks']}")
    print(f"Disclaimers fusionados y reubicados: {STATS['merged_disclaimers']}")
    print(f"Articulos rotos REGENERADOS: {STATS['regenerated']}")
    print("="*40)
