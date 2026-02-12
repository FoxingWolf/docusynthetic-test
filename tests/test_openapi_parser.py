"""Tests for OpenAPI parser."""

from venice_kb.sources.openapi_parser import parse_endpoints


def test_parse_endpoints(sample_swagger_snippet):
    """Test parsing endpoints from OpenAPI spec."""
    endpoints = parse_endpoints(sample_swagger_snippet)

    assert "POST /chat/completions" in endpoints
    endpoint = endpoints["POST /chat/completions"]
    assert endpoint["method"] == "POST"
    assert endpoint["path"] == "/chat/completions"
    assert endpoint["summary"] == "Create chat completion"
