# AGENTS.md

## Repository Overview

- NovumWorld is a bilingual Hugo publication backed by Python research and content pipelines.
- English content is under `content/en/`; Spanish content is under `content/es/`.
- Categories: `ia`, `crypto`, `fitness`, `tools`, `youtube`, `viral`, and `funds`.
- `main.py` runs the Scout -> Research -> Writer -> Save pipeline.
- `stocks_main.py` runs the independent investment-funds Scout -> Writer pipeline.
- Reusable Python logic belongs in `core/`; command-line utilities belong in `scripts/`.
- Tests are in `tests/` using pytest; `tests/conftest.py` adds `core/` and `scripts/` to `sys.path`.
- Hugo templates are under `layouts/`; browser assets are under `static/`.
- Hugo configuration is in `config.toml`; Vercel configuration is in `vercel.json`.
- GitHub Actions workflows under `.github/workflows/` can generate or modify published content.

## Instruction Files and Scope

- This file applies to the whole repository unless a more specific `AGENTS.md` exists below a directory.
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files are present.
- `GEMINI.md` contains additional audit and security expectations; follow it for security reviews.
- `.agent/workflows/deploy.md` documents the manual Vercel deploy-hook workflow.
- `.agents/` contains editorial context, not executable application code.
- Prefer the most specific applicable instruction file when guidance changes.

## Environment Setup

- Use Python 3.11, matching GitHub Actions and the documented runtime.
- Create a virtual environment before installing Python dependencies.
  - Windows PowerShell: `py -3.11 -m venv .venv` then `\.venv\Scripts\Activate.ps1`.
  - macOS/Linux: `python3.11 -m venv .venv` then `source .venv/bin/activate`.
- Install Python dependencies: `python -m pip install -r requirements.txt`.
- Install Node dependencies with `npm install` when changing or building the frontend pipeline.
- Hugo is required locally for site builds; Vercel uses Hugo `0.146.0`.
- Credentials are read from environment variables through `python-dotenv`.
- Common variables: `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `NVIDIA_API_KEY`, OpenRouter/GitHub Models tokens, and `VERCEL_DEPLOY_HOOK_URL`.
- Never print, commit, or paste credentials, `.env` files, service-account JSON, or private deploy-hook URLs.
- `.env*`, `.vercel/`, `public/`, `resources/`, caches, and Python bytecode are ignored or generated; verify before adding files.

## Build, Lint, and Test Commands

- Install dependencies: `python -m pip install -r requirements.txt` and `npm install`.
- Build the production site: `npm run build` (equivalent to `hugo --gc --minify`).
- Run a local draft-capable server: `hugo server -D`.
- Run the complete pytest suite: `python -m pytest`.
- Run with concise output: `python -m pytest -q`.
- Run one test module: `python -m pytest tests/test_visual.py`.
- Run one test function: `python -m pytest tests/test_visual.py::test_visual_logger`.
- Run one class method: `python -m pytest tests/test_visual.py::TestSeedDerivation::test_same_slug_same_seed`.
- Select tests by keyword: `python -m pytest -k "router and retry"`.
- Stop after the first failure: `python -m pytest -x`.
- Show print statements and logs: `python -m pytest -s tests/test_router.py`.
- Collect tests without executing: `python -m pytest --collect-only`.
- Compile a changed Python file: `python -m py_compile path/to/file.py`.
- Compile project Python sources: `python -m compileall core scripts tests main.py stocks_main.py`.
- Validate YAML/front matter: `python scripts/validate_yaml_strict.py`.
- Validate one article structure: `python scripts/validate_structure.py --file path/to/article.md`.
  - `validate_structure.py` deletes the target article when validation fails; use it deliberately.
- Validate article links: `python scripts/qa_link_validator.py path/to/article.md`.
- There is no configured Python linter, formatter, type checker, or JavaScript lint script.
- Do not invent a lint command; use focused pytest, compilation, and Hugo validation instead.
- Before a substantial change, run the focused test, then `python -m pytest`, then `npm run build`.

## Test Expectations

- Prefer deterministic unit tests with mocks, `tmp_path`, and `monkeypatch` for API, filesystem, and deployment behavior.
- Keep tests isolated; temporary content must be created under pytest `tmp_path` and cleaned up when needed.
- Tests in `test_data_finance.py`, `test_data_pubmed.py`, and `test_data_youtube.py` use live external services and may be slow or unavailable offline.
- `test_nvidia_integration.py` is a credential-aware integration suite and can call paid or rate-limited APIs.
- Mock LLM clients and HTTP responses rather than making network calls in ordinary unit tests.
- Run network-backed tests intentionally and report credential, rate-limit, or connectivity failures separately from code failures.
- Test filenames use `test_*.py`; test functions and methods use `test_` names; test classes use `Test...`.
- Preserve standalone `if __name__ == "__main__"` test entry points when modifying tests that provide them.

## Running Application Pipelines

- General pipeline: `python main.py --category crypto --lang es`.
- Use `--lang es` or `--lang en` to make language selection deterministic.
- Scout example: `python scripts/trend_scout.py --section crypto --lang es`.
- Funds pipeline: `python stocks_main.py --lang en`; omit `--lang` to process both languages.
- Categories and aliases are validated through `core/niche_registry.py` and `main.py`.
- Do not run generation pipelines casually: they can call paid APIs, write content, commit, push, or deploy.
- Prefer fixture-based or mocked tests for changes to API, LLM, research, or deployment code.
- Review generated Markdown, front matter, links, images, and data files before publishing.

## Python Style

- Follow PEP 8 with four spaces per indentation level and no tabs.
- Keep source files UTF-8; prefer ASCII for new code unless content or user-facing language requires otherwise.
- Keep imports at the top, grouped as standard library, third-party, then local imports.
- Remove duplicate and unused imports when touching a file, but avoid unrelated cleanup.
- Avoid runtime `sys.path` changes in new code; preserve the existing bootstrap pattern where compatibility requires it.
- Use descriptive `snake_case` for functions, variables, files, and module-level helpers.
- Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants.
- Use type annotations on new or modified public functions and meaningful data structures.
- Prefer built-in generics such as `list[str]` and `dict[str, Any]` when compatible with Python 3.11.
- Use `Optional` or `None` explicitly for values that may be absent; do not hide nullable behavior.
- Keep public functions focused on one pipeline responsibility and avoid needless global state.
- Add docstrings to public functions with non-obvious behavior, side effects, or external I/O.
- Prefer f-strings for interpolation and avoid concatenation for structured messages.
- Use `pathlib.Path` for new filesystem code where practical; preserve compatible string paths in legacy APIs.
- Open text files with explicit `encoding="utf-8"`; use context managers for files and subprocess resources.
- Keep lines reasonably short and preserve local formatting when a file is inconsistent.
- Do not reformat an entire legacy file for a small behavioral change.
- Add comments only for non-obvious decisions; do not restate the code.

## Data, APIs, and Error Handling

- Treat JSON, YAML/front matter, HTTP responses, API payloads, and environment variables as untrusted input.
- Validate required keys and types at integration boundaries before indexing or iterating nested data.
- Raise specific exceptions when callers can recover; never use a bare `except:`.
- Catch broad exceptions only at intentional pipeline or external-service boundaries, log context, and fail safely.
- Never silently swallow errors; return a documented status or emit a useful warning.
- Include the operation, category/path, provider, and retry context in error messages where relevant.
- Do not log authorization headers, full tokens, private article data, or complete secret-bearing URLs.
- Use bounded retries and backoff only for transient network, rate-limit, or service failures.
- Preserve the fail-safe behavior of optional indexing, deployment, visual generation, and external research layers.
- Use mocks for retry and fallback tests; assert both the successful result and the fallback path when practical.
- Prefer atomic or backup-aware writes for existing editorial data and avoid deleting content unless the utility explicitly requires it.

## Content and Hugo Conventions

- Preserve valid YAML front matter and existing field names when editing Markdown.
- Generated posts commonly use leaf bundles such as `content/{lang}/{category}/{slug}/index.md`; legacy flat Markdown files also exist.
- Keep each article in the matching language directory and use lowercase, hyphen-separated slugs.
- Preserve `translationKey`, language metadata, author/category metadata, and deterministic bilingual linking.
- Do not fabricate external or internal URLs; use only verified URLs supplied by the research/link pipeline.
- Keep source metadata, disclaimers, FAQ data, tables, and other QA-required editorial structures intact.
- Store bundle images beside their article when that pattern is already used; preserve established `static/` asset paths.
- Use Hugo templates and Ananke conventions consistently; do not rename partials or menu identifiers casually.
- Validate front matter, internal links, image references, headings, and rendered output after content changes.
- Keep English content under `content/en/` and Spanish content under `content/es/`; do not mix language output.

## JavaScript, CSS, and Configuration

- JavaScript is limited; preserve the CommonJS/PostCSS setup in `postcss.config.js`.
- Use semicolons and the existing four-space indentation in JavaScript and JSON configuration files.
- Keep `package.json` scripts and Vercel's Hugo build command compatible with production.
- Preserve Hugo `baseURL`, language configuration, menu identifiers, and Ananke custom CSS settings.
- Quote TOML values containing punctuation or values that could be parsed ambiguously.
- Avoid changing Hugo versions, theme branches, build commands, or deployment settings without a production-like build.

## Workflows and Deployment

- Workflows run on Ubuntu with Python 3.11 and install from `requirements.txt`.
- Preserve workflow permissions, concurrency controls, secret names, and the Scout -> Writer -> Corrector sequencing.
- Workflow jobs may commit generated content and images; review their exact `git add` scope before changing it.
- For manual code deployment, follow `.agent/workflows/deploy.md`; do not trigger a second deploy for GitHub Actions content commits.
- Use `scripts/deploy_notifier.py` only when the guarded Git/Vercel behavior is intended.
- Never hard-code `VERCEL_DEPLOY_HOOK_URL` or any API key.

## Change Hygiene

- Inspect `git status --short` and `git diff` before editing; preserve unrelated user changes.
- Keep changes focused and avoid committing `__pycache__/`, `.pytest_cache/`, generated site output, logs, or local scratch files.
- Review generated Markdown, front matter, links, images, and `git diff` before committing or pushing.
- Do not commit unless explicitly requested by the user.
