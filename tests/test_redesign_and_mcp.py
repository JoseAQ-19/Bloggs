import json
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

def test_higgsfield_mcp_config():
    """Verify that .agent/mcp.json exists and registers the Higgsfield MCP server."""
    mcp_file = BASE_DIR / ".agent" / "mcp.json"
    assert mcp_file.exists(), ".agent/mcp.json does not exist"
    
    with open(mcp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "mcpServers" in data, "mcpServers key missing from .agent/mcp.json"
    assert "higgsfield" in data["mcpServers"], "higgsfield MCP server not registered in mcpServers"
    assert "url" in data["mcpServers"]["higgsfield"] or "command" in data["mcpServers"]["higgsfield"], \
        "higgsfield configuration missing url or command"

def test_impeccable_css_tokens():
    """Verify that custom.css implements Impeccable Taste tokens and microinteractions."""
    css_file = BASE_DIR / "static" / "css" / "custom.css"
    assert css_file.exists(), "custom.css does not exist"
    
    content = css_file.read_text(encoding="utf-8")
    
    # Check deep dark mode and palette
    assert "#0a0a0c" in content, "Missing deep dark background #0a0a0c in custom.css"
    assert "#00f2fe" in content, "Missing cyan neon accent #00f2fe in custom.css"
    assert "rgba(255, 255, 255, 0.08)" in content, "Missing subtle translucent border token in custom.css"
    
    # Check asymmetric digital magazine classes
    assert "editorial-lead-card" in content, "Missing editorial-lead-card class in custom.css"
    assert "editorial-magazine-grid" in content, "Missing editorial-magazine-grid class in custom.css"
    assert "lead-cta-btn" in content, "Missing lead-cta-btn class in custom.css"
    assert "category-pill-badge" in content, "Missing category-pill-badge class in custom.css"
    
    # Check microinteractions
    assert "cubic-bezier(0.16, 1, 0.3, 1)" in content, "Missing smooth cubic-bezier transitions"

def test_asymmetric_homepage_templates():
    """Verify that layouts/index.html and layouts/home.html contain asymmetric magazine markup."""
    home_file = BASE_DIR / "layouts" / "home.html"
    index_file = BASE_DIR / "layouts" / "index.html"
    
    assert home_file.exists(), "layouts/home.html does not exist"
    assert index_file.exists(), "layouts/index.html does not exist"
    
    for template_path in [home_file, index_file]:
        content = template_path.read_text(encoding="utf-8")
        assert "editorial-lead-card" in content, f"{template_path.name} missing editorial-lead-card spotlight"
        assert "editorial-magazine-grid" in content, f"{template_path.name} missing editorial-magazine-grid"
        assert "category-pill-badge" in content, f"{template_path.name} missing category pills"

def test_single_article_template_structure():
    """Verify that layouts/single.html contains E-E-A-T audit bio, reading progress, and TOC."""
    single_file = BASE_DIR / "layouts" / "single.html"
    assert single_file.exists(), "layouts/single.html does not exist"
    
    content = single_file.read_text(encoding="utf-8")
    assert "single-article-card" in content, "single.html missing single-article-card wrapper"
    assert "reading-progress-bar" in content, "single.html missing reading-progress-bar"
    assert "tldr-data-box" in content, "single.html missing tldr-data-box"
    assert "faq-section" in content, "single.html missing faq-section"
    assert "author-bio" in content, "single.html missing author-bio E-E-A-T box"
    assert "toc-sidebar" in content, "single.html missing toc-sidebar"

def test_image_optimization_partial():
    """Verify that GetOptimizedImage.html supports custom sizing, eager LCP, and WebP."""
    img_partial = BASE_DIR / "layouts" / "partials" / "func" / "GetOptimizedImage.html"
    assert img_partial.exists(), "GetOptimizedImage.html partial missing"
    
    content = img_partial.read_text(encoding="utf-8")
    assert "aspect-ratio: 16/9" in content, "Missing aspect-ratio: 16/9 in GetOptimizedImage.html"
    assert "fetchpriority=" in content, "Missing fetchpriority in GetOptimizedImage.html"
    assert "$spec" in content, "Missing custom resize spec support in GetOptimizedImage.html"
