"""Shared pytest configuration and fixtures."""

import pytest


@pytest.fixture
def temp_kb_dir(tmp_path):
    """Create temporary knowledge base directory."""
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()
    return kb_dir
