"""Search command implementation (Phase 2)."""

import json
from pathlib import Path
from typing import Optional

from sdd_cli.cache import get_cache_dir
from sdd_cli.indexer.db import IndexDB
from sdd_cli.types import FilterCondition, MatchOp, SearchResult

_VALID_OPS: tuple[MatchOp, ...] = ("exact", "contains", "regex")


def _parse_filter(filter_str: str) -> FilterCondition:
    """Parse "field:op:value" string into a FilterCondition.

    Raises:
        ValueError: If the format is not "field:op:value" or op is invalid.
    """
    parts = filter_str.split(":", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid filter format: '{filter_str}'. Expected 'field:op:value' (op: exact/contains/regex)")
    field, op_str, value = parts
    if op_str not in _VALID_OPS:
        raise ValueError(f"Invalid filter op: '{op_str}'. Must be one of: exact, contains, regex")
    op: MatchOp = op_str  # type: ignore[assignment]
    return FilterCondition(field=field, op=op, value=value)


def search_documents(
    root: Path,
    query: Optional[str] = None,
    feature_id: Optional[str] = None,
    tag: Optional[str] = None,
    directory: Optional[str] = None,
    filters: Optional[list[FilterCondition]] = None,
    or_operator: bool = False,
    parent: Optional[str] = None,
    output_format: str = "text",
    limit: int = 10,
) -> str:
    """Search SDD documents.

    Args:
        root: Project root directory
        query: Full-text search query
        feature_id: Filter by feature ID
        tag: Filter by tag
        directory: Filter by directory type
        filters: List of DSL filter conditions
        or_operator: If True, combine filters with OR
        parent: Retrieve all descendants of this feature_id
        output_format: Output format (text or json)
        limit: Maximum number of results

    Returns:
        Formatted search results

    Raises:
        ValueError: If index not found or filter is invalid
    """
    # Check if index exists in XDG cache directory
    cache_dir = get_cache_dir(root)
    db_path = cache_dir / "index.db"
    if not db_path.exists():
        raise ValueError(f"Index not found at {db_path}. Please run 'sdd-cli index' first.")

    # Search database
    with IndexDB(db_path) as db:
        results = db.search(
            query=query,
            feature_id=feature_id,
            tag=tag,
            directory=directory,
            filters=filters,
            or_operator=or_operator,
            parent=parent,
            limit=limit,
        )

    # Format output
    if output_format == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)
    else:
        return _format_text_results(results, query)


def _format_text_results(results: list[SearchResult], query: Optional[str]) -> str:
    """Format search results as text.

    Args:
        results: List of search results
        query: Original search query

    Returns:
        Formatted text output
    """
    if not results:
        return "No results found."

    lines = []
    lines.append(f"Found {len(results)} result(s)")
    if query:
        lines.append(f"Query: {query}")
    lines.append("")

    for i, result in enumerate(results, 1):
        lines.append(f"{i}. {result['title']}")
        lines.append(f"   Path: {result['file_path']}")
        lines.append(f"   Feature ID: {result['feature_id']}")

        if result.get("tags"):
            tags_str = ", ".join(result["tags"])
            lines.append(f"   Tags: {tags_str}")

        snippet = result.get("snippet")
        if snippet:
            lines.append(f"   Snippet: {snippet.replace(chr(10), ' ')}")

        lines.append("")

    return "\n".join(lines)
