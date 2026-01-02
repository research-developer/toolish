"""Tool schema definitions for semantic discovery."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolStatus(str, Enum):
    """Connection status for a tool/service."""

    CONNECTED = "connected"  # OAuth already authorized
    KEYCHAIN = "keychain"  # Found in password manager
    AVAILABLE = "available"  # In registry but not connected
    UNAVAILABLE = "unavailable"  # Not in registry

    @property
    def weight(self) -> float:
        """Weight for scoring based on status."""
        return {
            ToolStatus.CONNECTED: 1.0,
            ToolStatus.KEYCHAIN: 0.8,
            ToolStatus.AVAILABLE: 0.5,
            ToolStatus.UNAVAILABLE: 0.0,
        }[self]


class ToolRoute(BaseModel):
    """WebSpec route definition."""

    method: str = Field(..., description="HTTP method (GET, POST, DELETE, etc.)")
    path: str = Field(..., description="Route path (e.g., /message)")
    content_types: list[str] = Field(default_factory=list, description="Supported content types")


class ToolSemantics(BaseModel):
    """Semantic anchors for embedding generation."""

    canonical: str = Field(..., description="Canonical description (e.g., 'send message via Slack')")
    predicates: list[str] = Field(
        ..., description="Action verbs (e.g., ['send', 'post', 'message', 'notify', 'ping'])"
    )
    objects: list[str] = Field(
        ..., description="Object nouns (e.g., ['message', 'note', 'notification', 'text'])"
    )
    contexts: list[str] = Field(
        default_factory=list, description="Usage contexts (e.g., ['team communication'])"
    )
    negative_examples: list[str] = Field(
        default_factory=list, description="What this tool is NOT (e.g., ['send email'])"
    )


class ToolParams(BaseModel):
    """Parameter definition for a tool."""

    type: str = Field(..., description="Parameter type (string, number, boolean, etc.)")
    required: bool = Field(default=False, description="Whether parameter is required")
    description: str = Field(default="", description="Parameter description")


class Tool(BaseModel):
    """Complete tool registration record."""

    id: str = Field(..., description="Unique tool identifier (e.g., 'slack-send-message')")
    service: str = Field(..., description="Service domain (e.g., 'slack.com')")
    route: ToolRoute = Field(..., description="WebSpec route definition")
    semantics: ToolSemantics = Field(..., description="Semantic anchors for discovery")
    params: dict[str, ToolParams] = Field(default_factory=dict, description="Tool parameters")

    def to_chroma_metadata(self) -> dict[str, Any]:
        """Convert to flat metadata dict for ChromaDB storage."""
        return {
            "id": self.id,
            "service": self.service,
            "method": self.route.method,
            "path": self.route.path,
            "canonical": self.semantics.canonical,
            "predicates": ",".join(self.semantics.predicates),
            "objects": ",".join(self.semantics.objects),
        }


class ToolMatch(BaseModel):
    """A tool match result from search."""

    tool: Tool
    status: ToolStatus
    semantic_score: float = Field(..., description="Cosine similarity from vector search")
    final_score: float = Field(..., description="Weighted final score")

    @classmethod
    def compute_score(
        cls,
        tool: Tool,
        status: ToolStatus,
        semantic_score: float,
        recency_boost: float = 1.0,
        preference_boost: float = 1.0,
    ) -> "ToolMatch":
        """Compute final score with all factors."""
        final = semantic_score * status.weight * recency_boost * preference_boost
        return cls(tool=tool, status=status, semantic_score=semantic_score, final_score=final)
