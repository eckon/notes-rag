# Notes RAG

A smart Q&A system for my personal notes using vector search and AI.

**Note:** This is based on my personal notes, therefore code changes would be needed for others to use it.

## What it does

Ask questions about my notes and get intelligent answers with source links.

The system automatically chunks my markdown notes,
stores them in a vector database (Pinecone),
and enables the use of AI to provide contextual responses.

**Key features:**

- Automatic note indexing with CI/CD
- Smart chunking of markdown sections and lists
- Vector-based semantic search
- AI-powered question answering
- Source file tracking and incremental updates
- Evaluation of AI-generated answers quality

## Workflow

1. **Index your notes** - Run the indexer to chunk and store your markdown files in the vector database
2. **Ask questions** - Choose one of two approaches:
   - **Simple Q&A**: Use the `ask` command to generate AI prompts with relevant context
   - **Advanced queries**: Use agentic AI tools (like `opencode` or `claude code`) that connect directly (e.g `mcp`) to the vector database for complex, multi-step questions

## Setup

1. Install dependencies:

> **Note:** Use `uv run nvim` to launch your editor with the correct virtual environment.

```bash
uv sync
```

2. Create `.env` file with:

```env
PINECONE_API_KEY=your_api_key
OLLAMA_HOST=http://localhost:11434  # optional for local AI question enhancement
```

## Usage

**Quick commands:**

```bash
# Index your notes (*-test for testing vector db)
just indexer-prod

# Ask a question and get the prompt in the clipboard
just ask "what did i do the last week?"
```

**Manual usage:**

> See `justfile` or scripts in `src/` for additional commands.

```bash
# Index notes (defaults to ~/Documents/notes)
uv run src/ai_notes_indexer.py --prod --root /path/to/notes
```

## Testing

```bash
# Run unit tests
just test

# Evaluate answer quality
just evaluate
```
