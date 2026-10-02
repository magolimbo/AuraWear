# CLAUDE.md

Prototype of a customer feedback workbench on GCP: synthetic data → Cloud
Storage → BigQuery → Gemini enrichment → Streamlit app.

## Read first
- `SPEC.md` (shared contracts), then the `SPEC.md` of the component you are working on.
- Build only what the specs describe. If something is unclear or missing, ask; do not invent requirements.
- When the prototype is decided to do something more simply than a production system for the case would, add a row to `docs/full_design.md`.

## Environment
- Windows, PowerShell. Python 3.11+ in a virtual environment at `.venv`.
- Activate: `.venv\Scripts\Activate.ps1` · Install: `pip install -r requirements.txt`
- GCP auth: Application Default Credentials (already configured). Never create or use key files.

## Commands
- Tests: `pytest`
- Lint: `ruff check .`
- Run a component: `python -m <folder>.<module>` (e.g. `python -m data_gen.generate`)

## Project structure
- One folder per component: `data_gen/`, `ingestion/`, `sql/`, `enrichment/`, `app/`.
- Tests in `tests/<component>/`.
- Project id, bucket, dataset names and region live only in `config.py`. Import them; never hard-code them elsewhere.

## Code rules
- Simple, readable code; no abstractions or features the spec does not ask for.
- Type hints on public functions; short docstrings.
- SQL that includes user input uses query parameters, never string formatting.
- No emoji in code, comments, logs or output.
- Code, comments and messages in English.

## Verification
- Only `enrichment/` has `pytest` tests. They never call real GCP services or Gemini: mock them. Write them before the implementation.
- Other components: run them and check the "Verified by" section of their `SPEC.md`.
- A task is done only when its verification passes and `ruff check .` reports no errors. Report what you ran and the result in your final message.

## Git
- Do not commit or push. I review the diff and commit myself.

## Boundaries
- **Always:** verify the task as described above before saying it is done; keep changes inside the component you were asked to work on.
- **Ask first:** changing any table, column or contract in `SPEC.md`; adding a dependency; creating GCP resources.
- **Never:** commit or push; delete GCP resources or data; commit secrets or `.env` files.