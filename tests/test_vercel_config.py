import json
from pathlib import Path

def test_vercel_config_hugo_version():
    root = Path(__file__).parent.parent
    vercel_json_path = root / "vercel.json"
    assert vercel_json_path.exists(), "vercel.json should exist"
    
    with open(vercel_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    assert "env" in config, "vercel.json should have env key"
    assert "HUGO_VERSION" in config["env"], "vercel.json env should define HUGO_VERSION"
    assert "v2.12.0" in config["buildCommand"], "buildCommand should specify stable --branch v2.12.0"
    
    hugo_version = config["env"]["HUGO_VERSION"]
    major, minor, *_ = hugo_version.split(".")
    assert int(major) > 0 or int(minor) >= 128, f"HUGO_VERSION must be >= 0.128.0, got {hugo_version}"

def test_config_toml_ananke_params():
    root = Path(__file__).parent.parent
    config_toml_path = root / "config.toml"
    assert config_toml_path.exists(), "config.toml should exist"
    
    content = config_toml_path.read_text(encoding="utf-8")
    assert "[params.ananke]" in content, "config.toml should define [params.ananke] section"
    assert 'custom_css = ["css/custom.css"]' in content, "custom_css should be defined under [params.ananke]"

def test_site_analytics_partial_name():
    root = Path(__file__).parent.parent
    site_analytics_path = root / "layouts" / "partials" / "site-analytics.html"
    assert site_analytics_path.exists(), "layouts/partials/site-analytics.html should exist"
    
    baseof_path = root / "layouts" / "baseof.html"
    assert baseof_path.exists(), "layouts/baseof.html should exist"
    baseof_content = baseof_path.read_text(encoding="utf-8")
    assert 'partial "site-analytics.html"' in baseof_content, "baseof.html must use site-analytics.html partial"
    assert 'partial "google_analytics.html"' not in baseof_content, "baseof.html must not use deprecated internal template name"

