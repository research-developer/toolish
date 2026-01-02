"""Mock API responses for local development.

Simulates actual API calls to services.
"""

from typing import Any


def mock_execute(tool_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Mock executing a tool - returns simulated success response."""
    return {
        "success": True,
        "tool_id": tool_id,
        "params": params,
        "message": f"[MOCK] Would execute {tool_id} with params: {params}",
    }


def mock_validate_params(tool_id: str, params: dict[str, Any]) -> tuple[bool, str | None]:
    """Mock parameter validation."""
    # In real impl, would check against tool's param schema
    return True, None
