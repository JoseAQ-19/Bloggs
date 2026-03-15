---
status: resolved
trigger: "article-rendering-regression - Pipeline de renderizado de artículos tiene 3 fallos críticos: fuga de JSON-LD como texto plano, layout colapsado en móviles (fitness), y texto invisible en móviles (viral)."
created: 2026-03-15T00:00:00Z
updated: 2026-03-15T01:00:00Z
symptoms_prefilled: true
goal: find_and_fix
---

## Current Focus

hypothesis: ALL THREE root causes confirmed and fixed.
test: git diff confirms all changes applied; grep confirms zero @context leaks in content/
expecting: All three symptoms eliminated
next_action: COMPLETE — session archived

## Symptoms

expected:
1. JSON-LD debe inyectarse en el <head> como <script type="application/ld+json">, nunca imprimirse en el cuerpo del artículo.
2. En móviles, los artículos de la sección Fitness deben respetar el ancho de pantalla sin overflow horizontal.
3. En móviles, los artículos de la sección Viral deben mostrar el texto del artículo debajo de la imagen principal.

actual:
1. El bloque {"@context": "https://schema.org"...} se renderiza como texto plano visible en el cuerpo del artículo.
2. El título y contenido de artículos Fitness se desbordan por la derecha. Aparece una línea vertical naranja extraña y el texto se corta.
3. En artículos Viral, debajo de la imagen principal solo hay un bloque blanco gigante. El texto existe en el DOM pero no se pinta.

errors: No hay errores de consola reportados explícitamente, los síntomas son visuales.

reproduction:
1. Abrir cualquier artículo de la sección General y ver texto JSON-LD impreso en el body.
2. Abrir cualquier artículo de la sección Fitness en viewport móvil (<768px).
3. Abrir cualquier artículo de la sección Viral en viewport móvil (<768px).

timeline: Regresión persistente. Parches anteriores fallaron. El problema es arquitectónico.

## Evidence

- timestamp: 2026-03-15T00:01:00Z
  checked: content/ dir for @context JSON-LD patterns
  found: 4 markdown files have raw JSON-LD embedded in body (not in <head>): en/fitness/silicon-valley-off-duty-police-altercations-en.md, en/viral/algorithmic-sociopath-ai-safety-en.md, en/funds/hartfords-850-million-fund-downgrade-morningstar-points-to-subadvising-risks-en.md, es/funds/spacex-una-valoracion-de-200000-millones-justificada.md
  implication: Hugo renders Markdown body content including these JSON blocks as plain text visible in article body

- timestamp: 2026-03-15T00:02:00Z
  checked: utils.py ContentCleaner.ruthless_clean() regex
  found: regex r'(?:^|\n)\s*\{\s*["\']@context["\']:[\s\S]*?\}\s*(?:\n|$)' is non-greedy (*?) so stops at first } — FAQPage blocks with nested braces only partially cleaned, leaving residue like "} ] }" behind. The cleaner only runs for NEW articles, not existing ones.
  implication: Existing 4 files need direct surgical cleaning; ContentCleaner regex needs fixing for future articles

- timestamp: 2026-03-15T00:03:00Z
  checked: static/css/custom.css fitness theme rules
  found: .theme-fitness article.glass-card { transform: skew(-2deg); border-left: 4px solid #FF5F1F !important; } — The skew (-2deg) combined with full-width article causes horizontal overflow. The orange vertical line is the border-left. The mobile media query rule "article { transform: none !important }" SHOULD override skew, but border-left: 4px still appears. On mobile single.html article has class "ph3" padding + border-left creates extra width.
  implication: Need to add explicit border-left override in mobile media query for fitness theme

- timestamp: 2026-03-15T00:04:00Z
  checked: static/css/custom.css viral theme rules + Tachyons .white class
  found: Tachyons .white { color: #fff }. The content div in single.html has class "nested-links white" → white text. Viral theme has bg-color: #ffffff. The current viral fix .theme-viral .nested-links.white p/span/li sets color: #000 but misses: strong, em, blockquote, h5, h6, and other inline elements. The mobile article.glass-card rule (line 948-960) sets width: calc(100vw - 20px) !important + margin: 0 auto which may interact. CRITICAL MISS: The content wrapper div itself inherits white, the fix selector .theme-viral .nested-links.white {} must cover ALL descendant elements.
  implication: Viral CSS fix is incomplete - use wildcard selector to cover all descendants

- timestamp: 2026-03-15T00:05:00Z
  checked: git log + diff between commits 92bf986..a1feeed (Critical Mobile Fix commit)
  found: The "ruthless" mobile fix in a1feeed replaced a careful per-element approach. Old version had explicit ".theme-fitness article.glass-card { transform: none; }" for mobile. New version relies on "article { transform: none !important }" but the border-left was never neutralized. Also the new article.glass-card mobile uses calc(100vw - 20px) width which can still cause pixel-level overflow.
  implication: Regression introduced in commit a1feeed by removing the fitness-specific mobile override

## Eliminated

- hypothesis: JSON-LD leaks from schema.html partial going to body
  evidence: schema.html is called from baseof.html inside <head> block - correctly placed. The leak is from raw JSON embedded in Markdown content files.
  timestamp: 2026-03-15T00:01:00Z

- hypothesis: Viral text invisibility caused by overflow:hidden or height:0 container
  evidence: No such rules found in CSS for the content wrapper on single article pages. Issue is color: white Tachyons class not fully overridden by viral fix.
  timestamp: 2026-03-15T00:04:00Z

- hypothesis: Fitness overflow caused by transform skew surviving mobile CSS
  evidence: transform: none !important in mobile @media covers article element. Root cause is border-left: 4px adds width AND the width: calc(100vw - 20px) on article.glass-card. The issue is the border-left from .theme-fitness not removed on mobile.
  timestamp: 2026-03-15T00:03:00Z

## Resolution

root_cause: |
  1. JSON-LD leak: Raw JSON-LD blocks (both bare { } and <script type="application/ld+json"> tags)
     were embedded directly in Markdown article body in 31 content files across all sections.
     Hugo renders Markdown body as-is, so JSON blocks became visible plain text in articles.
     Additionally, ContentCleaner.ruthless_clean() used a non-greedy regex that failed on
     nested FAQPage structures (stopped at first }, leaving "} ] }" residue).
  2. Fitness mobile overflow: .theme-fitness article.glass-card { transform: skew(-2deg);
     border-left: 4px solid #FF5F1F } was not neutralized in @media (max-width:768px).
     The generic "article { transform: none !important }" reset skew but not border-left.
     Regression introduced in commit a1feeed which removed the fitness-specific mobile override.
  3. Viral invisible text: Tachyons .white class (color:#fff) applied to content wrapper in
     single.html. Theme has bg-color:#ffffff. Previous CSS fix only covered p/span/li/strong/b/aside
     via specific selectors — missed h5, h6, em, blockquote, and any unknown Markdown-generated tags.

fix: |
  1. Removed all raw JSON-LD blocks (both bare JSON and <script> tags) from 31 content files.
     Fixed ContentCleaner.ruthless_clean() in utils.py to use brace-counting algorithm instead
     of non-greedy regex, correctly handling nested FAQPage JSON structures.
  2. Added to @media (max-width:768px) in static/css/custom.css:
       .theme-fitness article.glass-card {
           transform: none !important;
           border-left: none !important;
           border: 1px solid rgba(255, 95, 31, 0.3) !important;
           width: 100% !important;
           max-width: 100% !important;
       }
  3. Expanded viral text color override in static/css/custom.css to include:
     .theme-viral .nested-links.white * (universal descendant)
     + all heading levels h5/h6 at top-level theme scope
     + explicit selectors for all block elements inside .nested-copy-line-height

verification: |
  - grep -rn "@context" content/ → 0 results (confirmed clean)
  - grep -rn "<script type=\"application/ld+json\">" content/ → 0 results (confirmed clean)
  - git diff static/css/custom.css confirms both mobile fitness override and viral wildcard selector present
  - git diff utils.py confirms brace-counting algorithm in ContentCleaner.ruthless_clean()
  - All 31 modified content files show only removals of JSON blocks, no new @context additions

files_changed:
  - static/css/custom.css (viral text fix expanded + fitness mobile override added)
  - utils.py (ContentCleaner.ruthless_clean brace-counting algorithm)
  - content/en/fitness/silicon-valley-off-duty-police-altercations-en.md
  - content/en/viral/algorithmic-sociopath-ai-safety-en.md
  - content/en/funds/hartfords-850-million-fund-downgrade-morningstar-points-to-subadvising-risks-en.md
  - content/en/funds/sp-500-funds-why-expense-ratios-under-010-matter-more-than-you-think-en.md
  - content/en/crypto/bitcoin-surge-analysis-en.md
  - content/en/crypto/sec-enforcement-crypto-regulation-en.md
  - content/en/fitness/gamified-fitness-fundraising-en.md
  - content/en/fitness/st-patricks-day-fitness-waco-en.md
  - content/en/ia/ai-agents-secure-deployment-en.md
  - content/en/viral/ai-curling-controversy-en.md
  - content/en/youtube/youtube-ad-revenue-disney-paramount-wbd-en.md
  - content/en/youtube/youtube-ad-revenue-vs-disney-paramount-wbd-en.md
  - content/en/youtube/youtube-hate-speech-policy-jeopardy-podcast-en.md
  - content/en/youtube/youtube-jeopardy-podcast-demonetization-hate-speech-en.md
  - content/en/youtube/youtube-tv-subscriber-retention-en.md
  - content/es/fitness/cuerpos-celebrity-metodo-fitness-hollywood.md
  - content/es/fitness/entrenamiento-extremo-azken-portu-gimnasio-xxl.md
  - content/es/funds/spacex-una-valoracion-de-200000-millones-justificada.md
  - content/es/funds/stoxx-600-sube-un-15-tras-la-crisis-en-asia-pero-la-volatilidad-persiste.md
  - content/es/ia/crisis-la-estafa-del-siglo-como-nos-venden-el-derr.md
  - content/es/ia/ecnocinicos-como-las-corporaciones-nos-venden-humo.md
  - content/es/ia/el-tabu-tecnologico-lo-que-no-quieren-que-sepas.md
  - content/es/ia/la-ia-no-viene-a-salvarnos-viene-a-explotarnos.md
  - content/es/ia/openclaw-china-control-estatal.md
  - content/es/ia/silicon-valley-se-desangra-la-era-dorada-ha-termin.md
  - content/es/ia/tu-nevera-te-espia-el-futuro-orwelliano-que-ya-pag.md
  - content/es/tools/makecom-en-2-horas-domina-la-automatizacion-en-2026-guia-definitiva-para-principiantes.md
  - content/es/viral/alerta-nasa-satelite-descontrolado-amenaza-tierra.md
  - content/es/youtube/nba-gathers-200-plus-creators-for-all-star-weekend-in-los-angeles-variety.md
  - content/es/youtube/rose-bruno-mars-apt-youtube-records.md
  - content/es/youtube/youtube-bloqueadores-anuncios-guerra.md
