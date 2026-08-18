import os

WORKFLOW_DIR = os.path.abspath(".github/workflows")

workflows_config = [
    ("biohacking_es.yml", "Pipeline - Biohacking & Fitness (ES)", "48 4 * * *", "biohacking-es", "biohacking", "es"),
    ("biohacking_en.yml", "Pipeline - Biohacking & Fitness (EN)", "18 12 * * *", "biohacking-en", "biohacking", "en"),
    ("funds_es.yml", "Pipeline - Funds & Bolsa (ES)", "52 6 * * *", "funds-es", "funds", "es"),
    ("funds_en.yml", "Pipeline - Funds & Bolsa (EN)", "42 13 * * *", "funds-en", "funds", "en"),
    ("tools_es.yml", "Pipeline - Tools & Herramientas (ES)", "41 10 * * *", "tools-es", "tools", "es"),
    ("tools_en.yml", "Pipeline - Tools & Herramientas (EN)", "14 16 * * *", "tools-en", "tools", "en"),
    ("ia_saas_es.yml", "Pipeline - IA & SaaS (ES)", "27 12 * * *", "ia-saas-es", "ia-saas", "es"),
    ("ia_saas_en.yml", "Pipeline - IA & SaaS (EN)", "09 18 * * *", "ia-saas-en", "ia-saas", "en"),
    ("creators_es.yml", "Pipeline - Creators & YouTube (ES)", "19 13 * * *", "creators-es", "creators", "es"),
    ("creators_en.yml", "Pipeline - Creators & YouTube (EN)", "37 19 * * *", "creators-en", "creators", "en"),
    ("crypto_es.yml", "Pipeline - Crypto & Web3 (ES)", "36 15 * * *", "crypto-es", "crypto", "es"),
    ("crypto_en.yml", "Pipeline - Crypto & Web3 (EN)", "23 21 * * *", "crypto-en", "crypto", "en"),
    ("viral_es.yml", "Pipeline - Viral & Trends (ES)", "27 18 * * *", "viral-es", "viral", "es"),
    ("viral_en.yml", "Pipeline - Viral & Trends (EN)", "48 23 * * *", "viral-en", "viral", "en"),
]

def get_omniroute_steps():
    return """      # 1. Configuración de Node.js
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'

      # 2. Instalación Global Síncrona
      - name: Install OmniRoute CLI
        run: npm install -g omniroute

      # 3. Arranque en 2.º Plano con Polling Loop Saludable
      - name: Start OmniRoute Gateway (Background)
        env:
          PORT: 8000
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          omniroute --port 8000 &
          echo "Verificando disponibilidad de OmniRoute en http://localhost:8000/v1..."
          for i in {1..25}; do
            if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
              echo "OmniRoute está LISTO y respondiendo en el intento $i!"
              break
            fi
            echo "Intento $i/25: Esperando 2 segundos más..."
            sleep 2
          done
          curl --fail http://localhost:8000/v1/models || (echo "ERROR: OmniRoute no inició a tiempo" && exit 1)"""

def generate_workflow_yaml(name, cron_time, group_id, section, lang):
    omniroute_steps = get_omniroute_steps()
    return f"""name: "{name}"

on:
  schedule:
    - cron: '{cron_time}'  # ÚNICO cron maestro que dispara la cascada
  workflow_dispatch:      # Permite ejecución manual bajo demanda

permissions:
  contents: write

concurrency:
  group: {group_id}-${{{{ github.ref }}}}
  cancel-in-progress: false

env:
  OMNIROUTE_BASE_URL: "http://localhost:8000/v1"
  OMNIROUTE_API_KEY: "sk-omniroute"
  LLM_MODEL: "auto"
  GEMINI_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
  GOOGLE_API_KEY: ${{{{ secrets.GEMINI_API_KEY }}}}
  GROQ_API_KEY: ${{{{ secrets.GROQ_API_KEY }}}}
  OPENROUTER_API_KEY: ${{{{ secrets.OPEN_ROUTER_API_KEY || secrets.OPENROUTER_API_KEY || secrets.OPENROUTER_SCOUT_KEY }}}}
  OPEN_ROUTER_API_KEY: ${{{{ secrets.OPEN_ROUTER_API_KEY || secrets.OPENROUTER_API_KEY }}}}
  HUGGINGFACE_API_KEY: ${{{{ secrets.HUGGINGFACE_API_KEY || secrets.HF_SCOUT_API_KEY || secrets.CORRECTOR_HF_API_KEY }}}}
  EXA_API_KEY: ${{{{ secrets.EXA_API_KEY }}}}
  TOGETHER_API_KEY: ${{{{ secrets.TOGETHER_API_KEY }}}}
  NVIDIA_API_KEY: ${{{{ secrets.NVIDIA_API_KEY }}}}
  TOKEN_MODELS: ${{{{ secrets.TOKEN_MODELS }}}}
  MODELS_TOKEN_CEU: ${{{{ secrets.MODELS_TOKEN_CEU }}}}
  VERCEL_DEPLOY_HOOK_URL: ${{{{ secrets.VERCEL_DEPLOY_HOOK_URL }}}}
  GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}

jobs:
  # FASE 1: SCOUT (Busca tendencias en nichos ES/LATAM o EN/USA)
  scout:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{omniroute_steps}
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
          git pull --rebase --autostash origin main || git rebase --abort
          git push origin main || (sleep 5 && git pull --rebase --autostash origin main && git push origin main)

  # FASE 2: WRITER (Se activa AUTOMÁTICAMENTE al terminar el Scout)
  writer:
    needs: scout
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{omniroute_steps}
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
          git pull --rebase --autostash origin main || git rebase --abort
          git push origin main || (sleep 5 && git pull --rebase --autostash origin main && git push origin main)
      - name: Trigger Vercel Deploy Hook
        if: always()
        run: |
          if [ -n "$VERCEL_DEPLOY_HOOK_URL" ]; then
            echo "Disparando Vercel Deploy Hook..."
            curl -s -X POST "$VERCEL_DEPLOY_HOOK_URL" || true
          fi

  # FASE 3: CORRECTOR (Se activa AUTOMÁTICAMENTE al terminar el Writer)
  corrector:
    needs: writer
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{omniroute_steps}
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
          git commit -m "fix(corrector): auditoria post {section} {lang} [skip ci]" || exit 0
          git pull --rebase --autostash origin main || git rebase --abort
          git push origin main || (sleep 5 && git pull --rebase --autostash origin main && git push origin main)
"""

def main():
    print(f"Updating 14 workflows in {WORKFLOW_DIR}...")
    for filename, name, cron_time, group_id, section, lang in workflows_config:
        filepath = os.path.join(WORKFLOW_DIR, filename)
        content = generate_workflow_yaml(name, cron_time, group_id, section, lang)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"  [UPDATED] {filename}")

if __name__ == "__main__":
    main()
