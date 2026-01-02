"""Three-way join resolver for tool discovery.

Combines:
1. Semantic search results from vector DB
2. User's connected services (OAuth)
3. User's keychain hints (1Password domains)
"""

from dataclasses import dataclass

from toolish.db.chroma import ToolDatabase
from toolish.keychain import get_keychain
from toolish.models.tool import Tool, ToolMatch, ToolRoute, ToolSemantics, ToolStatus
from toolish.search.nlp import Extraction, extract


@dataclass
class ResolverResult:
    """Complete result from the three-way join resolution."""

    query: str
    extraction: Extraction
    matches: list[ToolMatch]
    confidence: str  # "high", "medium", "low", "none"

    @property
    def best_match(self) -> ToolMatch | None:
        """Get the highest-scoring match."""
        return self.matches[0] if self.matches else None

    @property
    def connected_matches(self) -> list[ToolMatch]:
        """Get only connected service matches."""
        return [m for m in self.matches if m.status == ToolStatus.CONNECTED]

    @property
    def keychain_matches(self) -> list[ToolMatch]:
        """Get only keychain matches."""
        return [m for m in self.matches if m.status == ToolStatus.KEYCHAIN]


class Resolver:
    """Three-way join resolver for semantic tool discovery."""

    def __init__(self, db: ToolDatabase | None = None):
        self.db = db or ToolDatabase()

    def resolve(
        self,
        query: str,
        top_k: int = 10,
        use_llm: bool = True,
        min_similarity: float = 0.5,
    ) -> ResolverResult:
        """Resolve a natural language query to ranked tool matches.

        The three-way join:
        1. Extract predicate/object from query
        2. Semantic search against tool registry
        3. Classify each match by user's relationship (connected/keychain/available)
        4. Compute weighted scores and rank
        """
        # Step 1: NLP extraction
        extraction = extract(query, use_llm=use_llm)

        # Step 2: Multi-vector semantic search
        search_results = self.db.search(
            query_text=extraction.action_text,
            predicate_text=extraction.predicate,
            object_text=extraction.object,
            top_k=top_k * 2,  # Get more to filter
        )

        # Step 3 & 4: Classify and score each match
        matches: list[ToolMatch] = []
        keychain = get_keychain()  # Fetch once, outside loop

        for result in search_results:
            semantic_score = result["weighted_score"]

            # Skip low similarity matches
            if semantic_score < min_similarity:
                continue

            # Get service status from keychain
            service = result["metadata"]["service"]
            status = keychain.get_service_status(service)

            # Skip unavailable
            if status == ToolStatus.UNAVAILABLE:
                continue

            # Reconstruct tool from metadata
            metadata = result["metadata"]
            # Parse predicates/objects, filtering empty strings from split
            predicates = [p for p in metadata["predicates"].split(",") if p]
            objects = [o for o in metadata["objects"].split(",") if o]

            tool = Tool(
                id=metadata["id"],
                service=metadata["service"],
                route=ToolRoute(method=metadata["method"], path=metadata["path"]),
                semantics=ToolSemantics(
                    canonical=metadata["canonical"],
                    predicates=predicates,
                    objects=objects,
                ),
            )

            # Compute final score
            match = ToolMatch.compute_score(
                tool=tool,
                status=status,
                semantic_score=semantic_score,
            )
            matches.append(match)

        # Sort by final score
        matches.sort(key=lambda m: m.final_score, reverse=True)
        matches = matches[:top_k]

        # Determine confidence level
        if not matches:
            confidence = "none"
        elif matches[0].final_score > 0.8:
            confidence = "high"
        elif matches[0].final_score > 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        return ResolverResult(
            query=query,
            extraction=extraction,
            matches=matches,
            confidence=confidence,
        )

    def resolve_quick(self, query: str) -> ResolverResult:
        """Quick resolution without LLM (uses simple extraction)."""
        return self.resolve(query, use_llm=False)
