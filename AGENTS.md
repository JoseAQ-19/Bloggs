# AGENTS.md

## Repository Overview

- NovumWorld is a bilingual Hugo publication with Python content and data pipelines.
- English content lives under `content/en/`; Spanish content lives under `content/es/`.
- Articles normally use Hugo leaf bundles: `content/{lang}/{category}/{slug}/index.md`.
- `main.py` is the general article-generation entry point.
- `stocks_main.py` is the specialized investment/funds entry point.
- Core reusable logic belongs in `core/`; executable utilities belong in `scripts/`.
- Tests are in `tests/` and use `pytest`.
- Hugo configuration is in `config.toml`; deployment configuration is in `vercel.json`.
- GitHub Actions workflows live in `.github/workflows/` and may generate content.

## Environment Setup

- Use Python 3.11, matching the GitHub Actions writer workflow.
- Create and activate a virtual environment before installing Python dependencies.
- Install dependencies with `python -m pip install -r requirements.txt`.
- Node dependencies are declared in `package.json`; install with `npm install` when needed.
- Hugo must be installed locally for site builds and validation.
- Do not commit `.env.local`, API keys, tokens, service-account JSON, or generated secrets.
- Copy `.env.example` to a local environment file and fill in credentials privately.
- Network-backed tests may require API credentials and may be slow or unavailable offline.

## Build, Lint, and Test Commands

- Install Python dependencies: `python -m pip install -r requirements.txt`.
- Install JavaScript dependencies: `npm install`.
- Build the site: `npm run build`.
- Equivalent direct Hugo build: `hugo --gc --minify`.
- Validate Hugo output locally: `hugo server -D`.
- Run the complete Python test suite: `python -m pytest`.
- Run tests with concise output: `python -m pytest -q`.
- Run one test module: `python -m pytest tests/test_visual.py`.
- Run one test function: `python -m pytest tests/test_visual.py::test_function_name`.
- Run one class method: `python -m pytest tests/test_file.py::TestClass::test_method`.
- Select tests by expression: `python -m pytest -k "router and retry"`.
- Stop at the first failure: `python -m pytest -x`.
- Show local output and logs: `python -m pytest -s tests/test_router.py`.
- Collect tests without running them: `python -m pytest --collect-only`.
- Run a script syntax check: `python -m py_compile path/to/file.py`.
- Compile all Python sources: `python -m compileall core scripts tests main.py stocks_main.py`.
- No dedicated repository lint script is currently defined in `package.json`.
- No formatter or type-checker configuration was found; preserve existing style manually.
- Before a PR, run the focused tests first, then `python -m pytest`, then `npm run build`.

## Running Application Pipelines

- General pipeline example: `python main.py --category crypto --lang es`.
- Use `--lang es` or `--lang en` to make language selection deterministic.
- Categories are validated against the registry in `core/niche_registry.py`.
- Do not run generation pipelines casually: they can call paid APIs, write content, and deploy.
- Prefer fixture-based or mocked tests for changes to API, LLM, research, or deployment code.
- Review generated Markdown, front matter, links, and images before publishing.

## Python Style

- Follow PEP 8 conventions and use four spaces for indentation.
- Keep files UTF-8, but use ASCII for new source text unless content requires otherwise.
- Use readable, descriptive `snake_case` names for functions, variables, and modules.
- Use `PascalCase` for classes and `UPPER_SNAKE_CASE` for module constants.
- Keep public functions small and focused on one pipeline responsibility.
- Add type annotations to new or modified public functions and meaningful data structures.
- Prefer built-in generics such as `list[str]` when compatible with the project Python version.
- Use docstrings for public functions with non-obvious behavior or side effects.
- Keep imports at the top, grouped as standard library, third-party, then local imports.
- Avoid duplicate imports and avoid modifying `sys.path` outside the established bootstrap pattern.
- Use `pathlib.Path` for new filesystem code where practical; preserve compatible existing APIs.
- Use context managers for files, subprocess resources, and other closable resources.
- Specify `encoding="utf-8"` for text file operations.
- Prefer f-strings for interpolation and avoid string concatenation for structured messages.
- Keep lines reasonably short, but do not reformat unrelated legacy code.
- Do not add comments that merely restate code; explain only non-obvious decisions.

## Types, Data, and Errors

- Validate external data at boundaries before passing it into core logic.
- Treat JSON, front matter, API responses, and environment variables as untrusted input.
- Check required keys and types before indexing dictionaries or iterating nested values.
- Use `Optional` or `None` explicitly where a value may be unavailable.
- Raise specific exceptions when callers can recover; do not use bare `except:`.
- Catch broad exceptions only at intentional pipeline boundaries, log context, and fail safely.
- Preserve the repository's fail-safe behavior for optional deploy and external-service operations.
- Never silently swallow errors; return a documented status or emit a useful warning.
- Include operation, path/category, and retry context in error messages.
- Avoid logging secrets, authorization headers, full tokens, or private article data.
- Use retries only for transient network/API failures and keep retry counts bounded.
- Make filesystem writes atomic or backup-aware when changing existing editorial data.

## Content and Hugo Conventions

- Preserve valid TOML/YAML front matter and existing field names when editing articles.
- Keep language-specific content in its matching language directory.
- Use lowercase, hyphen-separated slugs and avoid renaming published URLs without a reason.
- Preserve translation metadata and deterministic hreflang keys when editing bilingual posts.
- Keep images referenced by the article and store site assets under `static/images/` as established.
- Use Hugo templates and shortcodes consistently with the existing Ananke theme integration.
- Validate internal links, image paths, and rendered headings after content changes.
- Keep editorial claims sourced and retain source metadata expected by QA scripts.

## JavaScript, CSS, and Configuration

- JavaScript is limited; preserve the existing CommonJS/PostCSS setup.
- Use semicolons and two-space indentation in JavaScript/config snippets matching existing files.
- Keep PostCSS configuration compatible with the Vercel build command.
- Preserve the bilingual structure and menu identifiers in `config.toml`.
- Use quoted strings when TOML values contain punctuation or could be parsed ambiguously.
- Avoid changing deployment commands or Hugo version settings without testing a production-like build.

## GitHub Actions and Deployment

- Workflows use Ubuntu, Python 3.11, `pip install -r requirements.txt`, and `PYTHONPATH` for imports.
- Changes to workflows should preserve least-privilege permissions and existing secret names.
- Generated content workflows commit only intended content, data, and image paths when possible.
- The Vercel deploy hook is `VERCEL_DEPLOY_HOOK_URL`; never hard-code its value.
- Use `scripts/deploy_notifier.py` for the repository's guarded Git/Vercel deployment flow.
- Confirm tests/builds and inspect `git diff` before committing or pushing.
- Pull/rebase before pushing when concurrent GitHub Actions may have updated `main`.

## Repository-Specific Instructions

- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files were found.
- `README.md`, `GEMINI.md`, `.agents/`, and `.agent/` contain additional project/editorial context.
- Follow the most specific instruction file for the directory being changed if one is added later.
- Keep changes focused and avoid committing caches such as `.pytest_cache/` or `__pycache__/`.
