"""Parse OpenAPI/Swagger specification and generate endpoint documentation."""

import hashlib
import json
import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class OpenAPIParser:
    """Parse swagger.yaml and extract endpoint documentation."""

    def __init__(self, swagger_content: str):
        self.swagger_content = swagger_content
        self.spec: dict[str, Any] = {}
        self._parse()

    def _parse(self) -> None:
        """Parse YAML content."""
        try:
            self.spec = yaml.safe_load(self.swagger_content)
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse swagger.yaml: {e}")
            self.spec = {}

    def _resolve_ref(self, ref: str) -> Any:
        """Resolve a $ref pointer."""
        if not ref.startswith("#/"):
            return None

        parts = ref[2:].split("/")
        obj = self.spec
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
        return obj

    def _expand_schema(self, schema: Any, depth: int = 0) -> Any:
        """Recursively expand schema, resolving $ref."""
        if depth > 10:  # Prevent infinite recursion
            return schema

        if isinstance(schema, dict):
            if "$ref" in schema:
                resolved = self._resolve_ref(schema["$ref"])
                if resolved:
                    return self._expand_schema(resolved, depth + 1)
            return {k: self._expand_schema(v, depth + 1) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self._expand_schema(item, depth + 1) for item in schema]
        return schema

    def extract_endpoints(self) -> list[dict[str, Any]]:
        """
        Extract all endpoints from OpenAPI spec.

        Returns:
            List of endpoint dicts with method, path, summary, description, parameters, etc.
        """
        endpoints = []
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                endpoint = {
                    "method": method.upper(),
                    "path": path,
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operation_id": operation.get("operationId", ""),
                    "tags": operation.get("tags", []),
                    "parameters": [],
                    "request_body": None,
                    "responses": {},
                    "deprecated": operation.get("deprecated", False),
                }

                # Extract parameters
                parameters = operation.get("parameters", [])
                for param in parameters:
                    param_expanded = self._expand_schema(param)
                    param_info = {
                        "name": param_expanded.get("name", ""),
                        "in": param_expanded.get("in", ""),
                        "required": param_expanded.get("required", False),
                        "description": param_expanded.get("description", ""),
                        "schema": param_expanded.get("schema", {}),
                        "type": param_expanded.get("schema", {}).get("type", ""),
                    }
                    endpoint["parameters"].append(param_info)

                # Extract request body
                if "requestBody" in operation:
                    request_body = operation["requestBody"]
                    content = request_body.get("content", {})
                    endpoint["request_body"] = {
                        "required": request_body.get("required", False),
                        "description": request_body.get("description", ""),
                        "content": {},
                    }
                    for content_type, content_schema in content.items():
                        schema = content_schema.get("schema", {})
                        endpoint["request_body"]["content"][content_type] = self._expand_schema(
                            schema
                        )

                # Extract responses
                responses = operation.get("responses", {})
                for status_code, response in responses.items():
                    response_expanded = self._expand_schema(response)
                    endpoint["responses"][status_code] = {
                        "description": response_expanded.get("description", ""),
                        "content": {},
                    }
                    content = response_expanded.get("content", {})
                    for content_type, content_schema in content.items():
                        schema = content_schema.get("schema", {})
                        endpoint["responses"][status_code]["content"][content_type] = (
                            self._expand_schema(schema)
                        )

                # Extract Venice-specific extensions
                for key, value in operation.items():
                    if key.startswith("x-venice-"):
                        endpoint[key] = value

                endpoints.append(endpoint)

        return endpoints

    def generate_endpoint_markdown(self, endpoint: dict[str, Any]) -> str:
        """Generate Markdown documentation for a single endpoint."""
        lines = []

        # Title
        title = endpoint.get("summary") or endpoint.get("operation_id", "Endpoint")
        lines.append(f"# {title}\n")

        # HTTP signature
        lines.append(f"```http\n{endpoint['method']} {endpoint['path']}\n```\n")

        # Description
        if endpoint.get("description"):
            lines.append(f"{endpoint['description']}\n")

        # Deprecated warning
        if endpoint.get("deprecated"):
            lines.append("> ⚠️ **Warning:** This endpoint is deprecated.\n")

        # Parameters
        if endpoint["parameters"]:
            lines.append("## Parameters\n")
            lines.append("| Name | Location | Type | Required | Description |")
            lines.append("|------|----------|------|----------|-------------|")
            for param in endpoint["parameters"]:
                name = param.get("name", "")
                location = param.get("in", "")
                param_type = param.get("type") or param.get("schema", {}).get("type", "")
                required = "Yes" if param.get("required") else "No"
                description = param.get("description", "").replace("\n", " ")
                lines.append(f"| `{name}` | {location} | {param_type} | {required} | {description} |")
            lines.append("")

        # Request Body
        if endpoint.get("request_body"):
            lines.append("## Request Body\n")
            if endpoint["request_body"].get("description"):
                lines.append(f"{endpoint['request_body']['description']}\n")
            for content_type, schema in endpoint["request_body"].get("content", {}).items():
                lines.append(f"**Content-Type:** `{content_type}`\n")
                lines.append("```json")
                lines.append(json.dumps(self._schema_to_example(schema), indent=2))
                lines.append("```\n")

        # Responses
        if endpoint["responses"]:
            lines.append("## Responses\n")
            for status_code, response in sorted(endpoint["responses"].items()):
                lines.append(f"### {status_code}\n")
                if response.get("description"):
                    lines.append(f"{response['description']}\n")
                for content_type, schema in response.get("content", {}).items():
                    lines.append(f"**Content-Type:** `{content_type}`\n")
                    lines.append("```json")
                    lines.append(json.dumps(self._schema_to_example(schema), indent=2))
                    lines.append("```\n")

        return "\n".join(lines)

    def _schema_to_example(self, schema: dict[str, Any]) -> Any:
        """Convert a JSON schema to an example value."""
        if not isinstance(schema, dict):
            return schema

        schema_type = schema.get("type")

        if schema.get("example") is not None:
            return schema["example"]

        if schema.get("enum"):
            return schema["enum"][0]

        if schema_type == "object":
            properties = schema.get("properties", {})
            return {key: self._schema_to_example(val) for key, val in properties.items()}
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._schema_to_example(items)]
        elif schema_type == "string":
            return schema.get("default", "string")
        elif schema_type == "integer":
            return schema.get("default", 0)
        elif schema_type == "number":
            return schema.get("default", 0.0)
        elif schema_type == "boolean":
            return schema.get("default", True)
        elif schema_type == "null":
            return None

        return {}

    def get_content_hash(self) -> str:
        """Get SHA256 hash of swagger content."""
        return hashlib.sha256(self.swagger_content.encode()).hexdigest()
