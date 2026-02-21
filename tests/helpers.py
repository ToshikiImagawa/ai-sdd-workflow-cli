"""Shared test helpers for SDD CLI tests."""

from pathlib import Path
from typing import Any, Optional

from sdd_cli.types import DocumentInfo, ParsedDocument


def write_md(
    path: Path,
    frontmatter: Optional[dict[str, Any]] = None,
    body: str = "",
) -> Path:
    """Write a Markdown file with optional YAML frontmatter.

    Args:
        path: Destination file path (parent dirs created automatically).
        frontmatter: Dict to serialise as YAML frontmatter.
        body: Markdown body text.

    Returns:
        The written Path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if frontmatter:
        lines.append("---")
        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
    lines.append(body)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def sample_doc_info(
    file_path: str = "requirement/auth/index.md",
    file_name: str = "index",
    directory: str = "requirement",
) -> DocumentInfo:
    """Create a minimal doc_info dict expected by IndexDB.index_document."""
    return DocumentInfo(
        file_path=file_path,
        file_name=file_name,
        directory=directory,
    )


def sample_parsed_data(
    title: str = "Auth Feature",
    feature_id: str = "auth",
    file_type: str = "requirement",
    parent_feature_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    depends_on: Optional[list[str]] = None,
    content: str = "Authentication feature content.",
    links: Optional[list[str]] = None,
) -> ParsedDocument:
    """Create a parsed_data dict expected by IndexDB.index_document."""
    return ParsedDocument(
        title=title,
        feature_id=feature_id,
        file_type=file_type,
        parent_feature_id=parent_feature_id,
        tags=tags or [],
        depends_on=depends_on or [],
        content=content,
        links=links or [],
    )
