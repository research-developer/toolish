"""Keychain module for service credential management.

Provides a unified interface for querying service connection status
and retrieving credentials from various backends (1Password, mock, etc.)
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from toolish.keychain.base import KeychainProvider

# Singleton instance
_keychain: "KeychainProvider | None" = None


def get_keychain() -> "KeychainProvider":
    """Get the configured keychain provider.

    The provider is selected based on environment:
    - TOOLISH_MOCK_KEYCHAIN=1 → Use mock keychain
    - Otherwise → Use 1Password CLI

    Returns:
        The active KeychainProvider instance
    """
    global _keychain

    if _keychain is None:
        if os.environ.get("TOOLISH_MOCK_KEYCHAIN"):
            from toolish.keychain.mock import MockKeychain

            _keychain = MockKeychain()
        else:
            from toolish.keychain.op import OnePasswordKeychain

            _keychain = OnePasswordKeychain()

    return _keychain


def reset_keychain() -> None:
    """Reset the keychain singleton (for testing)."""
    global _keychain
    _keychain = None


# Re-export common types
from toolish.keychain.base import KeychainProvider

__all__ = ["get_keychain", "reset_keychain", "KeychainProvider"]
