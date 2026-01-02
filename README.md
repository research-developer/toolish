# Toolish

Embeddings-based semantic tool discovery. Matches natural language requests like "fire off a quick note" to the right API tools using vector similarity.

## Quick Start

```bash
# Install dependencies
uv sync

# Seed the database (18 sample tools)
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli seed

# Run the REPL
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli
```

The `.env` file contains 1Password secret references (not actual keys), so secrets are injected at runtime via `op run` and never touch disk.

## Usage

```
> fire off a quick note to the team
Extraction:
  predicate: send (raw: 'send')
  object: message (raw: 'message')
  confidence: 0.95

Results (high confidence):
1. ✅ [CONNECTED] slack.com
   POST /message
   send message via Slack
   Score: 0.892

2. ✅ [CONNECTED] gmail.com
   POST /send
   send email via Gmail
   Score: 0.756

3. 🔐 [KEYCHAIN] teams.microsoft.com
   POST /message
   send message via Teams
   Score: 0.612
```

## Architecture

- **ChromaDB**: Vector storage with 3 indices (canonical, predicates, objects)
- **OpenAI embeddings**: `text-embedding-3-small` for semantic similarity
- **Three-way join**: Ranks by semantic score × connection status weight
- **Mock keychain**: Simulates OAuth connections and 1Password credentials

## Project Structure

```
src/toolish/
├── models/tool.py      # Tool schema (predicates, objects, semantics)
├── db/
│   ├── chroma.py       # ChromaDB wrapper with multi-vector search
│   └── seed.py         # 18 sample tools
├── embeddings/
│   └── openai.py       # OpenAI embedding client
├── search/
│   ├── nlp.py          # Predicate/object extraction (LLM + fallback)
│   └── resolver.py     # Three-way join algorithm
├── mocks/
│   ├── keychain.py     # Mock credentials
│   └── api.py          # Mock API responses
└── cli.py              # Interactive REPL
```
