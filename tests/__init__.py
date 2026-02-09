"""Test package initialization."""

import docusynthetic


def test_version() -> None:
    """Test that version is set."""
    assert hasattr(docusynthetic, "__version__")
    assert docusynthetic.__version__ == "0.1.0"
