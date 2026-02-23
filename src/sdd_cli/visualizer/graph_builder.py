"""Graph builder for SDD dependency visualization."""

from typing import TYPE_CHECKING, Optional

from sdd_cli.types import DependencyGraph, DocumentRecord, GraphEdge, GraphNode
from sdd_cli.visualizer.analyzer import EDGE_CONSTITUTION

if TYPE_CHECKING:
    from sdd_cli.visualizer.analyzer import DependencyAnalyzer


class GraphBuilder:
    """Builds structured graph data from documents and dependencies."""

    def __init__(
        self,
        documents: list[DocumentRecord],
        dependencies: list[tuple[str, str, str]],
        analyzer: "DependencyAnalyzer",
    ):
        """Initialize builder.

        Args:
            documents: List of document metadata from IndexDB
            dependencies: List of (source, target, link_type) tuples from analyzer
            analyzer: DependencyAnalyzer instance for link resolution
        """
        self.documents = documents
        self.dependencies = dependencies
        self.analyzer = analyzer

    def build_dependency_graph(
        self,
        filter_dir: Optional[str] = None,
        feature_id: Optional[str] = None,
    ) -> DependencyGraph:
        """Build dependency graph as structured data.

        Args:
            filter_dir: Filter by directory type
            feature_id: Filter by feature ID

        Returns:
            Dictionary with nodes and edges
        """
        filtered_docs = self.documents
        if filter_dir:
            filtered_docs = [d for d in filtered_docs if d["directory"] == filter_dir]
        if feature_id:
            filtered_docs = [d for d in filtered_docs if d.get("feature_id") == feature_id]
        graph = self._build_graph_from_docs(filtered_docs)
        self._attach_constitution(graph, filtered_docs, {"requirement", "spec", "task"})
        return graph

    def build_split_dependency_graphs(
        self,
        filter_dir: Optional[str] = None,
    ) -> tuple[DependencyGraph, DependencyGraph]:
        """Build dependency graphs split by PRD existence.

        Args:
            filter_dir: Filter by directory type

        Returns:
            Tuple of (prd_based_graph, direct_graph) where:
                - prd_based_graph: Documents with requirements (PRD)
                - direct_graph: Documents without requirements (direct from CONSTITUTION)
        """
        filtered_docs = self.documents
        if filter_dir:
            filtered_docs = [d for d in filtered_docs if d["directory"] == filter_dir]

        prd_based_docs, direct_docs = self._classify_documents(filtered_docs)

        prd_graph = self._build_graph_from_docs(prd_based_docs)
        self._attach_constitution(prd_graph, prd_based_docs, {"requirement", "task"})

        direct_graph = self._build_graph_from_docs(direct_docs)
        self._attach_constitution(direct_graph, direct_docs, {"spec", "task"})

        return prd_graph, direct_graph

    def _classify_documents(self, docs: list[DocumentRecord]) -> tuple[list[DocumentRecord], list[DocumentRecord]]:
        """Classify documents into PRD-based and direct groups.

        First pass: requirement/spec/task are classified.
        Second pass: design docs follow their spec's classification.

        Args:
            docs: Documents to classify

        Returns:
            Tuple of (prd_based_docs, direct_docs)
        """
        prd_based_docs: list[DocumentRecord] = []
        direct_docs: list[DocumentRecord] = []
        spec_classification: dict[str, str] = {}  # feature_id -> "prd" or "direct"

        # First pass: classify requirements, specs, and tasks
        for doc in docs:
            file_type = doc.get("file_type", "")
            feat_id = doc.get("feature_id", "")

            if file_type == "requirement":
                prd_based_docs.append(doc)
            elif file_type == "spec":
                if self._has_requirement(feat_id):
                    prd_based_docs.append(doc)
                    spec_classification[feat_id] = "prd"
                else:
                    direct_docs.append(doc)
                    spec_classification[feat_id] = "direct"
            elif file_type == "task":
                if self._task_has_prd_link(doc, spec_classification):
                    prd_based_docs.append(doc)
                else:
                    direct_docs.append(doc)

        # Second pass: classify design docs based on their spec's classification
        for doc in docs:
            file_type = doc.get("file_type", "")
            feat_id = doc.get("feature_id", "")

            if file_type == "design":
                if feat_id in spec_classification:
                    if spec_classification[feat_id] == "prd":
                        prd_based_docs.append(doc)
                    else:
                        direct_docs.append(doc)
                elif self._has_spec(feat_id):
                    prd_based_docs.append(doc)
                else:
                    direct_docs.append(doc)

        return prd_based_docs, direct_docs

    def _build_graph_from_docs(self, docs: list[DocumentRecord]) -> DependencyGraph:
        """Build graph from filtered documents.

        Args:
            docs: List of document metadata

        Returns:
            Dictionary with nodes and edges
        """
        if not docs:
            return DependencyGraph(nodes=[], edges=[])

        # Extract filtered paths
        filtered_paths = {doc["file_path"] for doc in docs}

        # Filter dependencies
        filtered_deps = [
            (src, tgt, link_type)
            for src, tgt, link_type in self.dependencies
            if src in filtered_paths and tgt in filtered_paths
        ]

        # Build graph
        nodes: list[GraphNode] = []
        for doc in docs:
            nodes.append(
                GraphNode(
                    id=doc["file_path"],
                    title=doc.get("title", doc["file_name"]),
                    directory=doc["directory"],
                    file_type=doc.get("file_type", ""),
                    feature_id=doc.get("feature_id", ""),
                    links=doc.get("links", []),
                )
            )

        edges: list[GraphEdge] = []
        for src, tgt, link_type in filtered_deps:
            edges.append(
                GraphEdge(
                    source=src,
                    target=tgt,
                    type=link_type,
                )
            )

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
        )

    def _attach_constitution(
        self,
        graph: DependencyGraph,
        docs: list[DocumentRecord],
        file_types: set[str],
    ) -> None:
        """Add CONSTITUTION node and implicit edges to the graph.

        Args:
            graph: Graph dict to modify in-place
            docs: Documents to check
            file_types: Set of file_type values eligible for CONSTITUTION edges
        """
        if not docs:
            return

        # Insert CONSTITUTION node
        graph["nodes"].insert(
            0,
            GraphNode(
                id="CONSTITUTION.md",
                title="CONSTITUTION.md",
                directory="",
                file_type="",
                feature_id="",
                links=[],
            ),
        )

        # Add constitution edges for top-level nodes (nodes that don't depend on anything).
        # Direction is doc → CONSTITUTION (child→parent, same as all other edges).
        nodes_with_parent = {edge["source"] for edge in graph["edges"]}
        for doc in docs:
            if doc.get("file_type") in file_types and doc["file_path"] not in nodes_with_parent:
                graph["edges"].append(
                    GraphEdge(
                        source=doc["file_path"],
                        target="CONSTITUTION.md",
                        type=EDGE_CONSTITUTION,
                    )
                )

    def _has_requirement(self, feature_id: str) -> bool:
        """Check if a feature has a corresponding requirement document.

        Args:
            feature_id: Feature ID to check

        Returns:
            True if requirement exists
        """
        for doc in self.documents:
            if doc.get("file_type") == "requirement" and doc.get("feature_id") == feature_id:
                return True
        return False

    def _task_has_prd_link(self, doc: DocumentRecord, spec_classification: dict[str, str]) -> bool:
        """Check if a task document links to any requirement or PRD-classified document.

        Args:
            doc: Task document metadata
            spec_classification: Classification map of feature_id -> "prd"/"direct"

        Returns:
            True if any link target is a requirement or PRD-classified spec
        """
        for link in doc.get("links", []):
            resolved = self.analyzer.resolve_link(doc["file_path"], link)
            if not resolved:
                continue
            target_doc = next((d for d in self.documents if d["file_path"] == resolved), None)
            if not target_doc:
                continue
            if target_doc.get("file_type") == "requirement":
                return True
            if (
                target_doc.get("feature_id") in spec_classification
                and spec_classification[target_doc["feature_id"]] == "prd"
            ):
                return True
        return False

    def _has_spec(self, feature_id: str) -> bool:
        """Check if a feature has a corresponding spec document.

        Args:
            feature_id: Feature ID to check

        Returns:
            True if spec exists
        """
        return any(doc.get("file_type") == "spec" and doc.get("feature_id") == feature_id for doc in self.documents)
