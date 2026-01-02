"""WebSpec manifest schema for service registration."""

from pydantic import BaseModel, Field

from toolish.models.tool import Tool, ToolParams, ToolRoute, ToolSemantics


class ServiceMetadata(BaseModel):
    """Service-level metadata for the manifest."""

    name: str = Field(..., description="Human-readable service name")
    id: str = Field(..., description="Service ID (becomes subdomain, e.g., 'openai' -> openai.gimme.tools)")
    description: str = Field(default="", description="Service description")
    icon: str | None = Field(default=None, description="URL to service icon")
    homepage: str | None = Field(default=None, description="Service homepage URL")
    canonical_domains: list[str] = Field(default_factory=list, description="Domains this service operates under")


class OAuthConfig(BaseModel):
    """OAuth configuration for service authentication."""

    authorization_url: str | None = Field(default=None, description="OAuth authorization endpoint")
    token_url: str | None = Field(default=None, description="OAuth token endpoint")
    scopes: list[str] = Field(default_factory=list, description="Available OAuth scopes")


class WebhookConfig(BaseModel):
    """Webhook configuration for service events."""

    user_connected: str | None = Field(default=None, description="Webhook URL for user connection events")
    user_disconnected: str | None = Field(default=None, description="Webhook URL for user disconnection events")
    tool_invoked: str | None = Field(default=None, description="Webhook URL for tool invocation events")


class ManifestToolDefinition(BaseModel):
    """Tool definition within a manifest (YAML-friendly structure)."""

    id: str = Field(..., description="Unique tool identifier within the service")
    route: dict = Field(..., description="Route definition (method, path, types)")
    semantics: dict = Field(..., description="Semantic anchors (canonical, predicates, objects)")
    params: dict[str, dict] = Field(default_factory=dict, description="Tool parameters")


class ServiceManifest(BaseModel):
    """Complete WebSpec service manifest (gimme-tools.yaml)."""

    service: ServiceMetadata = Field(..., description="Service metadata")
    oauth: OAuthConfig | None = Field(default=None, description="OAuth configuration")
    webhooks: WebhookConfig | None = Field(default=None, description="Webhook configuration")
    tools: list[ManifestToolDefinition] = Field(default_factory=list, description="Tool definitions")

    def to_tools(self) -> list[Tool]:
        """Convert manifest tool definitions to Tool objects."""
        tools = []
        for tool_def in self.tools:
            # Build ToolRoute
            route = ToolRoute(
                method=tool_def.route.get("method", "GET"),
                path=tool_def.route.get("path", "/"),
                content_types=tool_def.route.get("types", []),
            )

            # Build ToolSemantics
            sem = tool_def.semantics
            semantics = ToolSemantics(
                canonical=sem.get("canonical", ""),
                predicates=sem.get("predicates", []),
                objects=sem.get("objects", []),
                contexts=sem.get("contexts", []),
                negative_examples=sem.get("not", []),
            )

            # Build params
            params = {}
            for param_name, param_def in tool_def.params.items():
                params[param_name] = ToolParams(
                    type=param_def.get("type", "string"),
                    required=param_def.get("required", False),
                    description=param_def.get("description", ""),
                )

            # Create Tool with service domain from canonical_domains or service.id
            service_domain = (
                self.service.canonical_domains[0]
                if self.service.canonical_domains
                else f"{self.service.id}.gimme.tools"
            )

            tool = Tool(
                id=tool_def.id,
                service=service_domain,
                route=route,
                semantics=semantics,
                params=params,
            )
            tools.append(tool)

        return tools
