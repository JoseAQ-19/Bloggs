import subprocess
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

def test_agent_skills_exist():
    """Verify that all 3 requested Agent Skills exist in .agent/skills/"""
    skills_dir = BASE_DIR / ".agent" / "skills"
    
    required_skills = [
        "frontend-design-taste",
        "threejs-3d-hero",
        "responsive-ui-components"
    ]
    
    for skill_name in required_skills:
        skill_path = skills_dir / skill_name / "SKILL.md"
        assert skill_path.exists(), f"Skill file missing: {skill_path}"
        content = skill_path.read_text(encoding="utf-8")
        assert len(content) > 100, f"Skill file empty or too short: {skill_path}"
        assert "name:" in content, f"Skill YAML header missing 'name:' in {skill_path}"

def test_static_assets_exist():
    """Verify custom CSS and 3D Hero JS assets exist and contain critical tokens & multi-themes"""
    css_path = BASE_DIR / "static" / "css" / "custom.css"
    js_path = BASE_DIR / "static" / "js" / "hero-3d.js"
    
    assert css_path.exists(), "custom.css does not exist"
    assert js_path.exists(), "hero-3d.js does not exist"
    
    css_content = css_path.read_text(encoding="utf-8")
    assert "--accent-purple" in css_content or "--font-heading" in css_content, "Missing design tokens in custom.css"
    assert "hero-3d-canvas" in css_content, "Missing 3D Hero canvas styles in custom.css"
    assert "section-hero-3d" in css_content, "Missing section 3D hero header styles in custom.css"
    
    js_content = js_path.read_text(encoding="utf-8")
    assert "hero-3d-canvas" in js_content, "Missing canvas element selector in hero-3d.js"
    assert "requestAnimationFrame" in js_content, "Missing animation loop in hero-3d.js"
    assert "theme === 'crypto'" in js_content or "crypto" in js_content, "Missing crypto theme logic in hero-3d.js"

def test_hugo_templates_exist():
    """Verify Hugo templates and partials exist and contain new components & section 3D canvas"""
    hero_partial = BASE_DIR / "layouts" / "partials" / "hero.html"
    site_header_partial = BASE_DIR / "layouts" / "partials" / "site-header.html"
    home_template = BASE_DIR / "layouts" / "home.html"
    single_template = BASE_DIR / "layouts" / "single.html"
    
    assert hero_partial.exists(), "hero.html partial missing"
    assert site_header_partial.exists(), "site-header.html partial missing"
    assert home_template.exists(), "home.html template missing"
    assert single_template.exists(), "single.html template missing"
    
    hero_content = hero_partial.read_text(encoding="utf-8")
    assert "hero-3d-canvas" in hero_content, "hero.html missing canvas"
    
    site_header_content = site_header_partial.read_text(encoding="utf-8")
    assert "hero-3d-canvas" in site_header_content, "site-header.html missing section 3D canvas"
    assert 'data-theme="{{ .Section }}"' in site_header_content, "site-header.html missing data-theme binding"
    
    single_content = single_template.read_text(encoding="utf-8")
    assert "reading-progress-bar" in single_content, "single.html missing reading progress"
    assert "faq-accordion" in single_content, "single.html missing FAQ accordion"

def test_hugo_build_command():
    """Verify Hugo site builds cleanly without errors if Hugo binary is present"""
    try:
        res = subprocess.run(
            ["hugo", "--renderToMemory", "--buildDrafts"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert res.returncode == 0, f"Hugo build failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    except FileNotFoundError:
        pytest.skip("Hugo binary is not installed in local environment path")
