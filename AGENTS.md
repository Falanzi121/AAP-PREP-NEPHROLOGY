# Repository Guidelines

## Project Structure & Module Organization
The repository currently stores exam source material. `AAP_PDF/` contains the canonical PDF dumps, each named `prep_<year>.pdf`. `raw_txt/` holds the extracted text transcriptions that mirror the PDF filenames (`prep_2021.txt`, etc.) for easy traceability. Place any helper scripts you add under a new `tools/` directory and keep inputs/outputs grouped by year so reviewers can quickly diff related resources.

## Build, Test, and Development Commands
There is no compiled application yet, but use the following workflow to keep artifacts in sync:
- `pdftotext AAP_PDF/prep_2021.pdf raw_txt/prep_2021.txt` regenerates a text file from its PDF counterpart (install poppler if missing).
- `rg -n "keyword" raw_txt` verifies that a concept exists in the extracted corpus.
- `python -m venv .venv && source .venv/bin/activate` prepares an isolated environment for any processing scripts you add.
Document additional commands inside `tools/README.md` whenever you introduce new automation.

## Coding Style & Naming Conventions
Prefer Python for automation and use 4-space indentation, descriptive function names (`extract_questions`, `normalize_whitespace`), and snake_case filenames. Keep Markdown prose under ~100 characters per line for easy reviews. When committing new PDFs or text, follow the `prep_<year>.<ext>` pattern to keep chronological ordering predictable.

## Testing Guidelines
Before committing regenerated text, run `git diff --raw_txt/prep_2021.txt` (swap with your file) to confirm only the intended sections changed. If you add Python tooling, accompany it with `pytest` tests in a `tests/` folder that mirrors the module names (`tests/test_extraction.py`). Include fixtures with small text samples so reviewers can reproduce failures without the heavy PDFs. Aim to cover edge cases such as malformed headings or duplicate questions.

## Commit & Pull Request Guidelines
The repository has no history yet, so adopt Conventional Commits (`feat: add 2023 PDF ingestion`) to establish clarity from the start. Each pull request should describe the dataset source, the commands used to regenerate artifacts, and any assumptions or manual edits. Link to tracking issues when available and attach snippets (for text) or checksums (for PDFs) so reviewers can validate integrity. Large binary additions should note their size and the reason they are required.

## Security & Data Handling
Study materials can contain proprietary content. Store originals only inside `AAP_PDF/`, avoid embedding excerpts in commit messages, and scrub personal data if you incorporate annotations. When sharing intermediate files, prefer encrypted channels and document access controls in the PR.
