import frontmatter
import os
import time
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path setup to import llm_router from root
sys.path.append(str(Path(__file__).parent.parent))
from scripts.llm_router import LLMRouter

load_dotenv()

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
    print(f"INFO: Reescribiendo {os.path.basename(path)} (vía GitHub Models Fallback)...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            title = post.get('title', 'Unknown Title')
            post.content = clean_leaked_tags(post.content)
            original_content = post.content
    except Exception as e:
        print(f"❌ Error {path}: {e}")
        return False
        
    lang = "es" if "/es/" in path.replace("\\", "/") else "en"
    tl_dr = "## Resumen Ejecutivo" if lang == "es" else "## Executive Summary"
    method = "## Metodología y Fuentes" if lang == "es" else "## Methodology and Sources"
    ymyl = "*Aviso YMYL: La información de este artículo es educativa y no constituye asesoramiento profesional.*" if lang == "es" else "*YMYL Disclaimer: This article is for informational purposes only and does not constitute professional advice.*"

    system_prompt = "Eres un redactor experto de NovumWorld. Reescribe artículos AdSense Tier 1 densos y estructurados."
    prompt = f"""TÍTULO: {title}
IDIOMA: {lang.upper()}

**ESTRUCTURA OBLIGATORIA:**
1. {tl_dr} (con viñetas de datos).
2. Cuerpo largo (>800 palabras, H2/H3).
3. {method}
4. {ymyl}

CERO YAML. CERO EMOJIS.

CONTENIDO ORIGINAL:
{original_content}
"""

    try:
        # LLMRouter.call_capa_cero usa los tokens de GitHub Models que NO cuentan para la cuota de AI Studio
        new_content = LLMRouter.call_capa_cero(prompt, system_prompt, model_type="reasoning")
        
        if not new_content:
            print("    ❌ GitHub Models falló (Capa 0 agotada).")
            return False
            
        new_content = clean_leaked_tags(new_content)
        if len(new_content) < 800:
            print(f"    ⚠️ Muy corto ({len(new_content)}).")
                
        if not new_content.startswith('##'):
            new_content = f"{tl_dr}\n" + new_content

        post.content = new_content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        print(f"✅ Éxito (GitHub Model).")
        return True
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

if __name__ == "__main__":
    count = 0
    print("--- INICIANDO RESTAURACIÓN VÍA GITHUB MODELS ---")
    for f in files_to_rewrite:
        if os.path.exists(f):
            if rewrite_article(f): count += 1
            time.sleep(2)
    print(f"\nFIN: {count}/{len(files_to_rewrite)}")
