"""1Password CLI keychain adapter.

Queries the `op` CLI to discover services and credentials.
"""

import json
import subprocess
from functools import lru_cache
from urllib.parse import urlparse

from toolish.keychain.base import KeychainProvider
from toolish.models.tool import ToolStatus


# Map common website domains to their canonical API domains
DOMAIN_MAP = {
    # AI Services
    "openai.com": "api.openai.com",
    "platform.openai.com": "api.openai.com",
    "console.anthropic.com": "api.anthropic.com",
    "anthropic.com": "api.anthropic.com",
    "replicate.com": "api.replicate.com",
    "huggingface.co": "api-inference.huggingface.co",
    "elevenlabs.io": "api.elevenlabs.io",
    # Productivity
    "linear.app": "api.linear.app",
    "app.asana.com": "app.asana.com",
    "asana.com": "app.asana.com",
    "discord.com": "discord.com",
    "telegram.org": "api.telegram.org",
    "twilio.com": "api.twilio.com",
    # Dev Tools
    "github.com": "github.com",
    "gitlab.com": "gitlab.com",
    "vercel.com": "api.vercel.com",
    "cloudflare.com": "api.cloudflare.com",
    # Google
    "mail.google.com": "gmail.com",
    "calendar.google.com": "calendar.google.com",
    "drive.google.com": "drive.google.com",
    # Microsoft
    "teams.microsoft.com": "teams.microsoft.com",
    # Other
    "slack.com": "slack.com",
    "notion.so": "notion.so",
    "app.supabase.com": "api.supabase.co",
    "supabase.com": "api.supabase.co",
}


class OnePasswordKeychain(KeychainProvider):
    """Keychain provider using 1Password CLI."""

    def __init__(self, vault: str = "Personal"):
        """Initialize with a specific vault.

        Args:
            vault: 1Password vault name to query
        """
        self.vault = vault
        self._items_cache: list[dict] | None = None
        self._item_details_cache: dict[str, dict] = {}

    def _run_op(self, *args: str) -> dict | list:
        """Execute op CLI command and parse JSON output.

        Raises:
            RuntimeError: If op command fails or CLI not installed
        """
        try:
            result = subprocess.run(
                ["op", *args, "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError("1Password CLI (op) not installed")
        except subprocess.TimeoutExpired:
            raise RuntimeError("1Password CLI timed out")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Unknown error"
            raise RuntimeError(f"1Password CLI failed: {error_msg}")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"1Password CLI returned invalid JSON: {e}")

    def _list_items(self) -> list[dict]:
        """Get all items from the vault (cached)."""
        if self._items_cache is None:
            try:
                self._items_cache = self._run_op("item", "list", "--vault", self.vault)
            except RuntimeError:
                # If op fails (not authenticated, etc.), return empty
                self._items_cache = []
        return self._items_cache

    def _get_item(self, item_id: str) -> dict:
        """Get full item details including fields (cached per item)."""
        if item_id not in self._item_details_cache:
            try:
                self._item_details_cache[item_id] = self._run_op("item", "get", item_id)
            except RuntimeError:
                self._item_details_cache[item_id] = {}
        return self._item_details_cache[item_id]

    def _normalize_domain(self, url: str) -> str | None:
        """Extract and normalize domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            # Remove port
            domain = domain.split(":")[0]
            return domain.lower() if domain else None
        except (ValueError, AttributeError):
            # urlparse can raise ValueError for invalid URLs
            # AttributeError if url is not a string-like object
            return None

    def _map_domain(self, domain: str) -> str:
        """Map website domain to canonical API domain."""
        return DOMAIN_MAP.get(domain, domain)

    @lru_cache(maxsize=1)
    def _extract_domains(self) -> dict[str, str]:
        """Build mapping of service domains → 1Password item IDs."""
        domains: dict[str, str] = {}
        for item in self._list_items():
            for url_entry in item.get("urls", []):
                url = url_entry.get("href", "")
                domain = self._normalize_domain(url)
                if domain:
                    canonical = self._map_domain(domain)
                    # Don't overwrite if we already have this domain
                    if canonical not in domains:
                        domains[canonical] = item["id"]
        return domains

    def _has_api_keys_section(self, item: dict) -> bool:
        """Check if item has an 'API Keys' section with fields."""
        for field in item.get("fields", []):
            section = field.get("section", {})
            if section.get("label", "").lower() == "api keys":
                return True
        return False

    def _classify_all_domains(self) -> tuple[list[str], list[str]]:
        """Classify all domains as connected or keychain in one pass.

        This avoids N+1 API calls by processing all domains together
        and leveraging the _item_details_cache.

        Returns:
            Tuple of (connected_domains, keychain_domains)
        """
        connected: list[str] = []
        keychain: list[str] = []

        for domain, item_id in self._extract_domains().items():
            item = self._get_item(item_id)
            if item and self._has_api_keys_section(item):
                connected.append(domain)
            elif item:
                keychain.append(domain)

        return sorted(connected), sorted(keychain)

    def get_service_status(self, service_domain: str) -> ToolStatus:
        """Determine connection status for a service domain."""
        domains = self._extract_domains()

        if service_domain not in domains:
            return ToolStatus.AVAILABLE

        item = self._get_item(domains[service_domain])
        if not item:
            return ToolStatus.AVAILABLE

        # If it has API Keys section → CONNECTED
        if self._has_api_keys_section(item):
            return ToolStatus.CONNECTED

        # Has URL but no API keys → KEYCHAIN
        return ToolStatus.KEYCHAIN

    def list_connected(self) -> list[str]:
        """List services that have API Keys sections."""
        return self._classify_all_domains()[0]

    def list_keychain(self) -> list[str]:
        """List services with URLs but no API Keys section."""
        return self._classify_all_domains()[1]

    def list_available(self) -> list[str]:
        """List known services not in keychain.

        Note: This returns an empty list since we don't have
        a complete registry of all available services here.
        The tool registry handles the AVAILABLE status.
        """
        return []

    def get_credential(
        self, service: str, field: str = "api-key"
    ) -> str | None:
        """Fetch credential on-demand using op read.

        Args:
            service: Service domain (e.g., "api.anthropic.com")
            field: Field label to find (case-insensitive, hyphens converted to spaces)

        Returns:
            The credential value, or None if not found
        """
        domains = self._extract_domains()
        if service not in domains:
            return None

        item = self._get_item(domains[service])
        if not item:
            return None

        # Normalize field name for comparison
        field_normalized = field.lower().replace("-", " ").replace("_", " ")

        # Look for field in API Keys section first
        for f in item.get("fields", []):
            section = f.get("section", {}).get("label", "").lower()
            label = f.get("label", "").lower()

            if section == "api keys" and label.replace("-", " ") == field_normalized:
                reference = f.get("reference")
                if reference:
                    try:
                        result = subprocess.run(
                            ["op", "read", reference],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        if result.returncode == 0:
                            return result.stdout.strip()
                    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                        # CLI not installed, timed out, or OS-level error
                        return None

        # If not found in API Keys, check other fields
        for f in item.get("fields", []):
            label = f.get("label", "").lower()
            if label.replace("-", " ") == field_normalized:
                reference = f.get("reference")
                if reference:
                    try:
                        result = subprocess.run(
                            ["op", "read", reference],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        if result.returncode == 0:
                            return result.stdout.strip()
                    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                        # CLI not installed, timed out, or OS-level error
                        return None

        return None

    def list_api_keys(self, service: str) -> list[str]:
        """List all API key field names for a service.

        Args:
            service: Service domain

        Returns:
            List of field labels in the API Keys section
        """
        domains = self._extract_domains()
        if service not in domains:
            return []

        item = self._get_item(domains[service])
        if not item:
            return []

        keys = []
        for f in item.get("fields", []):
            section = f.get("section", {}).get("label", "").lower()
            if section == "api keys":
                keys.append(f.get("label", ""))
        return keys

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._items_cache = None
        self._item_details_cache.clear()
        self._extract_domains.cache_clear()
