# Coding Agent Guidelines

## Build Commands

- Install deps: `uv sync`
- Run tests: `mise run test` (or `uv run pytest`)
  - NEVER RUN `mise run evaluate` (or `uv run src/evaluator.py`)
- Run single test: `uv run pytest src/markdown_chunker_test.py::test_function_name`
- Lint/format: `mise run check` (runs ruff check/format, prettier, markdownlint)

## Code Style

- Check `pyproject.toml` for more details of the project
- Language: Python 3.12+
- Package manager: `uv` (not pip)
- Imports: Standard library first, third-party, then local modules (see ai_notes_indexer.py:1-26)
- Formatting: Use `ruff format` and `ruff check --fix`
- Types: Use type hints where appropriate
- Naming: snake_case for functions/variables, PascalCase for classes
- Error handling: Use try/except blocks, print colored error messages with config.py colors
- Config: Use config.py for constants, environment variables via python-dotenv
- File structure: Main logic in classes, separate test files with `_test.py` suffix
- Documentation: Use docstrings for classes, brief comments for complex logic only
- Testing: Use pytest, test files alongside source files in src/
