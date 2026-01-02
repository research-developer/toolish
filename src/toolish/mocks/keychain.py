"""DEPRECATED: Mock keychain has moved to toolish.keychain.mock

This module is kept for backwards compatibility only.
Use toolish.keychain.get_keychain() instead.
"""

import warnings

from toolish.keychain.mock import (
    AVAILABLE_SERVICES,
    CONNECTED_SERVICES,
    KEYCHAIN_DOMAINS,
    MockKeychain,
)
from toolish.models.tool import ToolStatus

# Re-export for backwards compatibility
__all__ = [
    "CONNECTED_SERVICES",
    "KEYCHAIN_DOMAINS",
    "AVAILABLE_SERVICES",
    "get_service_status",
    "list_connected",
    "list_keychain",
    "list_available",
]


def _warn_deprecation():
    warnings.warn(
        "toolish.mocks.keychain is deprecated. Use toolish.keychain instead.",
        DeprecationWarning,
        stacklevel=3,
    )


_mock = MockKeychain()


def get_service_status(service_domain: str) -> ToolStatus:
    """DEPRECATED: Use get_keychain().get_service_status() instead."""
    _warn_deprecation()
    return _mock.get_service_status(service_domain)


def list_connected() -> list[str]:
    """DEPRECATED: Use get_keychain().list_connected() instead."""
    _warn_deprecation()
    return _mock.list_connected()


def list_keychain() -> list[str]:
    """DEPRECATED: Use get_keychain().list_keychain() instead."""
    _warn_deprecation()
    return _mock.list_keychain()


def list_available() -> list[str]:
    """DEPRECATED: Use get_keychain().list_available() instead."""
    _warn_deprecation()
    return _mock.list_available()
