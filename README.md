# ai scripts

## idea

- goal
  - ask ai a question about my notes and get info back with links
- solution
  - let a vector db handle the context search
  - let ai handle the answering
    - be it basic ai chat via the `ai_request.py` script
    - or agentic tools that do the answering to the vector db themselves
  - let ci/cd handle the vector upload after changes
    - new index creation should be done locally (long running task)
- initializing setup
  - chunking my notes into different parts to be turned into vectors
    - sections, which have the heading and the content (with sub-sections)
    - lists, which have the heading and the content of one list item and its sub-items
  - uploading these vectors with some metadata to a vector db like pinecone
    - path to the file
    - name of file
    - type of file
    - hash of file content
  - keeping track of the files and the version of its content that have been processed already
    - done via hash generation of file content and storing a tracking file
    - to avoid processing the same files without changes
    - to allow deletion of old files
    - also to allow rename/moving/deletion of complete files and their vectors
  - allowing upserts of new vectors to the db and ignoring already existing vectors
- answering setup (only relevant for manual request via `ai_request.py`)
  - get answer/request from user
  - (enhance question to make it more clear/specific)
    - via ollama or other tools
  - create a customized prompt aligned to my notes and their context
    - including question, instructions and context
  - format context as machine readable as possible
  - returning a ready prompt for chatgpt
  - manual pasting of prompt into chatgpt
- evaluation of the generated answers
  - comparing the generated answer with an expected answer
  - evaluating the quality of the answer

## setup

```bash
# install packages and create virtual `.venv`
uv sync

# editor needs to use the created `.venv` to have packages, etc.
# for example neovim:
uv run nvim
```

Then add the `PINECONE_API_KEY` to the `.env` file.

If `ollama` should be used, also add the `OLLAMA_HOST` to the `.env` file. And have the needed model(s) running.

## run

```bash
# run the notes indexer (auto run in ci/cd)
just indexer-test
just indexer-prod

# create prompt for an ai model and copy to clipboard
just ask "what is the best way to get a job?"

# or run it manually
## defaults: notes root is ~/Documents/notes; prod mode is off (-> testing mode)
uv run src/ai_notes_indexer.py --prod --root /path/to/notes
uv run src/ai_request.py "what is the best way to get a job?"
```

## testing


```bash
# for quick unit tests, mainly for the creation of chunks
just test
# or manually
uv run pytest

# for long running evaluation of the generated answers based on the QA pairs
# this expects `opencode` to be able to handle the answer/evaluation generation
just evaluate
# or manually
uv run src/evaluator.py
```
