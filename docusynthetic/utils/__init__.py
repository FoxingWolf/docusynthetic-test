"""Configuration utilities."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration for DocuSynthetic."""

    # GitHub settings
    github_repo_owner: str = "veniceai"
    github_repo_name: str = "api-docs"
    github_branch: str = "main"
    github_docs_path: str = ""

    # OpenAPI settings
    openapi_spec_url: str = "https://raw.githubusercontent.com/veniceai/api-docs/main/swagger.yaml"

    # Live site settings
    live_site_url: str = "https://docs.venice.ai"
    live_site_headless: bool = True

    # Output settings
    output_dir: Path = Path("./output")

    # Source selection
    fetch_github: bool = True
    fetch_openapi: bool = True
    fetch_live_site: bool = True

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file or use defaults.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration object.
        """
        if config_path and config_path.exists():
            import json

            config_data = json.loads(config_path.read_text())
            return cls(**config_data)
        return cls()

    def save(self, config_path: Path) -> None:
        """Save configuration to file.

        Args:
            config_path: Path to save configuration.
        """
        config_path.write_text(self.model_dump_json(indent=2))
