# used if no other argument is given to just (needs to stay at the top)
@_default:
  just --list

[group('ai')]
ask question:
  uv sync
  uv run src/ai_request.py "{{question}}"

[group('ai')]
indexer-test:
  uv sync
  uv run src/ai_notes_indexer.py

[group('ai')]
indexer-prod:
  uv sync
  uv run src/ai_notes_indexer.py --prod


[group('test')]
test:
  uv sync
  uv run pytest

[group('test')]
test-verbose:
  uv sync
  uv run pytest -vv

[group('test')]
evaluate:
  uv sync
  uv run src/evaluator.py


[group('dev')]
check:
  uv run ruff check --fix
  uv run ruff format
  npx prettier --write --cache --log-level warn '**/*.md'
  npx markdownlint-cli '**/*.md' -f --ignore-path '.gitignore'
