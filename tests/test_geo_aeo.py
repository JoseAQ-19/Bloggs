import os
import sys
import yaml
import pytest

# Ensure scripts directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from prompts_factory import SYSTEM_FORMAT_RULES_ES, SYSTEM_FORMAT_RULES_EN
from niche_registry import NICHES, get_silo, get_author
from orchestrator import extract_faq_items, guardar_post


def test_prompts_factory_geo_aeo_rules():
    """Verifica que los system prompts contengan las reglas obligatorias RAG Chunking, Tabla y FAQ."""
    # REGLA CHUNKING RAG 40-60 PALABRAS
    assert "CHUNKING RAG" in SYSTEM_FORMAT_RULES_ES or "40 y 60 palabras" in SYSTEM_FORMAT_RULES_ES
    assert "CHUNKING RAG" in SYSTEM_FORMAT_RULES_EN or "40 and 60 words" in SYSTEM_FORMAT_RULES_EN

    # TABLA MARKDOWN OBLIGATORIA
    assert "TABLA MARKDOWN OBLIGATORIA" in SYSTEM_FORMAT_RULES_ES
    assert "MANDATORY MARKDOWN TABLE" in SYSTEM_FORMAT_RULES_EN

    # SECCIÓN FAQ OBLIGATORIA
    assert "Preguntas Frecuentes" in SYSTEM_FORMAT_RULES_ES
    assert "Frequently Asked Questions" in SYSTEM_FORMAT_RULES_EN


def test_niche_registry_silos_and_authors():
    """Verifica que cada nicho tenga un silo temático jerárquico y un autor experto asignado."""
    niche_keys = ["ia", "crypto", "fitness", "tools", "youtube", "viral", "funds", "realestate"]
    for key in niche_keys:
        silo = get_silo(key)
        author_es = get_author(key, lang="es")
        author_en = get_author(key, lang="en")

        assert "/" in silo, f"Silo '{silo}' de {key} debe ser jerárquico (ej. Finanzas/Cripto)"
        assert len(author_es) > 5, f"Autor ES de {key} no puede estar vacío"
        assert len(author_en) > 5, f"Autor EN de {key} no puede estar vacío"


def test_extract_faq_items():
    """Verifica la extracción sintética de preguntas y respuestas de un texto Markdown."""
    sample_markdown = """
## Análisis Técnico
El mercado muestra señales de volatilidad.

## Preguntas Frecuentes

### ¿Cuál es la rentabilidad esperada del Bitcoin en 2026?
La rentabilidad del Bitcoin depende del ciclo de adopción institucional y la evolución de los tipos de interés de la Fed.

### ¿Qué riesgos principales afronta la red Ethereum?
El principal riesgo técnico se relaciona con la centralización de los validadores de staking y las regulaciones sobre DeFi.

## Nuestra lectura
Cierre del artículo.
"""
    items = extract_faq_items(sample_markdown)
    assert len(items) == 2
    assert items[0]["question"] == "¿Cuál es la rentabilidad esperada del Bitcoin en 2026?"
    assert "adopción institucional" in items[0]["answer"]
    assert items[1]["question"] == "¿Qué riesgos principales afronta la red Ethereum?"


def test_guardar_post_frontmatter_structure(tmp_path, monkeypatch):
    """Verifica que guardar_post inyecte correctamente categories (silo), author y faq en el YAML."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("content/es/crypto", exist_ok=True)

    meta = {"titulo": "Prueba de Inyección GEO 2026", "slug": "prueba-geo-2026"}
    contenido = """
## Resumen Ejecutivo
- Punto 1
- Punto 2

## Análisis de Mercado
| Métrica | Valor |
| --- | --- |
| TVL | $50B |

## Preguntas Frecuentes

### ¿Qué es DeFi?
DeFi se refiere a las finanzas descentralizadas operadas mediante contratos inteligentes en blockchain.
"""

    guardar_post(meta, contenido, lang="es", category="crypto", forced_image="/images/defaults/default-crypto.jpg")

    post_file = tmp_path / "content" / "es" / "crypto" / "prueba-geo-2026" / "index.md"
    assert post_file.exists()

    raw_text = post_file.read_text(encoding="utf-8")
    assert "---" in raw_text

    yaml_parts = raw_text.split("---")
    assert len(yaml_parts) >= 3
    frontmatter = yaml.safe_load(yaml_parts[1])

    assert "author" in frontmatter
    assert "Marc Valls" in frontmatter["author"]
    assert "Finanzas/Cripto" in frontmatter["categories"]
    assert "faq" in frontmatter
    assert len(frontmatter["faq"]) >= 1
    assert frontmatter["faq"][0]["question"] == "¿Qué es DeFi?"
