import pytest
import os
import json
from visual_context_extractor import VisualContextExtractor, build_image_prompt
from visual_logger import VisualLogger

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
