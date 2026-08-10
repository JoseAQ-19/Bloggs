import pytest
import os
import json
import io
from PIL import Image
from visual_context_extractor import VisualContextExtractor, build_image_prompt
from visual_logger import VisualLogger
from novum_visual import NovumVisualEngine, get_image
import orchestrator

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
    assert width <= 1280 and height <= 1280

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
