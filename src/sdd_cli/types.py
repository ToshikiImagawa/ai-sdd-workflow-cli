"""TypedDict definitions for SDD CLI data structures."""

from pathlib import Path
from typing import Optional, TypedDict


class DocumentInfo(TypedDict):
    """Scanner → DB に渡すドキュメント基本情報"""

    file_path: str
    file_name: str
    directory: str


class ScanResult(DocumentInfo):
    """Scanner が返す結果。full_path を含む拡張型"""

    full_path: Path


class ParsedDocument(TypedDict):
    """Parser.parse() の戻り値"""

    title: str
    feature_id: str
    file_type: str
    parent_feature_id: Optional[str]
    tags: list[str]
    depends_on: list[str]
    content: str
    links: list[str]


class DocumentRecord(TypedDict):
    """DB.get_all_documents() の戻り値。analyzer にも渡される"""

    file_path: str
    file_name: str
    directory: str
    file_type: str
    title: str
    feature_id: str
    parent_feature_id: Optional[str]
    tags: list[str]
    depends_on: list[str]
    links: list[str]


class SearchResult(TypedDict):
    """DB.search() の戻り値"""

    file_path: str
    file_name: str
    directory: str
    file_type: str
    title: str
    feature_id: str
    parent_feature_id: Optional[str]
    tags: list[str]
    snippet: Optional[str]


class GraphNode(TypedDict):
    """依存グラフのノード"""

    id: str
    title: str
    directory: str
    file_type: str
    feature_id: str


class GraphEdge(TypedDict):
    """依存グラフのエッジ"""

    source: str
    target: str
    type: str


class DependencyGraph(TypedDict):
    """依存グラフ全体"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
