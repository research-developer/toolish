"""ChromaDB wrapper for multi-vector tool search."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from toolish.embeddings.openai import embed_centroid, embed_text
from toolish.models.tool import Tool

# Default persist directory
DEFAULT_PERSIST_DIR = Path.home() / ".toolish" / "chroma"


class ToolDatabase:
    """ChromaDB-backed vector database for tool discovery."""

    def __init__(self, persist_dir: Path | None = None):
        """Initialize ChromaDB client with persistence."""
        self.persist_dir = persist_dir or DEFAULT_PERSIST_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Three collections for multi-vector search
        self.canonical = self.client.get_or_create_collection(
            name="canonical", metadata={"hnsw:space": "cosine"}
        )
        self.predicates = self.client.get_or_create_collection(
            name="predicates", metadata={"hnsw:space": "cosine"}
        )
        self.objects = self.client.get_or_create_collection(
            name="objects", metadata={"hnsw:space": "cosine"}
        )

    def register_tool(self, tool: Tool) -> None:
        """Register a tool with embeddings in all three collections."""
        metadata = tool.to_chroma_metadata()

        # 1. Canonical embedding
        canonical_emb = embed_text(tool.semantics.canonical)
        self.canonical.upsert(
            ids=[tool.id], embeddings=[canonical_emb], metadatas=[metadata]
        )

        # 2. Predicate centroid
        pred_emb = embed_centroid(tool.semantics.predicates)
        self.predicates.upsert(ids=[tool.id], embeddings=[pred_emb], metadatas=[metadata])

        # 3. Object centroid
        obj_emb = embed_centroid(tool.semantics.objects)
        self.objects.upsert(ids=[tool.id], embeddings=[obj_emb], metadatas=[metadata])

    def search(
        self,
        query_text: str,
        predicate_text: str | None = None,
        object_text: str | None = None,
        top_k: int = 10,
        canonical_weight: float = 0.5,
        predicate_weight: float = 0.3,
        object_weight: float = 0.2,
    ) -> list[dict[str, Any]]:
        """
        Multi-vector search across canonical, predicate, and object indices.

        Returns combined results weighted by the specified factors.
        """
        # Generate query embeddings
        query_emb = embed_text(query_text)
        pred_emb = embed_text(predicate_text) if predicate_text else query_emb
        obj_emb = embed_text(object_text) if object_text else query_emb

        # Search each collection
        canonical_results = self.canonical.query(
            query_embeddings=[query_emb], n_results=top_k, include=["metadatas", "distances"]
        )
        predicate_results = self.predicates.query(
            query_embeddings=[pred_emb], n_results=top_k, include=["metadatas", "distances"]
        )
        object_results = self.objects.query(
            query_embeddings=[obj_emb], n_results=top_k, include=["metadatas", "distances"]
        )

        # Combine scores (ChromaDB returns distances, convert to similarities)
        scores: dict[str, dict[str, Any]] = {}

        def add_scores(results: dict, weight: float, source: str) -> None:
            ids = results["ids"][0] if results["ids"] else []
            distances = results["distances"][0] if results["distances"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            for tool_id, distance, metadata in zip(ids, distances, metadatas):
                # Convert cosine distance to similarity (1 - distance for normalized vectors)
                similarity = 1 - distance

                if tool_id not in scores:
                    scores[tool_id] = {
                        "id": tool_id,
                        "metadata": metadata,
                        "canonical_score": 0.0,
                        "predicate_score": 0.0,
                        "object_score": 0.0,
                        "weighted_score": 0.0,
                    }

                scores[tool_id][f"{source}_score"] = similarity
                scores[tool_id]["weighted_score"] += similarity * weight

        add_scores(canonical_results, canonical_weight, "canonical")
        add_scores(predicate_results, predicate_weight, "predicate")
        add_scores(object_results, object_weight, "object")

        # Sort by weighted score
        ranked = sorted(scores.values(), key=lambda x: x["weighted_score"], reverse=True)
        return ranked[:top_k]

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools (metadata only)."""
        results = self.canonical.get(include=["metadatas"])
        return results["metadatas"] if results["metadatas"] else []

    def clear(self) -> None:
        """Clear all collections (for testing/reset)."""
        self.client.delete_collection("canonical")
        self.client.delete_collection("predicates")
        self.client.delete_collection("objects")
        # Recreate
        self.canonical = self.client.get_or_create_collection(
            name="canonical", metadata={"hnsw:space": "cosine"}
        )
        self.predicates = self.client.get_or_create_collection(
            name="predicates", metadata={"hnsw:space": "cosine"}
        )
        self.objects = self.client.get_or_create_collection(
            name="objects", metadata={"hnsw:space": "cosine"}
        )
