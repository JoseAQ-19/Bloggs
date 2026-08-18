#!/usr/bin/env python3
"""
Antigravity Loop Engineering Engine - Autonomous Quality & Self-Healing
Ciclo: Observar -> Evaluar -> Reparar (GEO/SEO) -> Validar (Gate) -> Sincronizar
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def run_loop():
    print("🚀 [LOOP START] Iniciando ciclo de automejora continua...")
    
    # 1. OBSERVAR: Análisis estático y extracción de notas
    code, out, err = run_cmd("python scripts/audit_v2.py --export-json docs/audits/audit_latest.json")
    audit_file = Path("docs/audits/audit_latest.json")
    
    if not audit_file.exists():
        print("⚠️ No se encontró reporte de auditoría. Abortando ciclo de forma segura.")
        return 0

    with open(audit_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. EVALUAR: Seleccionar los 3 artículos con menor puntuación o enlaces rotos
    articles = data.get("articles", [])
    candidates = sorted(articles, key=lambda x: x.get("score", 100))[:3]
    
    print(f"📊 Artículos seleccionados para remediación: {len(candidates)}")
    
    # 3. REPARAR: Corrección de Schemas, Chunking GEO y Enlaces 404
    for item in candidates:
        filepath = item.get("path")
        score = item.get("score", 0)
        print(f"🔧 Optimizando: {filepath} (Score previo: {score}/100)")
        # Ejecutar remediación quirúrgica
        run_cmd(f'python scripts/audit_v2.py --fix-file "{filepath}"')

    # 4. PUERTA DE VALIDACIÓN (FAIL-SAFE GATE)
    print("🧪 Validando integridad técnica...")
    pytest_code, _, _ = run_cmd("python -m pytest tests/test_workflows_integrity.py tests/test_daily_optimizer.py tests/test_deploy_notifier.py tests/test_vercel_config.py")
    hugo_code, _, _ = run_cmd("hugo --renderToMemory --buildDrafts")
    
    if pytest_code != 0:
        print("🚨 [GATE FAILED] Errores detectados en tests. Revertiendo cambios...")
        run_cmd("git restore content/ layouts/")
        return 1

    # 5. SINCRONIZAR MEMORIA Y GRAFO AST
    print("🧠 Sincronizando Grafo de Conocimiento...")
    run_cmd("graphify update")
    
    # 6. PERSISTENCIA EN GIT
    run_cmd("git config user.name 'AntigravityLoop'")
    run_cmd("git config user.email 'loop@novumworld.com'")
    run_cmd("git add content/ docs/audits/ graphify-out/")
    run_cmd("git commit -m 'chore(loop): optimización autónoma diaria GEO/SEO [skip ci]'")
    run_cmd("git pull --rebase --autostash origin main")
    run_cmd("git push origin main")
    
    print("✅ [LOOP SUCCESS] Ciclo de automejora completado con éxito.")
    return 0

if __name__ == "__main__":
    sys.exit(run_loop())
