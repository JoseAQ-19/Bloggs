from google import genai
from google.genai import types
from google.api_core import exceptions
import frontmatter
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("NO API KEY GOOGLE_API_KEY or GEMINI_API_KEY")
    exit(1)

client = genai.Client(api_key=API_KEY)

files_to_rewrite = [
    "content/en/tools/visa-ai-chargeback-hallucinations-en.md",
    "content/en/viral/sora-ai-deepfake-fears-ethical-debate-en.md",
    "content/en/tools/ai-productivity-superhuman-rows-acquisition-risks-en.md",
    "content/es/youtube/youtube-android-auto-trucos-riesgos-alternativas.md",
    "content/en/tools/induction-cooktop-roi-teardown-en.md",
    "content/es/ia/amazon-automatizacion-empleo-espana.md",
    "content/es/viral/trump-cede-ormuz-ibex.md",
    "content/es/youtube/rosalia-tabaco-campana-viral.md",
    "content/es/funds/magallanes-gana-su-tercer-premio-consecutivo-y-consolida-su-liderazgo-en-gestion.md",
    "content/en/youtube/youtuber-livestream-alibi-murder-forensics-en.md",
    "content/es/crypto/harvard-bitcoin-ethereum-elite-inversion.md",
    "content/en/crypto/secs-bold-move-defining-the-boundaries-of-crypto-securities-en.md",
    "content/en/funds/morningstar-awards-for-investing-excellence-thailand-2026-evaluating-the-top-3-f-en.md",
    "content/es/ia/silicon-valley-se-desangra-la-era-dorada-ha-termin.md",
    "content/es/youtube/ver-youtube-sin-pagar-por-esto-se-esta-volviendo-casi-imposible.md",
    "content/es/fitness/muerte-stephanie-buttermore-dietas-extremas-fitness.md",
    "content/es/ia/trabajo-y-la-distopia-2026-que-nadie-quiso-ver.md",
    "content/en/youtube/jeopardy-youtube-monetization-engagement-en.md",
    "content/es/tools/ih-set-analisis-tecnico-modelado-litoral.md",
    "content/es/crypto/makecom-dominado-en-2-horas-guia-definitiva-para-principiantes-2026.md"
]

def clean_leaked_tags(content):
    patterns = [
        r"^---\s*$.*?^---\s*$",
        r"^(title|slug|language|description|categories|tags|date|featured_image|canonical|translationKey):\s*.*$",
    ]
    cleaned = content
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.MULTILINE | re.DOTALL)
    
    cleaned_lines = []
    for line in cleaned.split("\n"):
        if not any(re.match(r"^(title|slug|translationKey|categories):", line.strip()) for pattern in patterns):
            cleaned_lines.append(line)
            
    return "\n".join(cleaned_lines).strip()

def rewrite_article(path):
    print(f"INFO: Reescribiendo {os.path.basename(path)}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            title = post.get('title', 'Unknown Title')
            meta_description = post.get('description', '')
            post.content = clean_leaked_tags(post.content)
            original_content = post.content
    except Exception as e:
        print(f"❌ Error al cargar {path}: {e}")
        return False
        
    lang = "es" if "/es/" in path.replace("\\", "/") else "en"
    tl_dr_text = "Resumen Ejecutivo (TL;DR)" if lang == "es" else "Executive Summary (TL;DR)"
    method_text = "Metodología y Fuentes" if lang == "es" else "Methodology and Sources"
    ymyl_text = "*Aviso YMYL: La información de este artículo es educativa y no constituye asesoramiento profesional. Consulte a un especialista certificado antes de tomar decisiones financieras o de salud.*" if lang == "es" else "*YMYL Disclaimer: This article is for informational purposes only and does not constitute professional advice. Always consult a certified specialist before making financial or health-related decisions.*"

    prompt = f"""TÍTULO: {title}
IDIOMA: {lang.upper()}

Eres un periodista experto de NovumWorld (AdSense Tier 1). Reescribe este contenido con rigor técnico y profundidad.

**ESTRUCTURA OBLIGATORIA:**
1. ## {tl_dr_text} (con 3-4 viñetas de datos específicos)
2. Cuerpo con subtítulos H2/H3 (estilo ensayo profundo, profesional).
3. ## {method_text}
4. {ymyl_text}

**REGLAS:** CERO YAML, CERO EMOJIS, MÍNIMO 800 PALABRAS.

CONTENIDO ORIGINAL:
{original_content}
"""

    models = ['models/gemini-2.0-flash-001', 'models/gemini-2.0-flash', 'models/gemini-2.5-flash']
    
    for m in models:
        for attempt in range(3):
            try:
                print(f"    -> Invocando {m} (Intento {attempt+1})...")
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=8192)
                )
                new_content = response.text.strip()
                if new_content.startswith('```'):
                    new_content = '\n'.join(new_content.split('\n')[1:-1]).strip()
                
                new_content = clean_leaked_tags(new_content)
                if len(new_content) < 700:
                    print(f"    ⚠️ Texto corto ({len(new_content)}).")
                    continue

                if not new_content.startswith('##'):
                    new_content = f"## {tl_dr_text}\n" + new_content

                post.content = new_content
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))
                print(f"✅ Hecho ({m}).")
                return True
            except Exception as e:
                print(f"    ❌ Error {m}: {e}")
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    print("    ⏳ Quota agotada. Esperando 15s...")
                    time.sleep(15)
                else:
                    break
    return False

if __name__ == "__main__":
    count = 0
    print("--- INICIANDO RESTAURACIÓN CON BACKOFF ---")
    for f in files_to_rewrite:
        if os.path.exists(f):
            if rewrite_article(f): count += 1
            time.sleep(5)
        else: print(f"⚠️ No existe: {f}")
    print(f"\nFIN: {count}/{len(files_to_rewrite)}")
