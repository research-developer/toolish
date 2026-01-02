# Toolish

Embeddings-based semantic tool discovery. Matches natural language requests like "fire off a quick note" to the right API tools using vector similarity.

## Quick Start

```bash
# Install dependencies
uv sync

# Option 1: With 1Password (recommended for production)
# The .env file contains 1Password secret references (op://...), not actual keys.
# Secrets are injected at runtime via `op run` and never touch disk.
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli seed
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli

# Option 2: Direct environment variable (for development/testing)
# If you don't have 1Password CLI, set OPENAI_API_KEY directly:
export OPENAI_API_KEY="sk-..."
export TOOLISH_MOCK_KEYCHAIN=1  # Use mock keychain instead of 1Password
PYTHONPATH=src uv run python -m toolish.cli seed
PYTHONPATH=src uv run python -m toolish.cli
```

### Seeding Options

```bash
# Seed with 18 hardcoded sample tools (default)
python -m toolish.cli seed

# Seed from YAML catalog (51 tools across AI, productivity, devtools)
python -m toolish.cli seed --from-catalog

# Seed specific category only
python -m toolish.cli seed --from-catalog --category ai
```

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
- **Keychain providers**: Pluggable keychain layer with both a 1Password-backed keychain and a mock keychain for testing/demo

By default, Toolish uses the 1Password-backed keychain (via `op run` and secret references in `.env`). To use the mock keychain instead, set `TOOLISH_MOCK_KEYCHAIN=1` before running the CLI.

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
