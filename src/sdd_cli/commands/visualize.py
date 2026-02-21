"""Visualize command implementation."""

import json
from pathlib import Path
from typing import Optional

from sdd_cli.cache import get_cache_dir
from sdd_cli.commands.index import build_index
from sdd_cli.indexer.db import IndexDB
from sdd_cli.types import DependencyGraph
from sdd_cli.visualizer.analyzer import DependencyAnalyzer
from sdd_cli.visualizer.server import start_server


def generate_visualization(
    root: Path,
    output: Path,
    filter_dir: Optional[str] = None,
    feature_id: Optional[str] = None,
) -> None:
    """Generate dependency graph visualization and start HTML viewer.

    Args:
        root: SDD root directory
        output: Output file path
        filter_dir: Filter by directory type
        feature_id: Filter by feature ID

    Raises:
        Exception: If visualization generation fails
    """
    # Check if index exists in XDG cache directory
    project_root = root.parent if root.name == ".sdd" else root
    cache_dir = get_cache_dir(project_root)
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
    analyzer = DependencyAnalyzer(documents, root)
    analyzer.analyze()

    # Get filtered dependency graph (single view)
    graph = analyzer.get_dependency_graph(
        filter_dir=filter_dir,
        feature_id=feature_id,
    )

    # Build graph metadata
    title = "SDD Dependency Graph"
    subtitle = "Interactive dependency graph visualization"
    if filter_dir:
        subtitle += f" (filtered by directory: {filter_dir})"
    if feature_id:
        subtitle += f" (filtered by feature: {feature_id})"

    # Build in-memory JSON data for the server
    json_data = {}
    json_data["dependency-graph.json"] = _build_graph_data(graph, title, subtitle)

    # If --output specifies a path, write to file
    if output:
        _write_graph_file(output, json_data["dependency-graph.json"])

    # Always generate split graphs (PRD-based and direct)
    prd_graph, direct_graph = analyzer.get_split_dependency_graphs(filter_dir=filter_dir)

    json_data["prd-based-graph.json"] = _build_graph_data(
        prd_graph,
        "PRD-Based Dependency Graph",
        "Documents with requirements (PRD)",
    )

    json_data["direct-graph.json"] = _build_graph_data(
        direct_graph,
        "Direct Dependency Graph",
        "Documents without requirements (without PRD)",
    )

    # Start HTML viewer with in-memory data
    start_server(json_data)


def _build_graph_data(graph: DependencyGraph, title: str, subtitle: str) -> bytes:
    """Build graph JSON data as bytes.

    Args:
        graph: Dependency graph data
        title: Graph title
        subtitle: Graph subtitle

    Returns:
        JSON-encoded bytes
    """
    graph_data = {
        "title": title,
        "subtitle": subtitle,
        "nodes": graph["nodes"],
        "edges": graph["edges"],
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
