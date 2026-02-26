"""TypedDict definitions for SDD CLI data structures."""

from pathlib import Path
from typing import Optional, TypedDict


class DocumentInfo(TypedDict):
    """Basic document information passed from Scanner to DB"""

    file_path: str
    file_name: str
    directory: str


class ScanResult(DocumentInfo):
    """Result returned by Scanner. Extended type that includes full_path"""

    full_path: Path


class ParsedDocument(TypedDict):
    """Return value of Parser.parse()"""

    # Existing fields
    title: str
    feature_id: str  # "document-indexing" (for backward compatibility)
    file_type: str
    parent_feature_id: Optional[str]
    tags: list[str]
    depends_on: list[str]
    content: str
    links: list[str]

    # New fields (AI-SDD common fields)
    id: str  # "prd-document-indexing"
    type: Optional[str]  # "prd" | "spec" | "design" | "task"
    status: Optional[str]  # "draft" | "review" | "approved" | "deprecated"
    created: Optional[str]  # "YYYY-MM-DD"
    updated: Optional[str]  # "YYYY-MM-DD"
    category: Optional[str]


class DocumentRecord(TypedDict):
    """Return value of DB.get_all_documents(). Also passed to analyzer."""

    # Existing fields
    file_path: str
    file_name: str
    directory: str
    file_type: str
    title: str
    feature_id: str  # "document-indexing" (for backward compatibility)
    parent_feature_id: Optional[str]
    tags: list[str]
    depends_on: list[str]
    links: list[str]

    # New fields (AI-SDD common fields)
    id: str  # "prd-document-indexing"
    type: Optional[str]
    status: Optional[str]
    created: Optional[str]
    updated: Optional[str]
    category: Optional[str]


class SearchResult(TypedDict):
    """Return value of DB.search()"""

    # Existing fields
    file_path: str
    file_name: str
    directory: str
    file_type: str
    title: str
    feature_id: str  # "document-indexing" (for backward compatibility)
    parent_feature_id: Optional[str]
    tags: list[str]
    snippet: Optional[str]

    # New fields (AI-SDD common fields)
    id: str  # "prd-document-indexing"
    type: Optional[str]
    status: Optional[str]
    created: Optional[str]
    updated: Optional[str]
    category: Optional[str]


class GraphNode(TypedDict):
    """Node in dependency graph"""

    id: str
    title: str
    directory: str
    file_type: str
    feature_id: str
    links: list[str]


class GraphEdge(TypedDict):
    """Edge in dependency graph"""

    source: str
    target: str
    type: str


class DependencyGraph(TypedDict):
    """Complete dependency graph"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SDDDirectories(TypedDict):
    """SDD directory configuration"""

    requirement: str
    specification: str
    task: str


class SDDConfig(TypedDict):
    """SDD configuration (.sdd-config.json schema)"""

    root: str
    lang: str
    directories: SDDDirectories
