#!/usr/bin/env python3
"""
TEST_UNIFIED_WATERFALL.PY — Tests automáticos para el Waterfall Unificado v3.
=============================================================================
Valida que:
1. NVIDIA NIM API responde correctamente (Llama-3.1-70B)
2. GitHub Models API responde correctamente (GPT-4o)
3. El motor unificado funciona para EN y ES
4. NO quedan residuos de Zhipu/GLM/OpenRouter en el código
5. El orden de TIERs es correcto

Ejecutar: python test_nvidia_integration.py
Exit Code 0 = PASS, Exit Code 1 = FAIL
"""

import os
import sys
import json
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Resultados del test
results = {"passed": 0, "failed": 0, "skipped": 0, "details": []}
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY")
GH_TOKEN = os.getenv("GITHUB_MODELS_TOKEN")


def log_result(test_name, status, message=""):
    """Registra el resultado de un test."""
    results["details"].append({
        "test": test_name,
        "status": status,
        "message": message
    })
    results[status] += 1
    icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}[status]
    print(f"   {icon} [{status.upper()}] {test_name}: {message}")


# ==================================================================
# TEST 1: Verificación de Credenciales
# ==================================================================
def test_api_keys_present():
    """Verifica que las API keys están configuradas."""
    if NVIDIA_KEY:
        log_result("NVIDIA_API_KEY Present", "passed", f"Key starts with: {NVIDIA_KEY[:10]}...")
    else:
        log_result("NVIDIA_API_KEY Present", "failed", "NVIDIA_API_KEY not found")

    if GH_TOKEN:
        log_result("GITHUB_MODELS_TOKEN Present", "passed", f"Token starts with: {GH_TOKEN[:10]}...")
    else:
        log_result("GITHUB_MODELS_TOKEN Present", "skipped", "GITHUB_MODELS_TOKEN not set — TIER 2 will be skipped in production")


# ==================================================================
# TEST 2: NVIDIA NIM / Llama-3.1-70B (TIER 1)
# ==================================================================
def test_nvidia_tier1():
    """Prueba TIER 1: NVIDIA NIM Llama-3.1-70B."""
    if not NVIDIA_KEY:
        log_result("TIER 1: NVIDIA Llama-3.1-70B", "skipped", "No API key")
        return

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=NVIDIA_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )

        # Test EN
        resp = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": "Write 3 sentences about the future of AI in journalism. Be concise."}],
            temperature=0.85,
            max_tokens=256
        )
        result_en = resp.choices[0].message.content.strip()
        
        if len(result_en.split()) >= 10:
            log_result("TIER 1: NVIDIA EN", "passed", f"{len(result_en.split())} words")
        else:
            log_result("TIER 1: NVIDIA EN", "failed", f"Only {len(result_en.split())} words")

        # Test ES
        resp_es = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": "Escribe 3 oraciones sobre el futuro de la IA en el periodismo. Sé conciso. Escribe TODO en español."}],
            temperature=0.85,
            max_tokens=256
        )
        result_es = resp_es.choices[0].message.content.strip()
        
        if len(result_es.split()) >= 10:
            log_result("TIER 1: NVIDIA ES", "passed", f"{len(result_es.split())} words")
        else:
            log_result("TIER 1: NVIDIA ES", "failed", f"Only {len(result_es.split())} words")

    except Exception as e:
        log_result("TIER 1: NVIDIA Llama-3.1-70B", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 3: GitHub Models / GPT-4o (TIER 2)
# ==================================================================
def test_github_tier2():
    """Prueba TIER 2: GitHub Models GPT-4o."""
    if not GH_TOKEN:
        log_result("TIER 2: GitHub Models GPT-4o", "skipped", "No GITHUB_MODELS_TOKEN")
        return

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=GH_TOKEN,
            base_url="https://models.inference.ai.azure.com"
        )

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Write 3 sentences about renewable energy trends. Be concise."}],
            temperature=0.85,
            max_tokens=256
        )
        result = resp.choices[0].message.content.strip()
        
        if len(result.split()) >= 10:
            log_result("TIER 2: GitHub Models GPT-4o", "passed", f"{len(result.split())} words")
        else:
            log_result("TIER 2: GitHub Models GPT-4o", "failed", f"Only {len(result.split())} words")
    except Exception as e:
        log_result("TIER 2: GitHub Models GPT-4o", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 4: _call_unified_engine Import Test
# ==================================================================
def test_unified_engine_exists():
    """Verifica que _call_unified_engine existe en main.py y es importable."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from main import _call_unified_engine
        log_result("_call_unified_engine Exists", "passed", "Function imported successfully")
    except ImportError as e:
        log_result("_call_unified_engine Exists", "failed", f"Import error: {e}")
    except Exception as e:
        log_result("_call_unified_engine Exists", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 5: Zhipu/GLM Residue Check (CRITICAL)
# ==================================================================
def test_no_zhipu_residue():
    """Verifica que NO quedan residuos de Zhipu/GLM en main.py."""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()
        
        banned_patterns = [
            "ZHIPU_API_KEY",
            "zhipu_key",
            "glm_client",
            "glm-4-flash",
            "glm-4.7-flashx",
            "z-ai/glm",
            "bigmodel.cn",
            "_call_nvidia_nim",
            "_call_en_engine",
        ]
        
        found = [p for p in banned_patterns if p in code]
        
        if not found:
            log_result("No Zhipu/GLM Residue (main.py)", "passed", f"All {len(banned_patterns)} banned patterns absent")
        else:
            log_result("No Zhipu/GLM Residue (main.py)", "failed", f"FOUND residues: {found}")
    except Exception as e:
        log_result("No Zhipu/GLM Residue", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 6: Zhipu/GLM Residue in stocks_writer.py
# ==================================================================
def test_no_zhipu_residue_stocks():
    """Verifica que NO quedan residuos de Zhipu/GLM/DeepSeek/Groq en stocks_writer.py."""
    try:
        with open("stocks_writer.py", "r", encoding="utf-8") as f:
            code = f.read()
        
        banned_patterns = [
            "ZHIPU",
            "zhipu",
            "glm_client",
            "deepseek",
            "DeepSeek",
            "groq_client",
            "GROQ_API_KEY",
        ]
        
        found = [p for p in banned_patterns if p in code]
        
        if not found:
            log_result("No Legacy Residue (stocks_writer.py)", "passed", f"All {len(banned_patterns)} banned patterns absent")
        else:
            log_result("No Legacy Residue (stocks_writer.py)", "failed", f"FOUND residues: {found}")
    except Exception as e:
        log_result("No Legacy Residue (stocks_writer.py)", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 7: Unified Waterfall Structure
# ==================================================================
def test_waterfall_structure():
    """Verifica que el waterfall unificado tiene la estructura correcta."""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()
        
        # Locate _call_unified_engine
        engine_start = code.find("def _call_unified_engine")
        if engine_start == -1:
            log_result("Waterfall Structure", "failed", "_call_unified_engine not found")
            return
        
        engine_end = code.find("\ndef ", engine_start + 10)
        engine_code = code[engine_start:engine_end if engine_end > 0 else len(code)]
        
        # Check all 3 TIERs are present
        checks = {
            "TIER 1 NVIDIA": "TIER 1" in engine_code and "NVIDIA" in engine_code,
            "TIER 2 GitHub": "TIER 2" in engine_code and "GitHub" in engine_code,
            "TIER 3 Gemini": "TIER 3" in engine_code and "Gemini" in engine_code,
            "meta/llama-3.1-70b": "meta/llama-3.1-70b-instruct" in engine_code,
            "gpt-4o": "gpt-4o" in engine_code,
            "gemini-2.0-flash": "gemini-2.0-flash" in engine_code,
            "GITHUB_MODELS_TOKEN": "GITHUB_MODELS_TOKEN" in engine_code,
            "NVIDIA_API_KEY": "NVIDIA_API_KEY" in engine_code,
        }
        
        failed = [k for k, v in checks.items() if not v]
        if not failed:
            log_result("Waterfall Structure", "passed", f"All {len(checks)} structure checks pass")
        else:
            log_result("Waterfall Structure", "failed", f"Missing: {failed}")

        # Check TIER order
        tier1_pos = engine_code.find("TIER 1")
        tier2_pos = engine_code.find("TIER 2")
        tier3_pos = engine_code.find("TIER 3")
        
        if tier1_pos < tier2_pos < tier3_pos:
            log_result("Waterfall Tier Order", "passed", "TIER 1 → TIER 2 → TIER 3 in correct order")
        else:
            log_result("Waterfall Tier Order", "failed", f"Positions: T1={tier1_pos}, T2={tier2_pos}, T3={tier3_pos}")

    except Exception as e:
        log_result("Waterfall Structure", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 8: Unified Engine Called for Both Languages
# ==================================================================
def test_unified_engine_both_langs():
    """Verifica que _call_unified_engine se usa para AMBOS idiomas."""
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()
        
        # Should find the unified call, not separate ES/EN engines
        unified_calls = code.count("_call_unified_engine")
        separate_es = "CEREBRO ESPAÑOL" in code
        separate_en = "CEREBRO INGLÉS" in code
        
        if unified_calls >= 2 and not separate_es and not separate_en:
            log_result("Unified Both Languages", "passed", f"_call_unified_engine used {unified_calls}x, no separate ES/EN blocks")
        elif separate_es or separate_en:
            log_result("Unified Both Languages", "failed", f"Still has separate ES/EN cerebro blocks")
        else:
            log_result("Unified Both Languages", "failed", f"_call_unified_engine only found {unified_calls}x (need >= 2)")
    except Exception as e:
        log_result("Unified Both Languages", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# TEST 9: SD3 Image Generation (Bonus)
# ==================================================================
def test_sd3_text_to_image():
    """Prueba la generación de imágenes con SD3 via NVIDIA API."""
    if not NVIDIA_KEY:
        log_result("SD3 Text-to-Image", "skipped", "No API key")
        return

    try:
        import requests
        headers = {
            "Authorization": f"Bearer {NVIDIA_KEY}",
            "Accept": "application/json",
        }
        payload = {
            "prompt": "A futuristic AI newsroom, photorealistic, 8k",
            "cfg_scale": 5,
            "steps": 30,
            "seed": 42
        }
        resp = requests.post(
            "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium",
            headers=headers, json=payload, timeout=60
        )
        if resp.status_code == 200:
            log_result("SD3 Text-to-Image", "passed", f"Image generated (HTTP 200)")
        elif resp.status_code == 402:
            log_result("SD3 Text-to-Image", "skipped", "Credits exhausted (HTTP 402)")
        else:
            log_result("SD3 Text-to-Image", "failed", f"HTTP {resp.status_code}")
    except Exception as e:
        log_result("SD3 Text-to-Image", "failed", f"{type(e).__name__}: {e}")


# ==================================================================
# MAIN
# ==================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 UNIFIED WATERFALL v3 — TEST SUITE")
    print("=" * 60)
    print(f"   Timestamp:           {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   NVIDIA_API_KEY:      {'✅' if NVIDIA_KEY else '❌'}")
    print(f"   GITHUB_MODELS_TOKEN: {'✅' if GH_TOKEN else '⏭️  (skipped)'}")
    print("=" * 60 + "\n")

    test_api_keys_present()
    test_nvidia_tier1()
    test_github_tier2()
    test_unified_engine_exists()
    test_no_zhipu_residue()
    test_no_zhipu_residue_stocks()
    test_waterfall_structure()
    test_unified_engine_both_langs()
    test_sd3_text_to_image()

    print("\n" + "=" * 60)
    print("📊 TEST REPORT")
    print("=" * 60)
    print(f"   ✅ Passed:  {results['passed']}")
    print(f"   ❌ Failed:  {results['failed']}")
    print(f"   ⏭️  Skipped: {results['skipped']}")
    print("=" * 60)

    report_path = os.path.join("data", "error_report_nvidia.json")
    os.makedirs("data", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "component": "unified_waterfall_v3",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "passed": results["passed"],
            "failed": results["failed"],
            "skipped": results["skipped"],
            "details": results["details"]
        }, f, indent=2, ensure_ascii=False)
    print(f"\n   📁 Report exported: {report_path}")

    if results["failed"] > 0:
        print("\n   🚨 SOME TESTS FAILED — Review the report above.\n")
        sys.exit(1)
    else:
        print("\n   🏆 ALL TESTS PASSED — Unified Waterfall v3 verified.\n")
        sys.exit(0)
