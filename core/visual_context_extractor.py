"""
VISUAL_CONTEXT_EXTRACTOR.PY — Motor de Extracción de Contexto Visual
=====================================================================
Extrae entidades, datos y tonos del artículo para construir prompts
de imagen hiper-específicos y alineados con el contenido.

Author: Auditoría Técnica
Version: 1.0.0
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VisualContext:
    """Contexto visual extraído del artículo."""
    # Entidades Principales
    primary_entity: str = ""  # "Bitcoin", "ETF", "Hyperliquid", "MrBeast"
    secondary_entities: List[str] = None  # ["SEC", "Grayscale", "FTX"]

    # Datos Numéricos Clave
    key_numbers: List[Tuple[str, str]] = None  # [("$74M", "liquidation"), ("4.25B", "TVL")]

    # Tono Emocional
    emotional_tone: str = ""  # "dramatic", "analytical", "warning", "celebration"

    # Contexto Visual
    visual_context: str = ""  # "trading floor", "gym", "studio", "data center"

    # Acción Principal
    primary_action: str = ""  # "falling", "rising", "analyzing", "training"

    # Keywords para Style Transfer
    style_keywords: List[str] = None


class VisualContextExtractor:
    """
    Extrae contexto visual desde el contenido del artículo.
    """

    # ── REGISTRO DE ESTILOS VISUALES POR NICHO ──
    VISUAL_STYLES = {
        "crypto": {
            "base_style": "professional financial photography",
            "color_palette": ["dark blue", "gold", "emerald green", "charcoal"],
            "compositions": ["trading desk with multiple monitors", "stock chart close-up",
                           "abstract blockchain visualization", "corporate boardroom"],
            "lighting": ["dramatic rim lighting", "cold monitor glow", "golden hour through glass"],
            "avoid": ["cartoons", "3d renders", "neon cyberpunk", "anime style"],
            "keywords_priority": ["chart", "graph", "candlestick", "portfolio", "portfolio"]
        },
        "fitness": {
            "base_style": "editorial sports photography",
            "color_palette": ["orange", "black", "white", "electric blue"],
            "compositions": ["athlete mid-workout", "gym interior wide shot",
                           "muscle anatomy illustration", "sweat droplet macro"],
            "lighting": ["dramatic side lighting", "golden hour outdoor", "studio strobe"],
            "avoid": ["cartoon", "anime", "illustration style"],
            "keywords_priority": ["athlete", "workout", "gym", "muscle", "training"]
        },
        "ia": {
            "base_style": "futuristic technology editorial",
            "color_palette": ["deep purple", "cyan", "white", "dark grey"],
            "compositions": ["server room perspective", "AI neural network visualization",
                           "robot hand with circuit", "futuristic interface close-up"],
            "lighting": ["neon glow", "holographic light", "cold LED"],
            "avoid": ["dystopian", "scary", "horror"],
            "keywords_priority": ["AI", "neural", "algorithm", "server", "robot"]
        },
        "youtube": {
            "base_style": "streaming studio photography",
            "color_palette": ["red", "white", "black", "purple"],
            "compositions": ["streamer at desk setup", "microphone close-up",
                           "recording studio interior", "play button 3D"],
            "lighting": ["ring light", "RGB ambient", "studio softbox"],
            "avoid": ["corporate", "stock photo generic"],
            "keywords_priority": ["streamer", "studio", "microphone", "camera", "recording"]
        },
        "viral": {
            "base_style": "editorial photojournalism",
            "color_palette": ["magenta", "yellow", "black", "white"],
            "compositions": ["newspaper front page", "viral moment capture",
                           "crowd reaction", "trending visualization"],
            "lighting": ["dramatic editorial", "fashion spotlight", "moody atmosphere"],
            "avoid": ["cartoon", "illustration", "anime"],
            "keywords_priority": ["trending", "viral", "news", "reaction", "moment"]
        },
        "funds": {
            "base_style": "institutional financial photography",
            "color_palette": ["navy blue", "gold", "white", "dark grey"],
            "compositions": ["financial document close-up", "portfolio allocation chart",
                           "corporate meeting room", "stock exchange floor"],
            "lighting": ["professional studio", "natural office light", "golden hour corporate"],
            "avoid": ["neon", "cyberpunk", "cartoon"],
            "keywords_priority": ["portfolio", "fund", "investment", "allocation", "chart"]
        }
    }

    # ── MAPEO DE TONOS EMOCIONALES ──
    EMOTIONAL_TONES = {
        "warning": ["crash", "fall", "loss", "risk", "danger", "warning", "collapse",
                   "horror", "crisis", "threat", "wipeout", "exposed"],
        "celebration": ["soars", "rally", "surge", "breakthrough", "record", "win",
                       "success", "growth", "boom", "milestone"],
        "analytical": ["analysis", "data", "study", "report", "research", "evidence",
                      "metric", "benchmark", "comparison"],
        "dramatic": ["dramatic", "shocking", "stunning", "reveals", "exposes", "secret",
                    "hidden", "bomb", "time bomb"]
    }

    # ── ACCIONES VISUALES POR VERBO ──
    ACTION_MAPPING = {
        "loss": "falling", "crash": "crashing", "fall": "falling",
        "rise": "rising", "surge": "surging", "growth": "growing",
        "analysis": "analyzing", "study": "studying", "research": "researching",
        "expose": "exposing", "reveal": "revealing", "warning": "warning",
        "training": "training", "workout": "working out"
    }

    def __init__(self):
        pass

    def extract(self, title: str, content: str, category: str) -> VisualContext:
        """
        Extrae contexto visual completo desde título y contenido.

        Args:
            title: Título del artículo
            content: Contenido completo del artículo (primeras 2000 palabras)
            category: Categoría/nicho (crypto, fitness, ia, etc.)

        Returns:
            VisualContext con todos los campos extraídos
        """
        ctx = VisualContext(secondary_entities=[], key_numbers=[], style_keywords=[])

        # 1. Extraer Entidad Principal
        ctx.primary_entity = self._extract_primary_entity(title, content)

        # 2. Extraer Entidades Secundarias
        ctx.secondary_entities = self._extract_secondary_entities(content, ctx.primary_entity)

        # 3. Extraer Números Clave
        ctx.key_numbers = self._extract_key_numbers(title + " " + content)

        # 4. Detectar Tono Emocional
        ctx.emotional_tone = self._detect_emotional_tone(title + " " + content)

        # 5. Determinar Contexto Visual
        ctx.visual_context = self._determine_visual_context(title, content, category)

        # 6. Extraer Acción Principal
        ctx.primary_action = self._extract_primary_action(title + " " + content)

        # 7. Generar Keywords de Estilo
        ctx.style_keywords = self._generate_style_keywords(category, ctx)

        return ctx

    def _extract_primary_entity(self, title: str, content: str) -> str:
        """Extrae la entidad principal del título."""
        # Patrones de entidad: Nombre propio, Ticker ($BTC), Empresa
        patterns = [
            r'\$([A-Z]{2,5})\b',  # Tickers: $BTC, $ETH
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Nombres propios
            r'([A-Z]{2,})\b',  # Siglas: ETF, SEC, CEO
        ]

        # Buscar en título primero
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                entity = match.group(1)
                # Validar que no sea palabra común
                common_words = ['The', 'This', 'That', 'What', 'How', 'Why', 'When']
                if entity not in common_words and len(entity) > 2:
                    return entity

        # Buscar en las primeras 500 palabras del contenido
        first_500 = content[:500] if content else ""
        for pattern in patterns:
            matches = re.findall(pattern, first_500)
            for m in matches:
                if m and len(m) > 2 and m not in ['The', 'This', 'That', 'What', 'How', 'Why']:
                    return m

        return "topic"  # Fallback genérico

    def _extract_secondary_entities(self, content: str, primary: str) -> List[str]:
        """Extrae entidades secundarias (empresas, personas, organizaciones)."""
        entities = []

        # Patrones de organizaciones
        org_patterns = [
            r'\b(SEC|FTC|FDA|CNN|BBC|Reuters|Bloomberg|Forbes|TechCrunch|The Verge)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Group|Capital|Fund))?)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'  # Nombres de personas
        ]

        text = content[:2000] if content else ""

        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m and m != primary and m not in entities and len(m) > 3:
                    entities.append(m)

        return entities[:5]  # Top 5 entidades secundarias

    def _extract_key_numbers(self, text: str) -> List[Tuple[str, str]]:
        """Extrae números clave con su contexto."""
        numbers = []

        # Patrón: número + contexto cercano
        pattern = r'(\$[\d.]+[BMK]?|[0-9,]+%|[0-9.]+\s*(?:billion|million|thousand))'
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            num = match.group(1)
            # Extraer contexto (palabras anteriores y posteriores)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end]
            # Limpiar contexto
            context = re.sub(r'[^\w\s]', ' ', context).strip()
            numbers.append((num, context))

        return numbers[:5]  # Top 5 números

    def _detect_emotional_tone(self, text: str) -> str:
        """Detecta el tono emocional del texto."""
        text_lower = text.lower()

        tone_scores = {}
        for tone, keywords in self.EMOTIONAL_TONES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                tone_scores[tone] = score

        if tone_scores:
            return max(tone_scores, key=tone_scores.get)
        return "neutral"

    def _determine_visual_context(self, title: str, content: str, category: str) -> str:
        """Determina el contexto visual apropiado."""
        text_lower = (title + " " + content[:1000]).lower()

        # Mapeo de palabras clave a contextos visuales
        context_keywords = {
            "trading floor": ["trading", "trader", "market", "stock", "exchange", "floor"],
            "gym": ["gym", "workout", "exercise", "fitness", "training", "muscle"],
            "studio": ["studio", "streamer", "youtube", "video", "podcast", "recording"],
            "data center": ["server", "data", "cloud", "AI", "neural", "algorithm"],
            "corporate office": ["CEO", "executive", "corporate", "company", "board"],
            "street protest": ["protest", "movement", "viral", "trending", "reaction"],
            "home office": ["remote", "home", "freelance", "entrepreneur"]
        }

        for context, keywords in context_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return context

        # Fallback por categoría
        category_contexts = {
            "crypto": "trading floor",
            "fitness": "gym",
            "ia": "data center",
            "youtube": "studio",
            "viral": "street scene",
            "funds": "corporate office"
        }

        return category_contexts.get(category, "professional setting")

    def _extract_primary_action(self, text: str) -> str:
        """Extrae la acción principal del artículo."""
        text_lower = text.lower()

        for action_keyword, visual_action in self.ACTION_MAPPING.items():
            if action_keyword in text_lower:
                return visual_action

        return "analyzing"  # Default

    def _generate_style_keywords(self, category: str, ctx: VisualContext) -> List[str]:
        """Genera keywords de estilo específicas para el prompt."""
        style_config = self.VISUAL_STYLES.get(category, self.VISUAL_STYLES["ia"])
        keywords = []

        # 1. Estilo base
        keywords.append(style_config["base_style"])

        # 2. Colores (uno aleatorio pero determinístico basado en tono)
        color_map = {
            "warning": "red and dark grey",
            "celebration": "gold and white",
            "analytical": "blue and white",
            "dramatic": "purple and black",
            "neutral": style_config["color_palette"][0]
        }
        keywords.append(color_map.get(ctx.emotional_tone, "neutral colors"))

        # 3. Composición basada en contexto visual
        if ctx.visual_context in style_config["compositions"]:
            keywords.append(ctx.visual_context)
        else:
            keywords.append(style_config["compositions"][0])

        # 4. Iluminación basada en tono
        lighting_map = {
            "warning": "dramatic red accent lighting",
            "celebration": "bright golden hour lighting",
            "analytical": "clean studio lighting",
            "dramatic": "moody atmosphere with rim light",
            "neutral": style_config["lighting"][0]
        }
        keywords.append(lighting_map.get(ctx.emotional_tone, "professional lighting"))

        return keywords


# ── MASTER IMAGE PROMPT BUILDER ──

class ImagePromptBuilder:
    """
    Construye prompts de imagen hiper-específicos usando el contexto extraído.
    """

    # Templates por nicho
    TEMPLATES = {
        "crypto": """
{entity} {action} visualization, {composition}, {style_keywords[0]},
{key_number} displayed on screen, {secondary_entities_text}
{style_keywords[1]} color scheme, {style_keywords[2]}, {style_keywords[3]},
professional financial editorial photography, sharp focus, 8k resolution,
no text, no watermark, no cartoon, realistic photography
""",
        "fitness": """
{entity} {action} in {composition}, {style_keywords[0]},
{primary_entity} prominently featured, athletic physique details,
{style_keywords[1]} lighting, {style_keywords[2]}, sweat and effort visible,
{style_keywords[3]}, editorial sports photography, dynamic pose,
no text overlay, professional shot, realistic human anatomy
""",
        "ia": """
{entity} {action} concept visualization, {composition},
{style_keywords[0]}, futuristic technology aesthetic,
{secondary_entities_text} elements in background,
{style_keywords[1]} palette, {style_keywords[2]}, {style_keywords[3]},
clean modern design, editorial tech photography, sharp details,
no text, no watermark, professional quality
""",
        "youtube": """
{entity} {action} in {composition}, {style_keywords[0]},
streaming setup with {secondary_entities_text},
{style_keywords[1]} atmosphere, {style_keywords[2]},
{style_keywords[3]}, professional streaming photography,
modern equipment, shallow depth of field, vibrant colors,
no text overlay, realistic photography
""",
        "viral": """
{entity} {action} moment, {composition}, {style_keywords[0]},
editorial photojournalism style, {secondary_entities_text},
{style_keywords[1]} lighting, {style_keywords[2]}, {style_keywords[3]},
newspaper quality, dramatic moment capture, sharp focus,
professional editorial photography, no cartoons, realistic
""",
        "funds": """
Professional financial setting, {entity} {action}, institutional photography,
{style_keywords[0]} tone, {style_keywords[1]} color palette, shallow depth of field,
documentary style, modern corporate office environment,
financial visualization without text, no text rendering, no UI elements, no charts with text,
extremely high quality, realistic lighting, 8k resolution
"""
    }

    @staticmethod
    def build(ctx: VisualContext, category: str) -> str:
        """
        Construye el prompt final a partir del contexto extraído.

        Args:
            ctx: VisualContext extraído del artículo
            category: Categoría del artículo

        Returns:
            Prompt de imagen listo para enviar a la API
        """
        template = ImagePromptBuilder.TEMPLATES.get(category, ImagePromptBuilder.TEMPLATES["ia"])

        # Formatear entidades secundarias
        secondary_text = ""
        if ctx.secondary_entities:
            secondary_text = f"with {', '.join(ctx.secondary_entities[:3])}"

        # Formatear número clave
        key_number_text = ""
        if ctx.key_numbers:
            num, context = ctx.key_numbers[0]
            key_number_text = f"{num} ({context})"
        else:
            key_number_text = "key data"

        # Construir prompt
        prompt = template.format(
            entity=ctx.primary_entity,
            primary_entity=ctx.primary_entity, # Added this to match fitness template
            action=ctx.primary_action,
            composition=ctx.visual_context,
            style_keywords=ctx.style_keywords,
            key_number=key_number_text,
            secondary_entities_text=secondary_text
        )

        # Limpiar y formatear
        prompt = " ".join(prompt.split())  # Normalizar espacios
        prompt = prompt.strip()
        return prompt

def build_image_prompt(title: str, content: str, category: str) -> str:
    """
    Función principal para generar un prompt de imagen a partir de un artículo.
    """
    extractor = VisualContextExtractor()
    ctx = extractor.extract(title, content, category)
    return ImagePromptBuilder.build(ctx, category)
