"""Render changelog as .md and .json."""

# This is a duplicate of changelog_writer.py functionality
# In diffing module - kept for consistency with spec structure

from venice_kb.diffing.changelog_writer import render_changelog_markdown, write_changelog

__all__ = ["write_changelog", "render_changelog_markdown"]
