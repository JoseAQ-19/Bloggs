import argparse
import sys
import os
import sys

# Añadir directorio raíz al path para poder importar módulos core si es necesario
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.audit import run_audit
from core.cleaner import run_text_clean, run_image_clean
from core.generator import run_manual_generation

def main():
    parser = argparse.ArgumentParser(description="Novum World CLI Manager - The Ultimate Admin Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # COMANDO: AUDIT
    audit_parser = subparsers.add_parser("audit", help="Run SEO and Content Quality Audit")
    
    # COMANDO: CLEAN
    clean_parser = subparsers.add_parser("clean", help="Clean up content or images")
    clean_parser.add_argument("--text", action="store_true", help="Remove TL;DR and AI fluff")
    clean_parser.add_argument("--images", action="store_true", help="Fix broken/low-quality images")
    
    # COMANDO: GENERATE
    gen_parser = subparsers.add_parser("generate", help="Manually generate content")
    gen_parser.add_argument("--section", type=str, required=True, help="Target section (ia, crypto, fitness, etc)")
    gen_parser.add_argument("--lang", type=str, default="es", help="Language (es/en)")

    args = parser.parse_args()

    if args.command == "audit":
        run_audit()
    elif args.command == "clean":
        if args.text:
            run_text_clean()
        if args.images:
            run_image_clean()
        if not args.text and not args.images:
            print("⚠️ Specify what to clean: --text or --images")
    elif args.command == "generate":
        run_manual_generation(args.section, args.lang)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
