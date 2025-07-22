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

## setup

```bash
# justfile: onetime setup python
just setup

# manually: onetime setup python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# to get access to python (repeat for every new terminal)
source venv/bin/activate

# to upgrade the packages
pip install --upgrade -r requirements.txt
```

Then add the `PINECONE_API_KEY` to the `.env` file.

If `ollama` should be used, also add the `OLLAMA_HOST` to the `.env` file. And have the needed model(s) running.

## running

```bash
# run the indexer (long running task)
# ci/cd will do this periodically - note: initial setup takes long, so should be done locally
# defaults: notes root is ~/Documents/notes; prod mode is off (-> testing mode)
python3 src/ai_notes_indexer.py

# run prod setup with custom notes root
python3 src/ai_notes_indexer.py --prod --root /path/to/notes

# justfile: create prompt for chatgpt and copy to clipboard
just ask "what is the best way to get a job?"

# manually: create prompt for chatgpt and copy to clipboard
python3 src/ai_request.py "what is the best way to get a job?" | clip
```

## testing

### automated tests

```bash
pytest
```

### manual tests

- baseline questions after running the `just ask` command and asking `chatgpt` to answer them
  - `just ask "i want to delete a camera for bid dutchman what do i need to consider?"`
    - should include
      - frontend usage
        - disabled when flags not set and data sent
        - using it to trigger events
      - how to update flag in db
      - info about legal entity for permission
      - reference to wiki because of readding the same camera
      - links to the wiki and my notes
        - mainly my camera-manager notes
        - wiki to camera manager setup/deletion page
