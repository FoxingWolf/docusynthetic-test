"""Document processor for merging and deduplication."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from docusynthetic.models import (
    BuildState,
    ChangelogEntry,
    DocumentContent,
    KnowledgeBaseIndex,
    SeverityLevel,
)


class DocumentProcessor:
    """Processes and merges documentation from multiple sources."""

    def __init__(self, output_dir: Path):
        """Initialize document processor.

        Args:
            output_dir: Directory to output the knowledge base.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def merge_documents(self, documents: List[DocumentContent]) -> List[DocumentContent]:
        """Merge and deduplicate documents.

        Args:
            documents: List of documents from all sources.

        Returns:
            Merged and deduplicated list of documents.
        """
        # Group by content hash
        hash_to_docs: Dict[str, List[DocumentContent]] = {}
        for doc in documents:
            if doc.content_hash not in hash_to_docs:
                hash_to_docs[doc.content_hash] = []
            hash_to_docs[doc.content_hash].append(doc)

        # For each unique content, prefer certain sources
        merged_docs = []
        for content_hash, doc_group in hash_to_docs.items():
            # Priority: GITHUB_MDX > OPENAPI_SPEC > LIVE_SITE
            sorted_docs = sorted(
                doc_group,
                key=lambda d: (
                    0
                    if d.metadata.source.value == "github_mdx"
                    else 1 if d.metadata.source.value == "openapi_spec" else 2
                ),
            )
            merged_docs.append(sorted_docs[0])

        return merged_docs

    def generate_index(self, documents: List[DocumentContent]) -> KnowledgeBaseIndex:
        """Generate JSON index for the knowledge base.

        Args:
            documents: List of documents.

        Returns:
            Knowledge base index.
        """
        # Group documents by category
        categories: Dict[str, List[str]] = {}
        doc_entries = []

        for doc in documents:
            category = doc.metadata.category or "Uncategorized"
            if category not in categories:
                categories[category] = []

            # Create safe filename
            filename = self._create_filename(doc.metadata.title)
            categories[category].append(filename)

            # Add to document entries
            doc_entries.append(
                {
                    "title": doc.metadata.title,
                    "filename": filename,
                    "source": doc.metadata.source.value,
                    "category": category,
                    "tags": doc.metadata.tags,
                    "last_updated": doc.metadata.last_updated.isoformat(),
                }
            )

        return KnowledgeBaseIndex(
            version="0.1.0",
            generated_at=datetime.now(),
            total_documents=len(documents),
            documents=doc_entries,
            categories=categories,
        )

    def save_knowledge_base(
        self, documents: List[DocumentContent], index: KnowledgeBaseIndex
    ) -> None:
        """Save knowledge base to disk.

        Args:
            documents: List of documents to save.
            index: Knowledge base index.
        """
        kb_dir = self.output_dir / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        # Save each document as markdown
        for doc in documents:
            filename = self._create_filename(doc.metadata.title)
            file_path = kb_dir / f"{filename}.md"

            # Create frontmatter
            frontmatter = f"""---
title: {doc.metadata.title}
source: {doc.metadata.source.value}
source_url: {doc.metadata.source_url}
category: {doc.metadata.category or 'Uncategorized'}
tags: {', '.join(doc.metadata.tags)}
last_updated: {doc.metadata.last_updated.isoformat()}
---

"""
            content = frontmatter + doc.content

            file_path.write_text(content, encoding="utf-8")

        # Save index
        index_path = self.output_dir / "index.json"
        index_path.write_text(
            index.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
        )

    def detect_changes(
        self, previous_state: Optional[BuildState], current_documents: List[DocumentContent]
    ) -> List[ChangelogEntry]:
        """Detect changes between builds.

        Args:
            previous_state: Previous build state.
            current_documents: Current documents.

        Returns:
            List of changelog entries.
        """
        if not previous_state:
            return [
                ChangelogEntry(
                    severity=SeverityLevel.INFO,
                    title="Initial build",
                    description="First build of the knowledge base",
                    affected_paths=["*"],
                )
            ]

        changes = []
        current_hashes = {doc.metadata.title: doc.content_hash for doc in current_documents}
        previous_hashes = previous_state.content_hashes

        # Detect new documents
        new_docs = set(current_hashes.keys()) - set(previous_hashes.keys())
        for doc_title in new_docs:
            changes.append(
                ChangelogEntry(
                    severity=SeverityLevel.INFO,
                    title=f"New document: {doc_title}",
                    description=f"Added new documentation page: {doc_title}",
                    affected_paths=[doc_title],
                )
            )

        # Detect removed documents
        removed_docs = set(previous_hashes.keys()) - set(current_hashes.keys())
        for doc_title in removed_docs:
            changes.append(
                ChangelogEntry(
                    severity=SeverityLevel.BREAKING,
                    title=f"Removed document: {doc_title}",
                    description=f"Documentation page removed: {doc_title}",
                    affected_paths=[doc_title],
                )
            )

        # Detect modified documents
        for doc_title in set(current_hashes.keys()) & set(previous_hashes.keys()):
            if current_hashes[doc_title] != previous_hashes[doc_title]:
                # Determine severity (simplified logic)
                severity = self._determine_change_severity(doc_title)
                changes.append(
                    ChangelogEntry(
                        severity=severity,
                        title=f"Updated: {doc_title}",
                        description=f"Documentation page updated: {doc_title}",
                        affected_paths=[doc_title],
                    )
                )

        return changes

    def save_changelog(self, changes: List[ChangelogEntry]) -> None:
        """Save changelog to disk.

        Args:
            changes: List of changelog entries.
        """
        if not changes:
            return

        changelog_path = self.output_dir / "CHANGELOG.md"

        # Create changelog markdown
        changelog_content = f"# Changelog\n\nGenerated: {datetime.now().isoformat()}\n\n"

        # Group by severity
        for severity in [SeverityLevel.BREAKING, SeverityLevel.IMPORTANT, SeverityLevel.INFO]:
            severity_changes = [c for c in changes if c.severity == severity]
            if severity_changes:
                changelog_content += f"\n## {severity.value.upper()}\n\n"
                for change in severity_changes:
                    changelog_content += f"- **{change.title}**: {change.description}\n"

        changelog_path.write_text(changelog_content, encoding="utf-8")

        # Also save as JSON
        changelog_json_path = self.output_dir / "changelog.json"
        changelog_json = [change.model_dump(mode="json") for change in changes]
        changelog_json_path.write_text(json.dumps(changelog_json, indent=2), encoding="utf-8")

    def save_state(self, documents: List[DocumentContent], index: KnowledgeBaseIndex) -> None:
        """Save current build state.

        Args:
            documents: Current documents.
            index: Current index.
        """
        state = BuildState(
            version="0.1.0",
            timestamp=datetime.now(),
            documents=documents,
            index=index,
            content_hashes={doc.metadata.title: doc.content_hash for doc in documents},
        )

        state_path = self.output_dir / "state.json"
        state_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def load_previous_state(self) -> Optional[BuildState]:
        """Load previous build state.

        Returns:
            Previous build state or None if not found.
        """
        state_path = self.output_dir / "state.json"
        if not state_path.exists():
            return None

        try:
            state_data = json.loads(state_path.read_text(encoding="utf-8"))
            return BuildState(**state_data)
        except Exception:
            return None

    def _create_filename(self, title: str) -> str:
        """Create safe filename from title.

        Args:
            title: Document title.

        Returns:
            Safe filename.
        """
        # Remove special characters and replace spaces with hyphens
        safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
        safe_name = safe_name.replace(" ", "-").lower()
        # Limit length
        return safe_name[:100]

    def _determine_change_severity(self, doc_title: str) -> SeverityLevel:
        """Determine severity of a change (simplified).

        Args:
            doc_title: Document title.

        Returns:
            Severity level.
        """
        # Simplified logic: consider API endpoint changes as important
        if any(
            keyword in doc_title.lower()
            for keyword in ["api", "endpoint", "breaking", "deprecated"]
        ):
            return SeverityLevel.IMPORTANT
        return SeverityLevel.INFO
