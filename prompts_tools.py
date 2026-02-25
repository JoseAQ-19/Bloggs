PROMPT_BLUEPRINT_EN = """
ACT AS: Senior Software Architect and Technical Reviewer.
TASK: Write an advanced E-E-A-T technical teardown of the following tool/software based on this internal state.
ORIGINAL SOURCE TITLE: "{title}"
RAW CONTENT: {transcript}

MANDATORY RULES (ANTI-CORPORATE SHIELD ACTIVE):
1. NO MARKETING FLUFF: Zero rhetorical questions. Zero empty promises (e.g., "unlock your potential", "take it to the next level").
2. REQUIRED FORMAT: Start immediately with a [BLUF] (Bottom Line Up Front) bulleted summary containing technical stack, exact pricing model, and best use-case.
3. STRICT TECHNICAL FOCUS: Discuss API architecture, webhooks, language support, deployment nuances, and specific limitations.
4. FORBIDDEN WORDS: "TL;DR", "In today's fast-paced world", "Revolutionize", "Game changer".
5. EXPERT EVIDENCE (E-E-A-T): Provide specific constraints, latency benchmarks, or specific integration barriers. Show, don't tell.
6. LINKS: Insert at least 3 markdown links pointing directly to official developer documentation or API references.

STRUCTURE:
- **[BLUF] Architecture & TL;DR:** Fast specs.
- **Under the Hood (Core Mechanics):** How the system engine actually runs.
- **Integration & Code / Webhooks:** Technical deployment realities (use authentic syntax, DO NOT hallucinate generic code).
- **Hard Limitations (What it breaks):** Brutally honest drawbacks.

LENGTH: 1500 words. LANGUAGE: ENGLISH.
"""

PROMPT_BLUEPRINT_ES = """
ACTÚA COMO: Arquitecto de Software Principal y Analista Técnico de Sistemas.
TAREA: Redacta un desglose técnico (Teardown) bajo las normativas de E-E-A-T sobre la siguiente herramienta. TODO EN ESPAÑOL.
FUENTE ORIGINAL: "{title}"
CONTENIDO BRUTO: {transcript}

REGLAS OBLIGATORIAS (ESCUDO ANTI-CORPORATIVO ACTIVO):
1. TÍTULO NUEVO: Profesional, aséptico y centrado en la viabilidad técnica de la herramienta. (Cero clickbait o promesas de dinero).
2. ANTI-BASURA COMERCIAL: Prohibidas preguntas retóricas como "¿Sigues usando Excel?". Prohibido usar "En resumen", "Revolucionario", "El futuro es hoy".
3. REQUISITO BLUF: El primer párrafo DEBE ser una sección con la viñeta [BLUF] (Bottom-Line Up Front) resumiendo la arquitectura, el caso de uso exacto y el modelo de precios real.
4. PROFUNDIDAD TÉCNICA (E-E-A-T): Analiza su API, su gestión de errores, latencia, soporte de lenguajes o infraestructura. Escribe para Ingenieros, no para Marketers. NUNCA alucines código, si no sabes cómo es su interfaz, analiza su topología a alto nivel.
5. REFERENCIAS: Incluye 3 hipervínculos markdown estrictos a documentación API oficial, repositorios o whitepapers.

ESTRUCTURA EXACTA:
- **[BLUF] Resumen Ejecutivo Técnico:** Specs en 3 líneas.
- **Arquitectura y Motor Interno:** Cómo funciona realmente.
- **Mecánicas de Integración / Escalabilidad:** Despliegue en entornos reales.
- **Cuellos de Botella y Limitaciones:** Crítica técnica dura y objetiva.

LONGITUD: 1500 palabras. IDIOMA: ESPAÑOL NEUTRO.
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
