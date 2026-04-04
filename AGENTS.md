AGENT OPERATIONS GUIDE FOR THIS REPO
====================================

This file documents how agentic coding assistants should work in this repository.
It covers build/lint/test commands, Python and JavaScript style, import and error
handling patterns, and how to respect the existing GSD/OpenCode tooling.

This repo powers a Hugo blog ("mi-blog") plus a large Python automation and
content pipeline ("NovumWorld" scripts). There is no global monolithic test
runner or formatter; agents must use the lightweight commands and patterns
described here.

1. BUILD / LINT / TEST COMMANDS
--------------------------------

- Python environment
  - Primary runtime: `python` / `python3` (repo assumes a global interpreter).
  - Dependencies: install once via:
    - `pip install -r requirements.txt`
  - Key testing dependency: `pytest` (see `requirements.txt`).

  - Run entire pytest suite:
    - `pytest`
  - Run a single test file (most useful here):
    - `pytest scripts/test_api_retry.py`
    - `pytest scripts/test_visual.py`
  - Run a single test function:
    - `pytest scripts/test_api_retry.py::test_api_retry_success_after_failure`
  - Some tests also use `unittest.main()`; you can run those via pytest or
    directly with Python:
    - `pytest scripts/test_json_cache.py`
    - `python scripts/test_json_cache.py`

- Hugo build (site generation)
  - Hugo is used for the blog; the JS toolchain is only for CSS processing.
  - To build the site for local verification (if Hugo is installed):
    - `hugo`
  - To run the development server:
    - `hugo server -D`

- CSS / PostCSS pipeline
  - Node tooling is scoped to PostCSS/autoprefixer. From repo root:
    - Install Node deps once:
      - `npm install`
    - Process CSS (if a script exists or manual call is needed):
      - `npx postcss static/css/custom.css -o static/css/custom.bundled.css`
  - `.opencode/package.json` is for the OpenCode/GSD integration only; do not
    modify it unless you are explicitly working on GSD hooks.

- GitHub Actions / CI
  - There are many workflows under `.github/workflows/*.yml` which orchestrate
    writer/scout/corrector jobs. Do **not** assume they run full tests.
  - If you change Python used in Actions, ensure `pytest scripts/test_api_retry.py`
    still passes locally; this is the canonical regression test called out in
    `PRD.md`.

2. PYTHON CODE STYLE
---------------------

This repo is heavily Python-centric. There is no `pyproject.toml`, `.flake8`,
or `.ruff.toml`; style must be inferred from examples.

- General formatting
  - Indentation: 4 spaces, no tabs.
  - Line length: keep under ~100–120 characters when reasonable.
  - Quotes: double quotes for user-facing strings and messages, single quotes
    are also present; match nearby code instead of enforcing a new rule.
  - Encoding: use `encoding="utf-8"` for file IO when reading/writing text.
  - Docstrings: used sparingly, in triple double quotes (`"""..."""`).

- Imports
  - Standard library imports first, then third-party libs, then local modules.
  - Example from `main.py`:
    - `import os`
    - `import sys`
    - `import json`
    - `import random`
    - `import argparse`
    - `import logging`
    - Then project imports: `import researcher`, `import trend_hunter`,
      `from niche_registry import NICHES`.
  - Do **not** add wildcard imports (`from x import *`). Use explicit names.
  - Keep imports at the top of the file unless a lazy import is clearly needed
    (match patterns like the `hashlib` re-import in `main.py`).

- Naming conventions
  - Modules and scripts: snake_case (`orchestrator.py`, `text_cleaner.py`).
  - Classes: PascalCase (`SlugManager`, `ImageManager`, `ContentCleaner`).
  - Functions and methods: snake_case (`planificar_articulo`, `safety_check`).
  - Constants: UPPER_SNAKE_CASE (`COMPLETED_FILE`, `STOPWORDS`).
  - Private helpers: leading underscore for internal functions (`_get_internal_links`).
  - Test functions: `test_*` for pytest and unittest test cases.

- Types and typing
  - Type hints are mostly absent in current code; do **not** introduce heavy
    typing in existing modules unless required by a task.
  - If you create new modules, you may use `typing` hints, but keep them simple
    and Pythonic (no complex `TypedDict`/`Protocol` unless already present).

- Error handling
  - Use `try/except` blocks around IO and external API calls; log a concise
    warning and fall back where possible instead of crashing.
  - Example from `orchestrator.safety_check`:
    - Wraps LLM calls in `try/except` and logs a warning, defaulting to SAFE.
  - For small utilities (e.g. `ImageManager.download_image`), broad `except`
    returning a safe default (`""`) is acceptable and already used.
  - In CLI entry points, prefer printing a clear message and exiting with
    `sys.exit(0 or 1)` instead of raising raw exceptions.

- Logging
  - Use the standard library `logging` module for reusable modules
    (`logging.warning`, `logging.debug`, etc.).
  - Top-level scripts may also use `print` for user-facing progress messages
    (see `main.py` and `orchestrator.py`). Do not remove these UX prints.

- Tests
  - Pytest style: plain `assert` statements with descriptive conditions.
  - Some tests subclass `unittest.TestCase` when more structure is needed.
  - When adding tests, follow the existing naming and structure in
    `scripts/test_api_retry.py` and `scripts/test_visual.py`.

3. JAVASCRIPT / NODE STYLE
---------------------------

JavaScript here is limited to small Node utilities under `.opencode/hooks` and
PostCSS config. These are CommonJS modules.

- Runtime and modules
  - Use Node CommonJS (`require`, `module.exports`) rather than ESM.
  - Shebang lines (`#!/usr/bin/env node`) are present on CLI scripts; keep them
    if you add new hooks.

- Formatting
  - 2-space indentation in existing JS files; match that.
  - Prefer `const` for values that never change, `let` otherwise; avoid `var`.
  - Semicolons are present; continue to use them consistently.
  - Use single quotes for strings where convenient; match nearby code.

- Imports and structure
  - Group Node built-ins (`fs`, `path`, `os`) at the top.
  - Avoid deep nested callbacks where possible; simple synchronous file IO is
    acceptable in hooks.

- Error handling
  - Hooks like `gsd-statusline.js` and `gsd-context-monitor.js` intentionally
    swallow errors to avoid breaking the developer experience; respect this
    pattern (wrap non-critical operations in `try/catch` and fail silently).

4. TESTING PATTERNS AND SINGLE-TEST RUNS
-----------------------------------------

Agents should default to running focused tests instead of the entire suite.

- Primary regression tests
  - API retry behavior (critical for LLM router resilience):
    - `pytest scripts/test_api_retry.py::test_api_retry_success_after_failure`
  - Visual pipeline behavior (image prompt and logging):
    - `pytest scripts/test_visual.py`

- When to run which tests
  - Changes in `llm_router.py`, `orchestrator.py`, or retry/backoff logic:
    - Run `pytest scripts/test_api_retry.py`.
  - Changes in visual context or image prompt logic:
    - Run `pytest scripts/test_visual.py`.
  - Changes in JSON caching, purge tools, or similar scripts:
    - Run `pytest scripts/test_json_cache.py` or the corresponding file.

5. ERROR HANDLING, RETRIES, AND LLM CALLS
-----------------------------------------

The orchestration layer is designed around resilient LLM calls.

- Router patterns
  - Use `LLMRouter.route_call(...)` for high-level calls when possible.
  - For lower-level OpenAI/NVIDIA clients, follow the patterns in
    `orchestrator._call_en_engine_v3_core` and `_call_es_engine_v3_core`:
    - Tiered fallbacks across providers.
    - Explicit retry loops with backoff on rate-limit errors (`429`).

- Backoff behavior
  - When adding or adjusting retries, keep the semantics validated by
    `test_api_retry_success_after_failure`: a transient 429 must not cause a
    permanent failure if a subsequent call succeeds.
  - Avoid unbounded retries; use a small fixed retry count with increasing
    sleep times.

- Safety and content checks
  - Use `orchestrator.safety_check(topic)` to validate topics instead of
    duplicating logic.
  - Respect `is_topic_redundant` when creating new topic selection flows.

6. FILE IO, PATHS, AND ENCODING
--------------------------------

- Always open text files with `encoding="utf-8"`.
- For paths, prefer `os.path.join` (Python) and `path.join` (Node) rather than
  string concatenation.
- When scanning content files for titles/slugs, follow the regex patterns and
  partial reads used in `LinkManager.get_latest_internal_links`.

7. GSD / OPENCODE INTEGRATION EXPECTATIONS
------------------------------------------

This repo is instrumented for the OpenCode "Get Shit Done" (GSD) workflows.

- Do not remove or bypass the `.opencode` folder, hooks, or `@opencode-ai/plugin`.
- Hooks intentionally:
  - Show a statusline with model/task/context usage.
  - Monitor context and inject warnings into the agent stream.
  - Check for GSD package updates in the background.
- If you extend these hooks, match current patterns:
  - Silent failure on errors (never block primary commands).
  - Write small JSON bridge files under system temp or `~/.opencode`.

8. GENERAL AGENT BEHAVIOR IN THIS REPO
---------------------------------------

- Never reset or discard user-modified content without explicit instruction.
- Prefer small, surgical changes over large refactors.
- When adding new scripts:
  - Place them under `scripts/` with snake_case filenames.
  - Include a `__main__` guard (`if __name__ == "__main__":`) for CLI use.
  - Add a focused test file when behavior is non-trivial.
- When modifying article generation or linking logic, preserve:
  - E-E-A-T link rules in `orchestrator.EEAT_LINK_RULES`.
  - Spiderweb internal linking behavior.
  - Language and SEO constraints around titles and slugs.

If you are uncertain about a convention, scan nearby files (especially
`orchestrator.py`, `main.py`, and `scripts/utils.py`) and match the dominant
pattern rather than introducing a new style.
