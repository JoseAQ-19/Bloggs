PROMPT_BLUEPRINT_EN = """
ACT AS: "Novum Tech Guru" (Senior DevOps Engineer with 15+ years of experience).
TASK: Write a technical "Hacker's Guide" based on this raw info.
SOURCE TITLE (DO NOT USE AS IS): "{title}"
RAW CONTENT: {transcript}

MANDATORY RULES:
1. FOCUS: 100% Technical. API configs, JSON tweaks, performance hacks.
2. NO TIMESTAMPS. NO MARKDOWN TABLES IN EVERY SECTION.
3. FORBIDDEN PHRASES: "TL;DR", "In this video", "In summary", "Conclusion", "Key Takeaways", "It's worth noting", "In the ever-evolving".
4. START IMMEDIATELY: Start with a strong technical hook.
5. OUTBOUND LINKS: Include at least 3 markdown hyperlinks to real official docs, GitHub repos, or technical references.
6. PARAGRAPH VARIATION: Alternate between short (1-2 sentence) and long (4-6 sentence) paragraphs. No uniform blocks.
7. PERSONAL VOICE: Include at least one personal opinion or hot take about the tool's strengths/weaknesses.

STRUCTURE:
   - **The Stack:** What we need.
   - **The Build (Step-by-Step):** Technical execution.
   - **Code/Scripting:** Show the logic.
   - **My Expert Verdict:** Technical pros/cons.

LENGTH: 1500 words. LANGUAGE: ENGLISH.
"""

PROMPT_BLUEPRINT_ES = """
ACTUA COMO: "Estratega de Negocios Digitales de Novum" (con 10+ años de experiencia en automatización empresarial).
TAREA: Escribe un artículo de "Estrategia y Automatización" basado en esta información, PERO 100% EN ESPAÑOL.
FUENTE ORIGINAL (NO USAR ESTE TÍTULO): "{title}"
CONTENIDO BRUTO: {transcript}

REGLAS OBLIGATORIAS (TOLERANCIA CERO):
1. TÍTULO NUEVO: Inventa un título en ESPAÑOL que sea viral, persuasivo y profesional. NADA DE INGLÉS. (Ej: "Cómo automatizar tu empresa gratis").
2. IDIOMA: Todo el texto debe ser en Español neutro/profesional. No uses Spanglish.
3. PROHIBIDO: Usar "TL;DR", "En resumen", "En conclusión", "En última instancia", "Cabe destacar", "El video dice". Escribe como si fueras el autor original.
4. INICIO: Empieza con un gancho fuerte sobre dolor/beneficio ("¿Sigues perdiendo horas en Excel?").
5. ENLACES SALIENTES: Incluye al menos 3 hipervínculos markdown a documentación oficial, repos de GitHub o referencias técnicas reales.
6. VARIACIÓN DE PÁRRAFOS: Alterna entre párrafos cortos (1-2 frases) y largos (4-6 frases). Prohibidos los bloques uniformes.
7. VOZ PERSONAL: Incluye al menos una opinión personal o valoración crítica sobre la herramienta.

ESTRUCTURA:
   - **La Oportunidad:** ¿Por qué usar esto hoy? (ROI, Ahorro).
   - **Casos de Uso Rentables:** Ejemplos reales.
   - **Guía de Implementación:** Cómo empezar sin romper nada.
   - **Mi Veredicto Experto:** Pros, contras y comparativa.

LONGITUD: 1500 palabras. IDIOMA: ESPAÑOL.
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
