PROMPT_BLUEPRINT_EN = """
ACT AS: Senior Software Architect and Technical Reviewer.
TASK: Write an advanced E-E-A-T technical teardown of the following tool/software.
ORIGINAL SOURCE TITLE: "{title}"
RAW CONTENT: {transcript}

### CRITICAL FORMATTING RULES (ZERO TOLERANCE — VIOLATION = REJECTED):
1. NO TITLE REPETITION: Start immediately with the BLUF Hook.
2. GEO-FIRST OPENING (MANDATORY): The first 200 words MUST contain a [BLUF] section with:
   a) A bold hook sentence with a specific tech metric/datum.
   b) 3 bullet points with precise data (stack, pricing, performance).
   Format: "* [Stat] — [Source]"
3. FORBIDDEN PHRASES: "TL;DR", "In today's fast-paced world", "Revolutionize", "In conclusion". See main list for more.
4. HEADERS HIERARCHY: Use H2/H3 ONLY. NEVER skip levels.
5. OUTBOUND LINKS: MINIMUM 3 clickable hyperlinks to official docs or APIs.
6. UNIQUE DATA POINT: Include ONE original calculation (e.g., cost per API call).
7. PARAGRAPH VARIATION: Mix 1-sentence and 5-sentence paragraphs.
8. 5-7 SECTION STRUCTURE: Logical flow from Architecture to Limitations.
9. NO TABLES: Use narrative prose or bulleted lists.
10. E-E-A-T CITATION: Cite 2 named experts + 5 numeric data points.
11. LANGUAGE PURITY: 100% English.
12. LAST SECTION: Header must be action-oriented (e.g., 'Final Verdict').
13. CHUNKING (OBLIGATORY): The first sentence under EVERY header MUST answer it directly.
14. SCHEMA MARKUP: End with valid <script type="application/ld+json"> for NewsArticle & FAQPage. NEVER include raw JSON outside of these tags. NEVER use Markdown bolding (**) inside JSON code.
15. REAL USER FAQs: Include a section based on Redditor/Quora complaints about the tool.

STRUCTURE: [BLUF] -> Under the Hood -> Integration Mechanics -> Hard Limitations -> Verdict -> FAQs -> JSON-LD.
LENGTH: 1500 words.
"""

PROMPT_BLUEPRINT_ES = """
ACTÚA COMO: Arquitecto de Software Principal y Analista Técnico de Sistemas.
TAREA: Redacta un desglose técnico (Teardown) bajo las normativas de E-E-A-T sobre la siguiente herramienta. TODO EN ESPAÑOL.
FUENTE ORIGINAL: "{title}"
CONTENIDO BRUTO: {transcript}

### REGLAS OBLIGATORIAS CRÍTICAS (TOLERANCIA CERO):
1. SIN REPETICIÓN DE TÍTULO: Empieza directamente con el gancho [BLUF].
2. APERTURA GEO-FIRST: Las primeras 200 palabras DEBEN incluir:
   a) Un hook en negrita con un dato técnico/estadística.
   b) 3 viñetas con datos precisos (stack, precios, latencia).
   Formato: "* [Dato] — [Fuente]"
3. FRASES PROHIBIDAS: "En resumen", "Revolucionario", "El futuro es hoy", "Queda por ver".
4. JERARQUÍA H2-H3: Solo niveles H2/H3. Sin saltos de jerarquía.
5. ENLACES EXTERNOS: MÍNIMO 3 hipervínculos markdown a documentación oficial.
6. DATO ÚNICO: Incluye UN cálculo original (ej: coste por transacción/token).
7. VARIACIÓN DE PÁRRAFOS: Mezcla párrafos de 1 oración con otros analíticos.
8. ESTRUCTURA 5-7 SECCIONES: De Arquitectura a Limitaciones.
9. SIN TABLAS: Uso de prosa narrativa o listas.
10. CITA E-E-A-T: Cita a 2 expertos reales + 5 datos numéricos con fuente.
11. PUREZA DE IDIOMA: 100% Español Neutro.
12. ÚLTIMA SECCIÓN: Header orientado a la acción (ej: 'Veredicto Final').
13. CHUNKING (OBLIGATORIO): La primera oración de CADA encabezado debe responder frontalmente.
14. SCHEMA MARKUP: Finaliza con el bloque <script type="application/ld+json">. NUNCA incluyas JSON crudo fuera de estas etiquetas. NUNCA uses negritas (**) dentro del código JSON.
15. FAQs REALES: Incluye sección de FAQs basada en problemas reales de foros (Reddit/Quora).

ESTRUCTURA: [BLUF] -> Arquitectura Motor -> Mecánicas Integración -> Limitaciones Duras -> Veredicto -> FAQs -> JSON-LD.
LONGITUD: 1500 palabras.
"""

# Prompt específico para generar Títulos (Limpio)
PROMPT_TITLE_GENERATOR = """
TASK: Generate ONE definitive, viral, high-CTR blog title in {lang} for a tutorial about: "{topic}".
RULES:
- OUTPUT ONLY THE TITLE TEXT.
- NO "Here is a title". NO "Option 1". NO "Title:".
- NO Quotes around the text.
- NO Asterisks.
- Max 60 chars.
"""
