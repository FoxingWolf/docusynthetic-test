"""OpenAPI specification fetcher."""

import hashlib
from datetime import datetime
from typing import Any, Dict, List

import httpx
import yaml

from docusynthetic.models import APIEndpoint, DocumentContent, DocumentMetadata, SourceType

from .base import BaseFetcher


class OpenAPIFetcher(BaseFetcher):
    """Fetches and parses OpenAPI specification."""

    def __init__(self, spec_url: str):
        """Initialize OpenAPI fetcher.

        Args:
            spec_url: URL to the OpenAPI specification file (YAML or JSON).
        """
        self.spec_url = spec_url

    async def fetch(self) -> List[DocumentContent]:
        """Fetch and parse OpenAPI specification.

        Returns:
            List of DocumentContent objects representing the API.
        """
        documents = []

        async with httpx.AsyncClient() as client:
            response = await client.get(self.spec_url)
            response.raise_for_status()

            # Parse YAML or JSON
            if self.spec_url.endswith(".yaml") or self.spec_url.endswith(".yml"):
                spec = yaml.safe_load(response.text)
            else:
                spec = response.json()

            # Extract API info
            info = spec.get("info", {})
            title = info.get("title", "API Documentation")
            description = info.get("description", "")

            # Create overview document
            overview_content = self._generate_overview(spec)
            overview_hash = hashlib.sha256(overview_content.encode()).hexdigest()

            metadata = DocumentMetadata(
                title=title,
                source=SourceType.OPENAPI_SPEC,
                source_url=self.spec_url,
                last_updated=datetime.now(),
                tags=["openapi", "overview"],
            )

            overview_doc = DocumentContent(
                metadata=metadata,
                content=overview_content,
                raw_content=response.text,
                content_hash=overview_hash,
            )
            documents.append(overview_doc)

            # Parse endpoints
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.lower() in ["get", "post", "put", "delete", "patch", "options"]:
                        endpoint_doc = self._create_endpoint_document(
                            path, method, details, spec
                        )
                        documents.append(endpoint_doc)

        return documents

    def _generate_overview(self, spec: Dict[str, Any]) -> str:
        """Generate overview markdown from OpenAPI spec.

        Args:
            spec: OpenAPI specification dictionary.

        Returns:
            Markdown formatted overview.
        """
        info = spec.get("info", {})
        title = info.get("title", "API Documentation")
        description = info.get("description", "")
        version = info.get("version", "1.0.0")

        servers = spec.get("servers", [])
        server_list = "\n".join([f"- {s.get('url', '')} - {s.get('description', '')}" for s in servers])

        overview = f"""# {title}

**Version:** {version}

## Description

{description}

## Servers

{server_list}

## Available Endpoints

This API documentation was generated from the OpenAPI specification.
"""
        return overview

    def _create_endpoint_document(
        self, path: str, method: str, details: Dict[str, Any], spec: Dict[str, Any]
    ) -> DocumentContent:
        """Create a document for a single endpoint.

        Args:
            path: Endpoint path.
            method: HTTP method.
            details: Endpoint details from spec.
            spec: Full OpenAPI specification.

        Returns:
            DocumentContent for the endpoint.
        """
        summary = details.get("summary", "")
        description = details.get("description", "")
        tags = details.get("tags", [])

        # Generate markdown content
        content = f"""# {method.upper()} {path}

## Summary

{summary}

## Description

{description}

## Parameters

"""
        parameters = details.get("parameters", [])
        if parameters:
            for param in parameters:
                param_name = param.get("name", "")
                param_in = param.get("in", "")
                param_desc = param.get("description", "")
                param_required = param.get("required", False)
                content += f"- **{param_name}** ({param_in}){' - Required' if param_required else ''}: {param_desc}\n"
        else:
            content += "No parameters.\n"

        # Request body
        request_body = details.get("requestBody", {})
        if request_body:
            content += "\n## Request Body\n\n"
            content += request_body.get("description", "")

        # Responses
        responses = details.get("responses", {})
        if responses:
            content += "\n## Responses\n\n"
            for status_code, response_info in responses.items():
                response_desc = response_info.get("description", "")
                content += f"### {status_code}\n\n{response_desc}\n\n"

        # Create hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Create metadata
        metadata = DocumentMetadata(
            title=f"{method.upper()} {path}",
            source=SourceType.OPENAPI_SPEC,
            source_url=self.spec_url,
            last_updated=datetime.now(),
            tags=tags + ["endpoint", method.lower()],
            category="API Endpoints",
        )

        return DocumentContent(
            metadata=metadata,
            content=content,
            raw_content=yaml.dump(details),
            content_hash=content_hash,
        )
