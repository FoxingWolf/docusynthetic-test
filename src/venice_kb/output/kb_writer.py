"""Write knowledge_base/ directory tree."""

from pathlib import Path
from venice_kb.utils.logging import logger


def write_kb_page(output_dir: Path, page_path: str, content: str) -> Path:
    """Write a single KB page to the output directory.
    
    Args:
        output_dir: Base output directory
        page_path: Page path (e.g., "api-reference/endpoints/chat")
        content: Markdown content
        
    Returns:
        Path to written file
    """
    # Ensure .md extension
    if not page_path.endswith(".md"):
        page_path = f"{page_path}.md"
    
    file_path = output_dir / page_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    
    logger.debug(f"Wrote: {file_path}")
    return file_path


def write_kb_directory(output_dir: Path, pages: dict[str, str]) -> list[Path]:
    """Write all KB pages to the output directory.
    
    Args:
        output_dir: Base output directory
        pages: Dictionary mapping paths to content
        
    Returns:
        List of written file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []
    
    for page_path, content in pages.items():
        file_path = write_kb_page(output_dir, page_path, content)
        written_files.append(file_path)
    
    logger.info(f"Wrote {len(written_files)} pages to {output_dir}")
    return written_files
