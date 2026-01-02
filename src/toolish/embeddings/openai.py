"""OpenAI embedding client for semantic vector generation."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
_project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(_project_root / ".env")

# Embedding model config
MODEL = "text-embedding-3-small"
DIMENSIONS = 1536


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Get cached OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text string."""
    client = get_client()
    response = client.embeddings.create(input=text, model=MODEL)
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    if not texts:
        return []
    client = get_client()
    response = client.embeddings.create(input=texts, model=MODEL)
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def embed_centroid(texts: list[str]) -> list[float]:
    """Generate centroid embedding (average) for a list of texts."""
    if not texts:
        raise ValueError("Cannot compute centroid of empty list")

    embeddings = embed_batch(texts)

    # Compute element-wise average
    n = len(embeddings)
    centroid = [sum(emb[i] for emb in embeddings) / n for i in range(DIMENSIONS)]
    return centroid
