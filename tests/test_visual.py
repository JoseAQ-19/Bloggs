import pytest
import os
import json
import io
import hashlib
from unittest.mock import patch, MagicMock
from PIL import Image
from visual_context_extractor import VisualContextExtractor, build_image_prompt
from visual_logger import VisualLogger
from novum_visual import (
    NovumVisualEngine,
    get_image,
    generate_unique_visual_prompt,
    _derive_seed,
    _sanitize_prompt,
    BANNED_PROMPT_WORDS,
)
import orchestrator


# ═══════════════════════════════════════════════════════════════════
# EXISTING TESTS (preserved)
# ═══════════════════════════════════════════════════════════════════

def test_visual_context_extractor():
    content = """
    Elon Musk announces a new AI model with 100B parameters. 
    The S&P 500 reached an all-time high of $5000 following a sudden bull market surge. 
    Tesla's TVL in crypto is surprisingly high.
    This is an alarming situation for legacy automakers.
    """
    
    extractor = VisualContextExtractor()
    ctx = extractor.extract("Elon Musk announces AI", content, "ia")
    
    # Check entities
    assert "Elon Musk" in ctx.primary_entity or "Elon Musk" in ctx.secondary_entities
    assert "Tesla" in ctx.secondary_entities or len(ctx.secondary_entities) > 0
    assert any("$5000" in t[0] for t in ctx.key_numbers) or len(ctx.key_numbers) > 0

def test_visual_logger(tmp_path):
    # Override log dir for testing
    original_log_dir = VisualLogger.LOG_DIR
    VisualLogger.LOG_DIR = str(tmp_path)
    
    VisualLogger.log("test-slug", "ia", "Test Title", "Cinematic prompt", "nvidia", "success")
    
    log_file = os.path.join(str(tmp_path), "image_prompts.jsonl")
    assert os.path.exists(log_file)
    
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = json.loads(f.readline())
        
    assert log_content["slug"] == "test-slug"
    assert log_content["provider"] == "nvidia"
    assert log_content["prompt"] == "Cinematic prompt"
    
    # Restore log dir
    VisualLogger.LOG_DIR = original_log_dir

def test_build_image_prompt():
    title = "Bitcoin Surges Past $100K!"
    content = "A massive bull market and green candles everywhere as BTC spikes. CEO Brian Armstrong tweets about it."
    
    prompt = build_image_prompt(title, content, "crypto")
    assert "Bitcoin" in prompt
    assert "green" in prompt.lower() or "bull" in prompt.lower() or "market" in prompt.lower()
    assert "crypto" in prompt.lower() or "bitcoin" in prompt.lower() or "trading" in prompt.lower()

def test_webp_conversion_and_compression(tmp_path):
    # Create a large dummy image (2000x2000 RGB)
    img = Image.new('RGB', (2000, 2000), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    raw_bytes = buf.getvalue()
    
    engine = NovumVisualEngine()
    target_path = os.path.join(str(tmp_path), "featured.webp")
    success, width, height = engine.process_and_save_webp(raw_bytes, target_path, max_size_kb=150)
    
    assert success is True
    assert os.path.exists(target_path)
    assert target_path.endswith(".webp")
    
    file_size_kb = os.path.getsize(target_path) / 1024
    assert file_size_kb < 150
    assert width > 0 and height > 0
    # Updated: now bounded by 1200x630 instead of 1280x1280
    assert width <= 1200 and height <= 630

def test_leaf_bundle_generation(tmp_path):
    engine = NovumVisualEngine()
    bundle_dir = str(tmp_path / "test-category" / "test-slug-bundle")
    
    # Generate and save in bundle_dir
    img_ref, width, height = engine.generate_and_save(
        title="Test Leaf Bundle Article",
        content="This is content for testing leaf bundle.",
        slug="test-slug-bundle",
        category="ia",
        bundle_dir=bundle_dir
    )
    
    assert img_ref == "featured.webp"
    featured_path = os.path.join(bundle_dir, "featured.webp")
    assert os.path.exists(featured_path)
    assert os.path.getsize(featured_path) / 1024 < 150
    assert width > 0 and height > 0

def test_orchestrator_guardar_post_leaf_bundle():
    meta = {
        'titulo': 'Prueba Leaf Bundle Hugo',
        'slug': 'test-hugo-leaf-bundle'
    }
    contenido = "Este es un articulo de prueba para la migración a Leaf Bundles de Hugo."
    contexto = {
        "sources": ["https://example.com/source1"],
        "key_findings": ["Finding 1", "Finding 2"]
    }
    
    orchestrator.guardar_post(meta, contenido, lang="es", category="ia", contexto=contexto)
    
    bundle_dir = "content/es/ia/test-hugo-leaf-bundle"
    index_file = os.path.join(bundle_dir, "index.md")
    featured_file = os.path.join(bundle_dir, "featured.webp")
    brief_file = os.path.join(bundle_dir, "research_brief.json")
    
    assert os.path.exists(index_file)
    assert os.path.exists(featured_file)
    assert os.path.exists(brief_file)
    
    # Check WebP compression < 150 KB
    assert os.path.getsize(featured_file) / 1024 < 150
    
    # Check frontmatter content
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'featured_image: "featured.webp"' in content or 'featured_image: featured.webp' in content
    assert 'image_width:' in content
    assert 'image_height:' in content
    
    # Cleanup test files
    try:
        import shutil
        shutil.rmtree(bundle_dir)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# NEW TESTS — Unique Image Generation (V7)
# ═══════════════════════════════════════════════════════════════════

class TestSeedDerivation:
    """Tests for deterministic seed generation from slug."""

    def test_same_slug_same_seed(self):
        """Same slug must always produce the same seed."""
        seed1 = _derive_seed("my-article-slug")
        seed2 = _derive_seed("my-article-slug")
        assert seed1 == seed2

    def test_different_slugs_different_seeds(self):
        """Different slugs must produce different seeds."""
        seed_a = _derive_seed("impacto-llama-33-servidores-privados")
        seed_b = _derive_seed("nvidia-h200-gpu-benchmark-review")
        seed_c = _derive_seed("bitcoin-etf-blackrock-sec-approval")
        assert seed_a != seed_b
        assert seed_b != seed_c
        assert seed_a != seed_c

    def test_seed_range(self):
        """Seed must be within [0, 999999]."""
        for slug in ["a", "test-slug", "very-long-slug-with-many-words-here", "日本語スラグ"]:
            seed = _derive_seed(slug)
            assert 0 <= seed <= 999999

    def test_seed_uses_sha256(self):
        """Verify seed derivation uses SHA-256 (not Python's non-deterministic hash())."""
        slug = "test-determinism"
        digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()
        expected = int(digest[:12], 16) % 1000000
        assert _derive_seed(slug) == expected


class TestPromptSanitization:
    """Tests for banned word removal from prompts."""

    def test_removes_banned_words(self):
        dirty = "A beautiful illustration of technology concept with abstract background"
        clean = _sanitize_prompt(dirty)
        for banned in ["illustration of", "technology concept", "abstract background"]:
            assert banned not in clean

    def test_preserves_clean_prompts(self):
        clean_prompt = "A futuristic datacenter corridor illuminated by cyan neural networks"
        result = _sanitize_prompt(clean_prompt)
        assert result == clean_prompt

    def test_cleans_double_spaces(self):
        dirty = "A   test   with   spaces"
        result = _sanitize_prompt(dirty)
        assert "  " not in result


class TestUniqueVisualPrompt:
    """Tests for LLM-driven visual prompt generation."""

    @patch("llm_router.LLMRouter")
    def test_generates_prompt_with_llm(self, mock_router):
        """Verify LLM is called and prompt contains seed fingerprint."""
        mock_router.route_call.return_value = (
            "A sprawling quantum computing lab with holographic data streams, "
            "deep violet and electric blue palette, dramatic backlighting, "
            "8k resolution, editorial photography, sharp focus, professional lighting"
        )
        
        result = generate_unique_visual_prompt(
            title="Quantum Computing Breakthrough",
            summary="New quantum processor achieves 1000 qubits.",
            category="ia",
            slug="quantum-computing-breakthrough"
        )

        assert mock_router.route_call.called
        assert len(result.split()) >= 10
        # Must contain seed fingerprint
        seed = _derive_seed("quantum-computing-breakthrough")
        assert str(seed) in result

    @patch("llm_router.LLMRouter")
    def test_falls_back_to_regex_on_llm_failure(self, mock_router):
        """If LLM fails, must fall back to build_image_prompt()."""
        mock_router.route_call.return_value = None

        result = generate_unique_visual_prompt(
            title="Bitcoin ETF Approved by SEC",
            summary="BlackRock's Bitcoin ETF receives SEC approval.",
            category="crypto",
            slug="bitcoin-etf-sec-approval"
        )

        assert result is not None
        assert len(result) > 20
        # Fallback must still contain seed fingerprint
        seed = _derive_seed("bitcoin-etf-sec-approval")
        assert str(seed) in result

    @patch("llm_router.LLMRouter")
    def test_three_articles_produce_different_prompts(self, mock_router):
        """Three different articles must produce three different prompts."""
        # Simulate LLM returning unique prompts for each call
        mock_router.route_call.side_effect = [
            "A sprawling quantum lab with holographic streams, violet palette, dramatic backlighting, 8k resolution, editorial photography, sharp focus, professional lighting",
            "A bustling Wall Street trading floor with green candlestick displays, golden ambient glow, overhead angle, 8k resolution, editorial photography, sharp focus, professional lighting",
            "An Olympic athlete mid-sprint on a wet track at sunset, orange and crimson sky, motion blur, low angle, 8k resolution, editorial photography, sharp focus, professional lighting",
        ]

        articles = [
            ("Quantum Computing Breakthrough", "New quantum processor.", "ia", "quantum-computing-breakthrough"),
            ("Bitcoin ETF Surge on Wall Street", "Bitcoin ETFs see record inflows.", "crypto", "bitcoin-etf-wall-street-surge"),
            ("Zone 2 Training Revolution", "New study on mitochondrial biogenesis.", "fitness", "zone-2-training-revolution"),
        ]

        prompts = []
        for title, summary, category, slug in articles:
            prompt = generate_unique_visual_prompt(title, summary, category, slug)
            prompts.append(prompt)

        # All three must be different
        assert prompts[0] != prompts[1]
        assert prompts[1] != prompts[2]
        assert prompts[0] != prompts[2]

        # Each must contain its own seed
        for i, (_, _, _, slug) in enumerate(articles):
            seed = _derive_seed(slug)
            assert str(seed) in prompts[i], f"Prompt {i} missing seed {seed}"

    @patch("llm_router.LLMRouter")
    def test_prompt_contains_no_banned_words(self, mock_router):
        """LLM output must be sanitized of banned generic words."""
        mock_router.route_call.return_value = (
            "An illustration of technology concept showing abstract background "
            "with generic stock photo style, professional lighting"
        )

        result = generate_unique_visual_prompt(
            title="Test Article",
            summary="Test summary content.",
            category="ia",
            slug="test-banned-words"
        )

        for banned in BANNED_PROMPT_WORDS:
            assert banned not in result, f"Banned word '{banned}' found in sanitized prompt"


class TestFallbackHonesty:
    """Regresión: el fallback local no debe enmascarar placeholders como imágenes únicas."""

    def test_flat_fallback_returns_shared_default_path(self, tmp_path):
        from novum_visual import NovumVisualEngine
        engine = NovumVisualEngine()
        ref, w, h = engine._get_fallback_image("crypto", str(tmp_path / "slug-x.webp"), "/images/slug-x.webp")
        assert ref.startswith("/images/defaults/")
        assert not (tmp_path / "slug-x.webp").exists()

    def test_bundle_fallback_still_writes_featured(self, tmp_path):
        from novum_visual import NovumVisualEngine
        engine = NovumVisualEngine()
        bundle = str(tmp_path / "bundle")
        os.makedirs(bundle, exist_ok=True)
        ref, w, h = engine._get_fallback_image("fitness", os.path.join(bundle, "featured.webp"), "featured.webp")
        assert ref == "featured.webp"
        assert os.path.exists(os.path.join(bundle, "featured.webp"))

    def test_category_alias_biohacking_maps_to_fitness(self):
        from novum_visual import _normalize_category
        assert _normalize_category("biohacking") == "fitness"
        assert _normalize_category("criptomonedas") == "crypto"
        assert _normalize_category("crypto") == "crypto"
        assert _normalize_category("") == "ia"


class TestWebPBoundingBox:
    """Tests for the updated 1200x630 bounding box resize."""

    def test_landscape_image_fits_bounding_box(self, tmp_path):
        """A wide landscape image should fit within 1200x630."""
        img = Image.new('RGB', (2400, 1260), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)

        engine = NovumVisualEngine()
        target = str(tmp_path / "landscape.webp")
        success, w, h = engine.process_and_save_webp(buf.getvalue(), target)

        assert success
        assert w <= 1200
        assert h <= 630

    def test_portrait_image_fits_bounding_box(self, tmp_path):
        """A tall portrait image should fit within 1200x630."""
        img = Image.new('RGB', (800, 1600), color=(200, 100, 50))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)

        engine = NovumVisualEngine()
        target = str(tmp_path / "portrait.webp")
        success, w, h = engine.process_and_save_webp(buf.getvalue(), target)

        assert success
        assert w <= 1200
        assert h <= 630

    def test_small_image_not_upscaled(self, tmp_path):
        """Images smaller than 1200x630 should not be upscaled."""
        img = Image.new('RGB', (600, 300), color=(50, 200, 100))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)

        engine = NovumVisualEngine()
        target = str(tmp_path / "small.webp")
        success, w, h = engine.process_and_save_webp(buf.getvalue(), target)

        assert success
        assert w == 600
        assert h == 300
