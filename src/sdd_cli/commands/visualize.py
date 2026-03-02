"""Visualize command implementation."""

from __future__ import annotations

import json
from pathlib import Path

from sdd_cli.cache import get_cache_dir
from sdd_cli.commands.index import build_index
from sdd_cli.config import resolve_sdd_root
from sdd_cli.indexer.db import IndexDB
from sdd_cli.linter.core import group_issues_by_file, run_lint_issues
from sdd_cli.types import DependencyGraph, LintIssue
from sdd_cli.visualizer.analyzer import DependencyAnalyzer
from sdd_cli.visualizer.graph_builder import GraphBuilder
from sdd_cli.visualizer.server import start_server


def generate_visualization(
    root: Path,
    output: Path,
    filter_dir: str | None = None,
    feature_id: str | None = None,
) -> None:
    """Generate dependency graph visualization and start HTML viewer.

    Args:
        root: Project root directory
        output: Output file path
        filter_dir: Filter by directory type
        feature_id: Filter by feature ID

    Raises:
        Exception: If visualization generation fails
    """
    # Check if index exists in XDG cache directory
    cache_dir = get_cache_dir(root)
    db_path = cache_dir / "index.db"
    if not db_path.exists():
        # Auto-generate index if it doesn't exist
        print("Index not found. Generating index...")
        build_index(root, quiet=False)
        print()

    # Get all documents from index
    with IndexDB(db_path) as db:
        documents = db.get_all_documents()

    if not documents:
        raise ValueError("No documents found in index.")

    # Analyze dependencies
    sdd_root = resolve_sdd_root(root)
    analyzer = DependencyAnalyzer(documents, sdd_root)
    deps = analyzer.analyze()
    builder = GraphBuilder(documents, deps, analyzer)

    # Get filtered dependency graph (single view)
    graph = builder.build_dependency_graph(
        filter_dir=filter_dir,
        feature_id=feature_id,
    )

    # Run lint checks (graceful failure: lint is supplementary info)
    lint_issues_by_file: dict[str, list[LintIssue]] = {}
    try:
        lint_result = run_lint_issues(root)
        lint_issues_by_file = group_issues_by_file(lint_result["issues"])
    except Exception:
        pass

    # Build graph metadata
    title = "SDD Dependency Graph"
    subtitle = "Interactive dependency graph visualization"
    if filter_dir:
        subtitle += f" (filtered by directory: {filter_dir})"
    if feature_id:
        subtitle += f" (filtered by feature: {feature_id})"

    # Build in-memory JSON data for the server
    json_data = {}
    json_data["dependency-graph.json"] = _build_graph_data(graph, title, subtitle, lint_issues_by_file)

    # If --output specifies a path, write to file
    if output:
        _write_graph_file(output, json_data["dependency-graph.json"])

    # Always generate split graphs (PRD-based and direct)
    prd_graph, direct_graph = builder.build_split_dependency_graphs(filter_dir=filter_dir)

    json_data["prd-based-graph.json"] = _build_graph_data(
        prd_graph,
        "PRD-Based Dependency Graph",
        "Documents with requirements (PRD)",
        lint_issues_by_file,
    )

    json_data["direct-graph.json"] = _build_graph_data(
        direct_graph,
        "Direct Dependency Graph",
        "Documents without requirements (without PRD)",
        lint_issues_by_file,
    )

    # Start HTML viewer with in-memory data
    start_server(json_data)


def _build_graph_data(
    graph: DependencyGraph,
    title: str,
    subtitle: str,
    lint_issues_by_file: dict[str, list[LintIssue]] | None = None,
) -> bytes:
    """Build graph JSON data as bytes.

    Args:
        graph: Dependency graph data
        title: Graph title
        subtitle: Graph subtitle
        lint_issues_by_file: Lint issues grouped by file path

    Returns:
        JSON-encoded bytes
    """
    # Build lintIssues: only include serializable fields
    lint_issues_json: dict[str, list] = {}
    if lint_issues_by_file:
        for file_path, issues in lint_issues_by_file.items():
            lint_issues_json[file_path] = [
                {
                    "severity": issue["severity"],
                    "rule": issue["rule"],
                    "message": issue["message"],
                    "line": issue.get("line"),
                }
                for issue in issues
            ]

    graph_data = {
        "title": title,
        "subtitle": subtitle,
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "lintIssues": lint_issues_json,
    }
    return json.dumps(graph_data, indent=2, ensure_ascii=False).encode("utf-8")


def _write_graph_file(output: Path, data: bytes):
    """Write graph data to file (for --output option).

    Args:
        output: Output file path
        data: JSON bytes to write
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output = output.parent / f"{output.stem}.json"
    json_output.write_bytes(data)
