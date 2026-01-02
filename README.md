# Toolish

**Semantic tool discovery for AI agents.** Match natural language requests like "fire off a quick note" to the right API tools using embeddings and real-time credential awareness.

---

## Why Toolish?

When you're building AI agents, the gap between what a user *says* and what API they *need* is huge. "Fire off a quick note" could mean Slack, email, SMS, or a dozen other things. Traditional keyword matching falls flat—you'd need to anticipate every possible phrasing.

Toolish solves this with **embeddings-based semantic matching**, a **three-way join algorithm** that factors in credential status, and a **live keychain** that knows what services your user can actually reach.

---

## Core Concepts

### Embeddings-Based Semantic Discovery

Embeddings map natural language into a vector space where semantically similar phrases cluster together, regardless of exact wording. Toolish uses OpenAI's `text-embedding-3-small` to embed both user queries and tool descriptions into the same space.

This means "send a message," "ping the team," and "drop a note" all land near tools tagged with predicates like `send`, `post`, `notify`. The result is intent-matching that feels almost telepathic—users describe what they want in their own words, and the right tool surfaces.

### Three-Way Join: Semantic Similarity × Connection Status

Raw semantic similarity isn't enough. If you ask to "send a Slack message" but you're not logged into Slack, that's a dead end. The three-way join solves this by combining vector search with real-world context: *what can this user actually do right now?*

The algorithm multiplies semantic scores by status weights:

| Status | Weight | Meaning |
|--------|--------|---------|
| **CONNECTED** | 1.0 | OAuth authorized or API key present—ready to execute |
| **KEYCHAIN** | 0.8 | Credentials exist but need setup (stored password, no token) |
| **AVAILABLE** | 0.5 | Tool exists in registry, no credentials found |

This means connected services bubble to the top, but you still see alternatives. An agent can say *"I'd use Slack, but you're not connected—want me to try Teams instead?"*

### 1Password as a Live Keychain

Most credential management in AI tooling is static—hardcoded lists, environment variables, or config files you have to maintain manually. Toolish flips this by querying 1Password directly. Your vault becomes the source of truth: add an API key to a service's "API Keys" section, and it automatically becomes CONNECTED.

This preserves the rich structure 1Password already provides. Instead of flattening everything into a `.env` file (where you lose context about what key goes where), Toolish reads items, inspects their sections, and maps URLs to service domains. Credentials are fetched on-demand via `op read`, so secrets never sit in memory unnecessarily.

### WebSpec YAML Catalog

Defining tools in code gets messy fast. You end up with massive Python dicts, duplicated metadata, and no easy way to add new services without touching core logic. WebSpec manifests externalize tool definitions into human-readable YAML files organized by category—`catalog/ai/openai.yaml`, `catalog/productivity/discord.yaml`, etc.

Each manifest describes a service and its tools with structured semantics:

- **Predicates** — The verbs: `send`, `generate`, `create`, `list`
- **Objects** — The nouns: `message`, `image`, `completion`, `task`
- **Contexts** — Usage hints: `ai generation`, `team communication`
- **Negative examples** — What this tool is *not* for (disambiguation)

Adding a new API is just dropping a YAML file in the right folder and running the seed script. No code changes, no redeployment—just declare the tool's semantics and let the embedding pipeline do the rest.

### Multi-Vector Search

A single embedding per tool is limiting. "Generate an image" and "create a picture" should match the same tool, but subtle differences in phrasing can push them apart in vector space. Toolish solves this with three parallel indices, each capturing a different facet of meaning.

The **canonical** collection embeds the full tool description. The **predicates** collection embeds the centroid of all action verbs. The **objects** collection does the same for nouns. At query time, we search all three and combine scores with configurable weights (default: 50% canonical, 30% predicates, 20% objects). This multi-vector approach is more robust to phrasing variations and gives you fine-grained control over what matters most in your matching.

---

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key
- 1Password CLI (`op`) — optional but recommended

### Quick Setup

```bash
git clone https://github.com/research-developer/toolish.git
cd toolish
uv sync
```

### Configuration

**Option 1: With 1Password (recommended)**

Create a `.env` file with 1Password secret references:

```bash
OPENAI_API_KEY=op://Personal/OpenAI/API Keys/default
```

Secrets are injected at runtime via `op run` and never touch disk:

```bash
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli seed
PYTHONPATH=src op run --env-file=.env -- uv run python -m toolish.cli
```

**Option 2: Direct environment variable**

```bash
export OPENAI_API_KEY="sk-..."
export TOOLISH_MOCK_KEYCHAIN=1  # Use mock keychain instead of 1Password
PYTHONPATH=src uv run python -m toolish.cli seed
PYTHONPATH=src uv run python -m toolish.cli
```

### Seeding the Database

```bash
# Seed with 18 sample tools (default)
python -m toolish.cli seed

# Seed from YAML catalog (51 tools across AI, productivity, devtools)
python -m toolish.cli seed --from-catalog

# Seed specific category only
python -m toolish.cli seed --from-catalog --category ai
```

---

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

---

## Architecture

```
src/toolish/
├── models/tool.py        # Tool schema (predicates, objects, semantics)
├── db/
│   ├── chroma.py         # ChromaDB wrapper with multi-vector search
│   └── seed.py           # Database seeding from code or YAML
├── embeddings/
│   └── openai.py         # OpenAI embedding client
├── search/
│   ├── nlp.py            # Predicate/object extraction (LLM + fallback)
│   └── resolver.py       # Three-way join algorithm
├── keychain/
│   ├── base.py           # Abstract KeychainProvider interface
│   ├── op.py             # 1Password CLI adapter
│   └── mock.py           # Mock keychain for testing
├── catalog/
│   └── loader.py         # WebSpec YAML manifest loader
└── cli.py                # Interactive REPL
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vector DB | ChromaDB | 3 collections: canonical, predicates, objects |
| Embeddings | OpenAI `text-embedding-3-small` | Semantic similarity |
| Keychain | 1Password CLI / Mock | Real-time credential status |
| Catalog | YAML manifests | Declarative tool definitions |

---

## Roadmap

Toolish is being developed as a **SaaS platform** for AI agent developers. Current focus:

- [ ] REST API for tool resolution
- [ ] Hosted embedding & vector search
- [ ] OAuth integration layer
- [ ] Multi-tenant keychain management
- [ ] Usage analytics dashboard

---

## License

MIT
