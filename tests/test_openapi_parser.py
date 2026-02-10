"""Test OpenAPI parser."""

from pathlib import Path

import pytest

from venice_kb.sources.openapi_parser import OpenAPIParser


@pytest.fixture
def sample_swagger():
    """Load sample swagger fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_swagger.yaml"
    return fixture_path.read_text()


def test_parse_swagger(sample_swagger):
    """Test parsing swagger YAML."""
    parser = OpenAPIParser(sample_swagger)
    assert parser.spec is not None
    assert "paths" in parser.spec


def test_extract_endpoints(sample_swagger):
    """Test endpoint extraction."""
    parser = OpenAPIParser(sample_swagger)
    endpoints = parser.extract_endpoints()

    assert len(endpoints) == 2
    assert any(e["path"] == "/chat/completions" for e in endpoints)
    assert any(e["path"] == "/models" for e in endpoints)


def test_endpoint_parameters(sample_swagger):
    """Test parameter extraction."""
    parser = OpenAPIParser(sample_swagger)
    endpoints = parser.extract_endpoints()

    models_endpoint = next(e for e in endpoints if e["path"] == "/models")
    assert len(models_endpoint["parameters"]) == 1
    assert models_endpoint["parameters"][0]["name"] == "type"


def test_request_body_extraction(sample_swagger):
    """Test request body schema extraction."""
    parser = OpenAPIParser(sample_swagger)
    endpoints = parser.extract_endpoints()

    chat_endpoint = next(e for e in endpoints if e["path"] == "/chat/completions")
    assert chat_endpoint["request_body"] is not None
    assert chat_endpoint["request_body"]["required"] is True


def test_resolve_ref(sample_swagger):
    """Test $ref resolution."""
    parser = OpenAPIParser(sample_swagger)
    resolved = parser._resolve_ref("#/components/schemas/Message")
    assert resolved is not None
    assert "properties" in resolved


def test_generate_markdown(sample_swagger):
    """Test endpoint markdown generation."""
    parser = OpenAPIParser(sample_swagger)
    endpoints = parser.extract_endpoints()
    chat_endpoint = next(e for e in endpoints if e["path"] == "/chat/completions")

    markdown = parser.generate_endpoint_markdown(chat_endpoint)
    assert "Create chat completion" in markdown
    assert "POST /chat/completions" in markdown
    assert "## Parameters" in markdown or "## Request Body" in markdown


def test_content_hash(sample_swagger):
    """Test content hash generation."""
    parser = OpenAPIParser(sample_swagger)
    hash1 = parser.get_content_hash()
    assert len(hash1) == 64  # SHA256 hex

    # Same content should produce same hash
    parser2 = OpenAPIParser(sample_swagger)
    hash2 = parser2.get_content_hash()
    assert hash1 == hash2
