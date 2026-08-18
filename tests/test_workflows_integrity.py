import os
import yaml

WORKFLOWS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".github", "workflows"))

EXPECTED_WORKFLOWS = [
    "biohacking_es.yml", "biohacking_en.yml",
    "funds_es.yml", "funds_en.yml",
    "tools_es.yml", "tools_en.yml",
    "ia_saas_es.yml", "ia_saas_en.yml",
    "creators_es.yml", "creators_en.yml",
    "crypto_es.yml", "crypto_en.yml",
    "viral_es.yml", "viral_en.yml"
]

def test_all_expected_workflows_exist():
    for wf in EXPECTED_WORKFLOWS:
        path = os.path.join(WORKFLOWS_DIR, wf)
        assert os.path.exists(path), f"Workflow file {wf} does not exist at {path}"

def test_workflows_yaml_validity_and_omniroute_background_config():
    for wf in EXPECTED_WORKFLOWS:
        path = os.path.join(WORKFLOWS_DIR, wf)
        with open(path, "r", encoding="utf-8") as f:
            content_str = f.read()
            f.seek(0)
            data = yaml.safe_load(f)
            
        assert data is not None, f"Workflow {wf} is empty or invalid YAML"
        
        # Verify permissions: contents: write
        permissions = data.get("permissions")
        assert permissions is not None, f"Workflow {wf} missing permissions block"
        assert permissions.get("contents") == "write", f"Workflow {wf} permissions.contents must be 'write'"
        
        # Verify env vars
        env = data.get("env", {})
        assert env.get("OMNIROUTE_BASE_URL") == "http://localhost:8000/v1"
        assert env.get("LLM_MODEL") == "auto"
        assert "GEMINI_API_KEY" in env
        assert "GROQ_API_KEY" in env
        assert "OPENROUTER_API_KEY" in env
        
        # Verify Node.js & OmniRoute background execution in steps
        assert "Setup Node.js" in content_str
        assert "omniroute --port 8000 &" in content_str
        assert "http://localhost:8000/v1/models" in content_str

def test_requirements_contains_critical_dependencies():
    req_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "requirements.txt"))
    assert os.path.exists(req_path), "requirements.txt not found"
    
    with open(req_path, "r", encoding="utf-8") as f:
        reqs = {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}
        
    critical = ["pillow", "matplotlib", "pyyaml", "requests", "openai", "together", "google-genai", "pytest"]
    for c in critical:
        assert c in reqs, f"Critical dependency '{c}' missing from requirements.txt"

