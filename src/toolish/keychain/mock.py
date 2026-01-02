"""Mock keychain provider for testing and development.

Provides hardcoded service statuses without requiring 1Password.
"""

from toolish.keychain.base import KeychainProvider
from toolish.models.tool import ToolStatus


# Mock user's connected services (OAuth already authorized)
CONNECTED_SERVICES: set[str] = {
    # Original services
    "slack.com",
    "gmail.com",
    "calendar.google.com",
    # AI services
    "api.openai.com",
    "api.anthropic.com",
    # Productivity services
    "api.linear.app",
    "discord.com",
}

# Mock user's keychain hints (has credentials but not OAuth connected)
KEYCHAIN_DOMAINS: set[str] = {
    # Original services
    "drive.google.com",
    "github.com",
    "teams.microsoft.com",
    # AI services
    "api.replicate.com",
    "api-inference.huggingface.co",
    # Productivity services
    "app.asana.com",
    "api.telegram.org",
    # Dev tools
    "gitlab.com",
    "api.vercel.com",
}

# All available services in the registry
AVAILABLE_SERVICES: set[str] = {
    # === Original/Hardcoded ===
    "slack.com",
    "gmail.com",
    "calendar.google.com",
    "drive.google.com",
    "github.com",
    "teams.microsoft.com",
    "notion.so",
    "dropbox.com",
    "trello.com",
    # === AI/ML Services ===
    "api.openai.com",
    "api.anthropic.com",
    "api.replicate.com",
    "api-inference.huggingface.co",
    "api.elevenlabs.io",
    # === Productivity Services ===
    "api.linear.app",
    "app.asana.com",
    "discord.com",
    "api.telegram.org",
    "api.twilio.com",
    # === Dev Tools ===
    "gitlab.com",
    "api.vercel.com",
    "api.cloudflare.com",
}

# Mock API keys for testing
MOCK_CREDENTIALS: dict[str, dict[str, str]] = {
    "api.openai.com": {"api-key": "sk-mock-openai-key"},
    "api.anthropic.com": {"api-key": "sk-ant-mock-anthropic-key"},
    "slack.com": {"api-key": "xoxb-mock-slack-token"},
    "github.com": {"api-key": "ghp_mock_github_token"},
}


class MockKeychain(KeychainProvider):
    """Mock keychain provider with hardcoded data."""

    def get_service_status(self, service_domain: str) -> ToolStatus:
        """Determine the connection status for a service domain."""
        if service_domain in CONNECTED_SERVICES:
            return ToolStatus.CONNECTED
        if service_domain in KEYCHAIN_DOMAINS:
            return ToolStatus.KEYCHAIN
        if service_domain in AVAILABLE_SERVICES:
            return ToolStatus.AVAILABLE
        return ToolStatus.UNAVAILABLE

    def list_connected(self) -> list[str]:
        """List all connected services."""
        return sorted(CONNECTED_SERVICES)

    def list_keychain(self) -> list[str]:
        """List all services with keychain credentials."""
        return sorted(KEYCHAIN_DOMAINS)

    def list_available(self) -> list[str]:
        """List all available (but not connected) services."""
        return sorted(AVAILABLE_SERVICES - CONNECTED_SERVICES - KEYCHAIN_DOMAINS)

    def get_credential(self, service: str, field: str = "api-key") -> str | None:
        """Get mock credential for a service."""
        service_creds = MOCK_CREDENTIALS.get(service, {})
        return service_creds.get(field)
