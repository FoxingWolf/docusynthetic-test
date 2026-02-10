"""Smoke tests to ensure basic imports work."""

import pytest


def test_import_main():
    """Test that main module can be imported."""
    from venice_kb import __version__

    assert __version__ == "0.1.0"


def test_import_sources():
    """Test that source modules can be imported."""
    from venice_kb.sources import github_fetcher, openapi_parser, web_scraper

    assert github_fetcher is not None
    assert openapi_parser is not None
    assert web_scraper is not None


def test_import_processing():
    """Test that processing modules can be imported."""
    from venice_kb.processing import mdx_converter, html_converter, merger

    assert mdx_converter is not None
    assert html_converter is not None
    assert merger is not None


def test_import_diffing():
    """Test that diffing modules can be imported."""
    from venice_kb.diffing import models, snapshot, differ

    assert models is not None
    assert snapshot is not None
    assert differ is not None


def test_import_output():
    """Test that output modules can be imported."""
    from venice_kb.output import kb_writer, index_writer

    assert kb_writer is not None
    assert index_writer is not None


def test_import_cli():
    """Test that CLI can be imported."""
    from venice_kb import cli

    assert cli is not None
    assert cli.app is not None
