import os
import sys

if sys.platform == "win32" and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKFLOWS_CONFIG = [
    # 1. Biohacking
    {
        "file": "biohacking_es.yml",
        "name": "Pipeline - Biohacking & Fitness (ES)",
        "cron": "48 4 * * *",
        "group": "biohacking-es",
        "section": "biohacking",
        "lang": "es"
    },
    {
        "file": "biohacking_en.yml",
        "name": "Pipeline - Biohacking & Fitness (EN)",
        "cron": "18 12 * * *",
        "group": "biohacking-en",
        "section": "biohacking",
        "lang": "en"
    },
    # 2. Funds
    {
        "file": "funds_es.yml",
        "name": "Pipeline - Funds & Bolsa (ES)",
        "cron": "52 6 * * *",
        "group": "funds-es",
        "section": "funds",
        "lang": "es"
    },
    {
        "file": "funds_en.yml",
        "name": "Pipeline - Funds & Bolsa (EN)",
        "cron": "42 13 * * *",
        "group": "funds-en",
        "section": "funds",
        "lang": "en"
    },
    # 3. Tools
    {
        "file": "tools_es.yml",
        "name": "Pipeline - Tools & Herramientas (ES)",
        "cron": "41 10 * * *",
        "group": "tools-es",
        "section": "tools",
        "lang": "es"
    },
    {
        "file": "tools_en.yml",
        "name": "Pipeline - Tools & Herramientas (EN)",
        "cron": "14 16 * * *",
        "group": "tools-en",
        "section": "tools",
        "lang": "en"
    },
    # 4. IA & SaaS
    {
        "file": "ia_saas_es.yml",
        "name": "Pipeline - IA & SaaS (ES)",
        "cron": "27 12 * * *",
        "group": "ia-saas-es",
        "section": "ia-saas",
        "lang": "es"
    },
    {
        "file": "ia_saas_en.yml",
        "name": "Pipeline - IA & SaaS (EN)",
        "cron": "09 18 * * *",
        "group": "ia-saas-en",
        "section": "ia-saas",
        "lang": "en"
    },
    # 5. Creators / YouTube
    {
        "file": "creators_es.yml",
        "name": "Pipeline - Creators & YouTube (ES)",
        "cron": "19 13 * * *",
        "group": "creators-es",
        "section": "creators",
        "lang": "es"
    },
    {
        "file": "creators_en.yml",
        "name": "Pipeline - Creators & YouTube (EN)",
        "cron": "37 19 * * *",
        "group": "creators-en",
        "section": "creators",
        "lang": "en"
    },
    # 6. Crypto
    {
        "file": "crypto_es.yml",
        "name": "Pipeline - Crypto & Criptomonedas (ES)",
        "cron": "36 15 * * *",
        "group": "crypto-es",
        "section": "crypto",
        "lang": "es"
    },
    {
        "file": "crypto_en.yml",
        "name": "Pipeline - Crypto & Criptomonedas (EN)",
        "cron": "23 21 * * *",
        "group": "crypto-en",
        "section": "crypto",
        "lang": "en"
    },
    # 7. Viral
    {
        "file": "viral_es.yml",
        "name": "Pipeline - Viral & Tendencias (ES)",
        "cron": "27 18 * * *",
        "group": "viral-es",
        "section": "viral",
        "lang": "es"
    },
    {
        "file": "viral_en.yml",
        "name": "Pipeline - Viral & Tendencias (EN)",
        "cron": "48 23 * * *",
        "group": "viral-en",
        "section": "viral",
        "lang": "en"
    }
]

TEMPLATE = """name: "{name}"

on:
  schedule:
    - cron: '{cron}'  # ÚNICO cron maestro que dispara la cascada
  workflow_dispatch:      # Permite ejecución manual bajo demanda

concurrency:
  group: {group}-${{{{ github.ref }}}}
  cancel-in-progress: false

jobs:
  # FASE 1: SCOUT (Busca tendencias en nichos ES/LATAM o EN/USA)
  scout:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: pip install -r requirements.txt
      - name: Run Scout
        run: python scripts/trend_scout.py --section {section} --lang {lang}
      - name: Commit Scout Research
        run: |
          git config user.name "NovumBot"
          git config user.email "bot@novumworld.com"
          git add .
          git commit -m "docs(scout): tendencias {section} {lang} [skip ci]" || exit 0
          git pull --rebase --autostash origin main
          git push origin main

  # FASE 2: WRITER (Se activa AUTOMÁTICAMENTE al terminar el Scout)
  writer:
    needs: scout
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: pip install -r requirements.txt
      - name: Run Writer
        run: python main.py --section {section} --lang {lang}
      - name: Commit New Article & Images
        run: |
          git config user.name "NovumBot"
          git config user.email "bot@novumworld.com"
          git add .
          git commit -m "feat(writer): nuevo post {section} {lang} [skip ci]" || exit 0
          git pull --rebase --autostash origin main
          git push origin main

  # FASE 3: CORRECTOR (Se activa AUTOMÁTICAMENTE al terminar el Writer)
  corrector:
    needs: writer
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Dependencies
        run: pip install -r requirements.txt
      - name: Run Corrector Audit
        run: python audit_v2.py --section {section} --lang {lang}
      - name: Commit Audited Changes
        run: |
          git config user.name "NovumBot"
          git config user.email "bot@novumworld.com"
          git add .
          git commit -m "fix(corrector): auditoría post {section} {lang} [skip ci]" || exit 0
          git pull --rebase --autostash origin main
          git push origin main
"""

def generate():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.github', 'workflows')
    os.makedirs(target_dir, exist_ok=True)
    
    generated_files = []
    for cfg in WORKFLOWS_CONFIG:
        content = TEMPLATE.format(**cfg)
        file_path = os.path.join(target_dir, cfg['file'])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        generated_files.append(cfg['file'])
        print(f"✅ Generado: .github/workflows/{cfg['file']}")

    print(f"\n🎉 Total generado: {len(generated_files)} workflows.")

if __name__ == '__main__':
    generate()
