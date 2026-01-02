"""Load WebSpec manifests from YAML files."""

from pathlib import Path

import yaml

from toolish.models.manifest import ServiceManifest
from toolish.models.tool import Tool


class CatalogLoader:
    """Loads WebSpec manifests from a catalog directory."""

    def __init__(self, catalog_path: Path | str | None = None):
        """Initialize loader with catalog path.

        Args:
            catalog_path: Path to catalog directory. Defaults to project root catalog/.
        """
        if catalog_path is None:
            # Default to project root catalog/
            catalog_path = Path(__file__).parent.parent.parent.parent / "catalog"
        self.catalog_path = Path(catalog_path)

    def discover_manifests(self) -> list[Path]:
        """Find all YAML manifest files in the catalog."""
        if not self.catalog_path.exists():
            return []

        manifests = []
        for yaml_file in self.catalog_path.rglob("*.yaml"):
            manifests.append(yaml_file)
        for yml_file in self.catalog_path.rglob("*.yml"):
            manifests.append(yml_file)

        return sorted(manifests)

    def load_manifest(self, manifest_path: Path) -> ServiceManifest:
        """Load a single manifest file."""
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        return ServiceManifest(**data)

    def load_all(self) -> list[Tool]:
        """Load all manifests and return Tool objects."""
        all_tools: list[Tool] = []

        for manifest_path in self.discover_manifests():
            try:
                manifest = self.load_manifest(manifest_path)
                tools = manifest.to_tools()
                all_tools.extend(tools)
                print(f"  Loaded {len(tools)} tools from {manifest_path.name}")
            except Exception as e:
                print(f"  Warning: Failed to load {manifest_path}: {e}")

        return all_tools

    def load_category(self, category: str) -> list[Tool]:
        """Load manifests from a specific category (ai, productivity, devtools)."""
        category_path = self.catalog_path / category
        if not category_path.exists():
            return []

        tools: list[Tool] = []
        for manifest_path in sorted(category_path.glob("*.yaml")) + sorted(
            category_path.glob("*.yml")
        ):
            try:
                manifest = self.load_manifest(manifest_path)
                tools.extend(manifest.to_tools())
            except Exception as e:
                print(f"  Warning: Failed to load {manifest_path}: {e}")

        return tools


def load_catalog(
    catalog_path: Path | str | None = None,
    category: str | None = None,
) -> list[Tool]:
    """Convenience function to load tools from catalog.

    Args:
        catalog_path: Path to catalog directory. Defaults to project root catalog/.
        category: Optional category to filter by (ai, productivity, devtools).

    Returns:
        List of Tool objects from manifests.
    """
    loader = CatalogLoader(catalog_path)
    if category:
        return loader.load_category(category)
    return loader.load_all()
