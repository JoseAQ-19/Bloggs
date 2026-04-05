#!/usr/bin/env python3
"""
🦅 PROTOCOLO FÉNIX: Remasterización Masiva de Contenido Legacy
================================================================
- Preserva frontmatter (título, fecha, imagen, slug) INTACTO.
- Reescribe el body con Framework Contrariano + E-E-A-T.
- Inyecta 3-5 outbound links reales a fuentes de alta autoridad.
- Purga frases robóticas prohibidas.
- Corrige **Bold** headers → ## H2.
- Sanea translationKeys huérfanas.
- Marca archivos procesados con `remastered: true`.
"""

import os
import re
import sys
import time
import glob
from dotenv import load_dotenv

load_dotenv()

from google import genai

GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# ============================================================
# CONFIGURACIÓN
# ============================================================
CONTENT_DIRS = ["content/es", "content/en"]
SKIP_FILES = ["_index.md", "about.md", "contact.md", "privacy.md"]
SLEEP_BETWEEN = 8  # Segundos entre cada llamada API

REMASTER_PROMPT_ES = """ACTÚA COMO: Editor Jefe Contrariano de un medio de investigación tecnológica de élite.

TAREA: Reescribe el siguiente artículo aplicando estas reglas ESTRICTAS:

1. FRAMEWORK CONTRARIANO:
   - Mantén la esencia y el tema original, pero reescríbelo con opiniones FUERTES y polarizantes.
   - Encuentra la grieta en la narrativa y explótala.
   - Está PROHIBIDO terminar con tibiezas como "el tiempo lo dirá" o "depende de nosotros".
   - Toma una postura definitiva en la conclusión.

2. PURGA DE FRASES ROBÓTICAS (ELIMINAR TODAS):
   - "En última instancia"
   - "En conclusión" / "En resumen"
   - "Solo el tiempo lo dirá"
   - "Un arma de doble filo"
   - "En el vertiginoso mundo"
   - "Cabe destacar"
   - "Es importante señalar"
   - "Queda por ver"
   - "El paisaje digital"
   - "Navegar por el panorama"

3. POLÍTICA ESTRICTA DE ENLACES EXTERNOS (OUTBOUND LINKS):
   - PROHIBIDO inventar, adivinar o fabricar URLs.
   - SOLO puedes convertir en hipervínculos las URLs que ya aparezcan explícitamente en el cuerpo original o que te proporcione el sistema.
   - Si el artículo original no contiene URLs y el sistema no te da ninguna, reescribe TODO el contenido SIN añadir enlaces externos nuevos.
   - Cuando sí haya URLs reales disponibles, conviértelas a formato Markdown [texto descriptivo](https://url-real-verificable.com) copiando la URL EXACTA.

4. ESTRUCTURA MARKDOWN:
   - Usa ## para subtítulos (H2). NUNCA **negrita** como subtítulo.
   - Varía la longitud de los párrafos (1 a 6 oraciones).
   - Máximo UNA lista con viñetas por artículo.
   - Incluye al menos un dato numérico con contexto comparativo.

5. IDIOMA: Todo el texto DEBE estar en ESPAÑOL. Cero anglicismos innecesarios.

6. NO INCLUIR el título del artículo al inicio. Empieza directamente con el gancho.

7. LONGITUD: Mantén una longitud similar al original (mínimo 800 palabras).

ARTÍCULO ORIGINAL A REESCRIBIR:
---
{body}
---

DEVUELVE SOLO EL TEXTO REESCRITO EN MARKDOWN. SIN EXPLICACIONES. SIN COMILLAS."""

REMASTER_PROMPT_EN = """ACT AS: Contrarian Editor-in-Chief of an elite investigative tech publication.

TASK: Rewrite the following article applying these STRICT rules:

1. CONTRARIAN FRAMEWORK:
   - Keep the original topic and essence, but rewrite with STRONG, polarizing opinions.
   - Find the crack in the narrative and exploit it.
   - FORBIDDEN to end with lukewarm conclusions like "only time will tell" or "it's up to us".
   - Take a definitive stance in the conclusion.

2. PURGE ROBOTIC PHRASES (ELIMINATE ALL):
   - "It remains to be seen"
   - "In conclusion" / "In summary"
   - "A double-edged sword"
   - "In the ever-evolving landscape"
   - "It's worth noting"
   - "Navigating the complexities"
   - "The digital landscape"
   - "Only time will tell"

3. STRICT URL POLICY FOR OUTBOUND LINKS:
   - You are STRICTLY FORBIDDEN from inventing, guessing, or fabricating ANY URL.
   - You may ONLY add hyperlinks using URLs that already exist explicitly in the original body or that are provided by the system.
   - If the original article and the system context do NOT provide URLs, rewrite the article with ZERO external links.
   - When URLs are available, convert them to Markdown [descriptive anchor text](https://real-verifiable-url.com) copying the URL VERBATIM.

4. MARKDOWN STRUCTURE:
   - Use ## for subheadings (H2). NEVER **bold** as subheading.
   - Vary paragraph length (1 to 6 sentences).
   - Maximum ONE bulleted list per article.
   - Include at least one numerical data point with comparative context.

5. LANGUAGE: ALL text MUST be in ENGLISH. Zero unnecessary foreign words.

6. DO NOT include the article title at the beginning. Start directly with the hook.

7. LENGTH: Maintain similar length to the original (minimum 800 words).

ORIGINAL ARTICLE TO REWRITE:
---
{body}
---

RETURN ONLY THE REWRITTEN TEXT IN MARKDOWN. NO EXPLANATIONS. NO QUOTES."""


# ============================================================
# HELPERS
# ============================================================

def split_frontmatter_body(content):
    """Separa el frontmatter YAML del body del artículo."""
    # Match --- delimited frontmatter
    match = re.match(r'^(---\s*\n.*?\n---\s*\n)(.*)', content, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, content


def is_already_remastered(frontmatter):
    """Comprueba si el artículo ya fue remasterizado."""
    return "remastered: true" in frontmatter or "remastered: \"true\"" in frontmatter


def has_outbound_links(body):
    """Comprueba si el body tiene al menos 1 outbound link."""
    return bool(re.search(r'\[.+?\]\(https?://', body))


def get_translation_key(frontmatter):
    """Extrae la translationKey del frontmatter."""
    match = re.search(r'translationKey:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
    return match.group(1).strip().strip('"').strip("'") if match else None


def build_translation_index():
    """Construye un índice de todas las translationKeys existentes por idioma."""
    index = {"es": set(), "en": set()}
    for lang in ["es", "en"]:
        for fpath in glob.glob(f"content/{lang}/**/*.md", recursive=True):
            basename = os.path.basename(fpath)
            if basename in SKIP_FILES:
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)
                key = get_translation_key(content)
                if key:
                    index[lang].add(key)
            except Exception:
                continue
    return index


def remove_orphan_translation_key(frontmatter, lang, trans_index):
    """Si la translationKey no tiene pareja en el otro idioma, la elimina."""
    key = get_translation_key(frontmatter)
    if not key:
        return frontmatter, False
    
    other_lang = "en" if lang == "es" else "es"
    if key not in trans_index.get(other_lang, set()):
        # Eliminar la línea translationKey
        frontmatter = re.sub(r'translationKey:.*\n', '', frontmatter)
        return frontmatter, True
    return frontmatter, False


def add_remastered_flag(frontmatter):
    """Añade remastered: true al frontmatter antes del cierre ---."""
    if "remastered:" in frontmatter:
        return frontmatter
    # Insertar antes del último ---
    return frontmatter.rstrip().rstrip('-').rstrip() + "\nremastered: true\n---\n"


def detect_lang(fpath):
    """Detecta el idioma del archivo por su path."""
    if "/es/" in fpath:
        return "es"
    elif "/en/" in fpath:
        return "en"
    return "en"  # default


def rewrite_body(body, lang, title=""):
    """Envía el body al LLM para reescritura Contrariana + Links."""
    if not client:
        print("      ❌ No hay API key de Gemini configurada.")
        return None
    
    prompt_template = REMASTER_PROMPT_ES if lang == "es" else REMASTER_PROMPT_EN
    prompt = prompt_template.format(body=body[:12000])  # Limitar input
    
    try:
        resp = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        result = resp.text.strip()
        
        # Validación mínima
        if len(result) < 400:
            print(f"      ⚠️ Respuesta demasiado corta ({len(result)} chars). Saltando.")
            return None
        
        # Limpiar posibles artefactos del LLM
        result = result.strip('```').strip('markdown').strip()
        if result.startswith('```'):
            result = re.sub(r'^```\w*\n', '', result)
            result = re.sub(r'\n```$', '', result)
        
        return result
        
    except Exception as e:
        print(f"      ❌ Error LLM: {e}")
        return None


# ============================================================
# MAIN
# ============================================================

def main():
    print("🦅 PROTOCOLO FÉNIX: Remasterización Masiva de Contenido Legacy")
    print("=" * 60)
    
    # 1. Construir índice de traducciones
    print("\n📋 Construyendo índice de translationKeys...")
    trans_index = build_translation_index()
    print(f"   ES keys: {len(trans_index['es'])} | EN keys: {len(trans_index['en'])}")
    
    # 2. Recopilar todos los archivos .md
    all_files = []
    for content_dir in CONTENT_DIRS:
        for fpath in glob.glob(f"{content_dir}/**/*.md", recursive=True):
            basename = os.path.basename(fpath)
            if basename in SKIP_FILES:
                continue
            all_files.append(fpath)
    
    print(f"\n📁 Total archivos encontrados: {len(all_files)}")
    
    # Contadores
    stats = {
        "total": len(all_files),
        "remastered": 0,
        "skipped_already": 0,
        "skipped_error": 0,
        "orphan_keys_fixed": 0,
        "links_injected": 0,
    }
    
    # 3. Procesar cada archivo
    for i, fpath in enumerate(all_files):
        rel_path = fpath.replace("content/", "")
        print(f"\n[{i+1}/{stats['total']}] 📄 {rel_path}")
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"   ❌ Error leyendo: {e}")
            stats["skipped_error"] += 1
            continue
        
        frontmatter, body = split_frontmatter_body(content)
        
        if not frontmatter:
            print("   ⚠️ Sin frontmatter válido. Saltando.")
            stats["skipped_error"] += 1
            continue
        
        # Skip si ya fue remasterizado
        if is_already_remastered(frontmatter):
            print("   ✅ Ya remasterizado. Saltando.")
            stats["skipped_already"] += 1
            continue
        
        lang = detect_lang(fpath)
        modified = False
        
        # --- CIRUGÍA 3: Sanear translationKey huérfana ---
        frontmatter, key_removed = remove_orphan_translation_key(frontmatter, lang, trans_index)
        if key_removed:
            print(f"   🔗 translationKey huérfana eliminada.")
            stats["orphan_keys_fixed"] += 1
            modified = True
        
        # --- CIRUGÍA 1 & 2: Reescritura Contrariana + Links ---
        # Siempre reescribir si no tiene links O si no está remasterizado
        needs_rewrite = not has_outbound_links(body) or not is_already_remastered(frontmatter)
        
        if needs_rewrite:
            # Extraer título para contexto
            title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
            title = title_match.group(1).strip().strip('"') if title_match else ""
            
            print(f"   ✍️ Reescribiendo [{lang.upper()}]: {title[:60]}...")
            new_body = rewrite_body(body, lang, title)
            
            if new_body:
                # Verificar que tiene links
                if has_outbound_links(new_body):
                    stats["links_injected"] += 1
                    print(f"   🔗 Links inyectados correctamente.")
                else:
                    print(f"   ⚠️ El LLM no inyectó links. Guardando de todas formas.")
                
                body = new_body
                modified = True
                print(f"   ✅ Reescrito ({len(new_body)} chars).")
            else:
                print(f"   ⚠️ Reescritura fallida. Manteniendo original.")
        
        # --- Guardar si hubo cambios ---
        if modified:
            # Añadir flag de remasterizado
            frontmatter = add_remastered_flag(frontmatter)
            
            # Preservar la imagen inline si existía al inicio del body original
            # (Hugo Ananke usa ![title](image) justo después del frontmatter)
            image_match = re.match(r'^\s*(!\[.*?\]\(.*?\))\s*\n', body)
            
            # Reconstruir archivo
            final_content = frontmatter + "\n" + body.strip() + "\n"
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            stats["remastered"] += 1
            print(f"   💾 Guardado.")
        
        # Rate limiting
        if needs_rewrite and modified:
            print(f"   ⏳ Rate limit: sleep({SLEEP_BETWEEN}s)...")
            time.sleep(SLEEP_BETWEEN)
    
    # 4. Reporte final
    print("\n" + "=" * 60)
    print("🦅 PROTOCOLO FÉNIX: REPORTE FINAL")
    print("=" * 60)
    print(f"📁 Total archivos escaneados:    {stats['total']}")
    print(f"✅ Remasterizados con éxito:     {stats['remastered']}")
    print(f"🔗 Con links inyectados:         {stats['links_injected']}")
    print(f"🔗 translationKeys saneadas:     {stats['orphan_keys_fixed']}")
    print(f"⏭️  Ya remasterizados (skip):     {stats['skipped_already']}")
    print(f"❌ Errores/saltados:             {stats['skipped_error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
