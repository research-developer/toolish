"""Abstract keychain provider interface.

Defines the contract for keychain backends (1Password, mock, etc.)
"""

from abc import ABC, abstractmethod

from toolish.models.tool import ToolStatus


class KeychainProvider(ABC):
    """Abstract base class for keychain providers."""

    @abstractmethod
    def get_service_status(self, service_domain: str) -> ToolStatus:
        """Determine connection status for a service domain.

        Args:
            service_domain: The canonical domain (e.g., "api.openai.com")

        Returns:
            ToolStatus.CONNECTED if service has active API key
            ToolStatus.KEYCHAIN if service has credentials but no API key
            ToolStatus.AVAILABLE if service exists but no credentials
            ToolStatus.UNAVAILABLE otherwise
        """
        pass

    @abstractmethod
    def list_connected(self) -> list[str]:
        """List services with active OAuth/API tokens.

        Returns:
            List of service domains that are fully connected
        """
        pass

    @abstractmethod
    def list_keychain(self) -> list[str]:
        """List services with stored credentials (but not connected).

        Returns:
            List of service domains with credentials in keychain
        """
        pass

    @abstractmethod
    def list_available(self) -> list[str]:
        """List available services (neither connected nor in keychain).

        Returns:
            List of available service domains
        """
        pass

    @abstractmethod
    def get_credential(self, service: str, field: str = "api-key") -> str | None:
        """Fetch a credential on-demand.

        Args:
            service: Service domain (e.g., "api.openai.com")
            field: Field name to retrieve (default: "api-key")

        Returns:
            The credential value, or None if not found
        """
        pass
