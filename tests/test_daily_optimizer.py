import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from core.daily_optimizer import DailyOptimizer

@pytest.fixture
def temp_workspace(tmp_path):
    """Crea una estructura temporal de artículos para pruebas aisladas."""
    content_dir = tmp_path / "content" / "es" / "ia"
    content_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Artículo Completo / Alto Score
    high_score_file = content_dir / "high_score.md"
    high_score_content = """---
title: "IA Generativa en 2026"
description: "Análisis técnico de modelos generativos."
translationKey: "ia-generativa-2026"
featured_image: "/images/ia-gen.webp"
faq:
  - question: "¿Qué es?"
    answer: "Un modelo probabilístico avanzado."
---

## Resumen Ejecutivo
Texto introductorio de alta calidad.

| Modelo | Parámetros | Precisión |
| :--- | :--- | :--- |
| GPT-4o | 1.8T | 94% |

## Preguntas Frecuentes
### ¿Qué es?
Un modelo probabilístico avanzado.
""" + ("\nContenido técnico extenso y detallado con datos reales. " * 60)
    high_score_file.write_text(high_score_content, encoding="utf-8")

    # 2. Artículo Débil / Bajo Score (Sin tabla, sin FAQ, con frase robótica)
    weak_file = content_dir / "weak_article.md"
    weak_content = """---
title: "Artículo Débil"
---

# Título H1 Duplicado
En el vertiginoso mundo de la tecnología este es un artículo corto sin tablas ni preguntas frecuentes.
"""
    weak_file.write_text(weak_content, encoding="utf-8")

    return str(tmp_path), str(high_score_file), str(weak_file)

def test_score_article_high_vs_weak(temp_workspace):
    base_dir, high_file, weak_file = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)

    high_res = optimizer.score_article(high_file)
    weak_res = optimizer.score_article(weak_file)

    assert high_res["score"] > 80
    assert weak_res["score"] < 60
    assert "Falta tabla comparativa Markdown (Information Gain)" in weak_res["issues"]
    assert "Falta sección de Preguntas Frecuentes (FAQ Schema)" in weak_res["issues"]

def test_find_weakest_articles(temp_workspace):
    base_dir, high_file, weak_file = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)

    weakest = optimizer.find_weakest_articles(top_n=1)
    assert len(weakest) == 1
    assert os.path.basename(weakest[0]["filepath"]) == "weak_article.md"

def test_optimize_article_injects_table_and_faq(temp_workspace):
    base_dir, _, weak_file = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)

    with patch("core.daily_optimizer.LLMRouter.route_call", return_value=None):
        res = optimizer.optimize_article(weak_file, dry_run=False)
        assert res["success"] is True
        assert len(res["changes"]) >= 2

    # Verificar que el archivo ahora tiene tabla y FAQ
    with open(weak_file, "r", encoding="utf-8") as f:
        new_content = f.read()

    assert "|" in new_content
    assert "Preguntas Frecuentes" in new_content or "Frequently Asked Questions" in new_content
    assert "vertiginoso mundo" not in new_content

def test_validate_gate_success(temp_workspace):
    base_dir, _, _ = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert optimizer.validate_gate() is True

def test_validate_gate_failure(temp_workspace):
    base_dir, _, _ = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="SyntaxError")
        assert optimizer.validate_gate() is False

def test_sync_memory_creates_files(temp_workspace, tmp_path):
    base_dir, _, _ = temp_workspace
    optimizer = DailyOptimizer(base_dir=base_dir)
    
    report = {
        "total_scanned": 10,
        "repaired_articles": [
            {
                "filepath": "content/es/ia/test.md",
                "original_score": 45,
                "changes": ["Inyectada tabla", "Añadida FAQ"]
            }
        ],
        "gate_passed": True
    }

    test_docs_path = tmp_path / "docs" / "audits"
    test_obsidian_path = tmp_path / "obsidian"
    test_obsidian_path.mkdir(parents=True, exist_ok=True)
    with patch("core.daily_optimizer.AUDIT_DOCS_PATH", str(test_docs_path)), \
         patch("core.daily_optimizer.OBSIDIAN_VAULT_PATH", str(test_obsidian_path)):
        optimizer.sync_memory(report)
        log_file = test_docs_path / "daily_log.md"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Registro Diario de Automejora Continua" in content
        assert "content/es/ia/test.md" in content

        obs_file = test_obsidian_path / "Daily_Improvements.md"
        assert obs_file.exists()
