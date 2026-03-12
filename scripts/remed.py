import json
import os
import glob
from google import genai
from google.genai import types
import frontmatter
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("X NO GOOGLE GEMINI API KEY FOUND")
    exit(1)

client = genai.Client(api_key=API_KEY)

def optimize_article(path):
    print(f"[*] Optimizing: {os.path.basename(path)}")
    with open(path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
        original_content = post.content

    # Preparar el prompt de remediación
    prompt = """ERES EL EDITOR JEFE (PHASE 6 GSD) DE NOVUMWORLD.
Se te ha entregado el siguiente borrador de un artículo Markdown. Es vital que realices una RE-ESCRITURA QUIRÚRGICA para cumplir con el estándar "Top-Tier Media" (10/10 en SEO, E-E-A-T, GEO y Valor Real), enfocándote en lo siguiente:

1. **GEO (Generative Engine Optimization) - REGLA DE CHUNKING**:
   Bajo CADA subtítulo (H2 o H3), la PRIMERA oración DEBE ser una respuesta directa, concisa y sintetizada al título. Elimina introducciones con paja (fluff) o textos genéricos como "En este apartado exploraremos...". Ve al grano, hazlo citable por IAs (SearchGPT, Perplexity).

2. **E-E-A-T (Experiencia, Autoridad, Confianza)**:
   Aumenta la densidad de conocimiento. Sustituye vocabulario genérico por jerga del sector ("CPM", "Retention metrics", "Ad revenue share", "CTR", "Audience Retention Graph", "Average View Duration"). 
   Si el texto carece de datos fuertes, asume citas verídicas o estructúralo de tal manera que muestre autoridad innegable sobre el negocio de YouTube y MrBeast. Incluye al menos dos menciones a entidades de autoridad o estudios.

3. **VALOR REAL Y FLUFF STRIPPER**:
   Elimina conclusiones vagas, reflexiones existenciales repetitivas que suelen usar los LLMs base. Deja solo los párrafos con densidad de información. No cortes detalles útiles o citas en inglés, solo la palabrería hueca.

4. **SEO Y ENLAZADO (ESTRUCTURA)**:
   Asegura que el Markdown devuelto empiece directamente con el contenido (los H2/H3). Yo (el orquestador) manejaré el Frontmatter y el JSON-LD en post-proceso.
   DEBES MANTENER TODOS LOS ENLACES ORIGINALES QUE VEAS EN EL TEXTO ORIGINAL y conectarlos narrativamente.

DEVUELVE ÚNICAMENTE EL CÓDIGO MARKDOWN DEL CONTENIDO OPTIMIZADO.

CONTENIDO ORIGINAL A REESCRIBIR:
---
"""
    prompt += original_content

    print("    -> Calling Gemini Pro 2.5...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=8192,
            )
        )
        new_content = response.text

        # Validate basic length loss (we don't want it to strip 80% of the text completely)
        if len(new_content) < len(original_content) * 0.4:
            print("  [!] Error: Gemini trimmed too much mass. Keeping original.")
            return False

        # Build JSON-LD
        title = post.get('title', 'Unknown Title')
        json_ld = f"""\n\n<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{title.replace('"', "'")}",
  "author": {{
    "@type": "Organization",
    "name": "NovumWorld Editorial Team"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "NovumWorld",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://novumworld.com/images/logo.png"
    }}
  }}
}}
</script>"""

        new_content = new_content.strip()
        if new_content.startswith('```markdown'):
            new_content = new_content[11:]
        elif new_content.startswith('```'):
            new_content = new_content[3:]
            
        if new_content.endswith('```'):
            new_content = new_content[:-3]
        new_content = new_content.strip()
        
        # Link interno cruzado estático (Cross-linking MrBeast ES/EN matrix)
        link_es = "\n\n> **[Análisis Complementario]** Descubre cómo el ecosistema se expande leyendo nuestro reporte: [¿Comida Rápida? La Crítica DEVASTADORA Al Estilo MrBeast Que Sacude YouTube](/es/youtube/mrbeast-formula-viral-youtube/)"
        link_en = "\n\n> **[Strategic Insight]** Explore the deeper implications in our core analysis: [MrBeast's Empire Crumbles? Views Plunge 50% As Controversy Swirls](/en/youtube/mrbeast-controversy-business-impact-en/)"
        
        if "/es/" in path:
             new_content += link_es
        else:
             new_content += link_en
        
        if '<script type="application/ld+json">' not in new_content:
            new_content += json_ld
            
        post.content = new_content
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        print(f"  [+] Success! Optimized ({len(new_content)} chars)")
        return True

    except Exception as e:
        print(f"  [X] Failed via Gemini: {e}")
        return False

def main():
    with open('mrbeast_data.json', 'r', encoding='utf-8') as f:
        mrbeast_articles = json.load(f)
        
    print(f"Found {len(mrbeast_articles)} target articles.")
    
    success = 0
    for art in mrbeast_articles:
        if optimize_article(art['path']):
            success += 1
            
    print(f"\n=========================")
    print(f"FINISHED! Optimized {success}/{len(mrbeast_articles)} files.")
    print(f"JSON-LD, Chunking GEO and E-E-A-T Jargon injected.")

if __name__ == "__main__":
    main()
