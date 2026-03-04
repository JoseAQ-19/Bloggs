"""
qa_orchestrator.py — Orquestador de Editores Jefe QA (ES + EN).

Punto de entrada CLI que ejecuta los editores especializados por idioma.

Uso:
    python qa_orchestrator.py --lang es --category ia
    python qa_orchestrator.py --lang en --category crypto
    python qa_orchestrator.py --lang all --category ia  # Ejecuta ambos
"""

import argparse
import json
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="QA Editor Orchestrator — Editores Jefe ES/EN"
    )
    parser.add_argument(
        "--lang",
        type=str,
        required=True,
        choices=["es", "en", "all"],
        help="Idioma del editor: es, en, o all (ambos)"
    )
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="Categoría del nicho: ia, crypto, fitness, youtube, viral, tools, funds"
    )
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"🎯 QA EDITOR ORCHESTRATOR — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Idioma: {args.lang.upper()} | Categoría: {args.category.upper()}")
    print(f"{'='*70}")

    results = {}

    # === EDITOR ESPAÑOL ===
    if args.lang in ("es", "all"):
        print(f"\n{'─'*70}")
        print(f"🇪🇸 EJECUTANDO EDITOR JEFE — ESPAÑOL")
        print(f"{'─'*70}")
        try:
            from qa_editor_es import run as run_editor_es
            result_es = run_editor_es(args.category)
            results["es"] = result_es
        except Exception as e:
            print(f"   ❌ [Editor ES] Error fatal: {e}")
            results["es"] = {"status": "error", "reason": str(e)}

    # === EDITOR INGLÉS ===
    if args.lang in ("en", "all"):
        print(f"\n{'─'*70}")
        print(f"🇬🇧 EJECUTANDO EDITOR JEFE — ENGLISH")
        print(f"{'─'*70}")
        try:
            from qa_editor_en import run as run_editor_en
            result_en = run_editor_en(args.category)
            results["en"] = result_en
        except Exception as e:
            print(f"   ❌ [Editor EN] Fatal error: {e}")
            results["en"] = {"status": "error", "reason": str(e)}

    # === RESUMEN FINAL ===
    print(f"\n{'='*70}")
    print(f"📋 RESUMEN QA EDITOR")
    print(f"{'='*70}")

    all_success = True
    for lang, result in results.items():
        if result is None:
            print(f"   [{lang.upper()}] ⚠️ Sin archivos para editar")
            all_success = False
        elif result.get("status") == "success":
            print(f"   [{lang.upper()}] ✅ Editado exitosamente")
            print(f"         📊 Palabras: {result.get('original_words', '?')} → {result.get('edited_words', '?')}")
            print(f"         🔗 Enlaces muertos reparados: {result.get('dead_links_fixed', 0)}")
            print(f"         🔍 Fact-check: {'✅ Ejecutado' if result.get('factcheck_ran') else '⏭️ Saltado'}")
            if result.get("issues"):
                print(f"         ⚠️ Warnings: {', '.join(result['issues'])}")
        elif result.get("status") == "skipped":
            print(f"   [{lang.upper()}] ⏭️ Saltado: {result.get('reason', 'desconocido')}")
        elif result.get("status") == "rejected":
            print(f"   [{lang.upper()}] ❌ Rechazado: {result.get('reason', 'desconocido')}")
            all_success = False
        else:
            print(f"   [{lang.upper()}] ❌ Error: {result.get('reason', 'desconocido')}")
            all_success = False

    print(f"\n{'='*70}")

    if all_success:
        print("✅ QA Editor completado. Los .md están listos para git commit.")
    else:
        print("⚠️ QA Editor completado con warnings. Los borradores originales se preservaron donde fue necesario.")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
