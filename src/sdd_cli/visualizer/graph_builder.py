"""Graph builder for SDD dependency visualization."""

from typing import TYPE_CHECKING, Optional

from sdd_cli.types import DependencyGraph, DocumentRecord, GraphEdge, GraphNode

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
        graph = self._build_graph_from_docs(filtered_docs, include_constitution=True)
        self._add_constitution_edges(graph, filtered_docs, {"requirement", "spec"})
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
        # Filter documents
        filtered_docs = self.documents
        if filter_dir:
            filtered_docs = [d for d in filtered_docs if d["directory"] == filter_dir]

        # Separate documents by PRD existence
        prd_based_docs = []
        direct_docs = []

        # First pass: classify requirements and specs
        spec_classification: dict[str, str] = {}  # feature_id -> "prd" or "direct"

        for doc in filtered_docs:
            file_type = doc.get("file_type", "")
            feat_id = doc.get("feature_id", "")

            if file_type == "requirement":
                # All requirements go to PRD-based graph
                prd_based_docs.append(doc)
            elif file_type == "spec":
                # Spec docs: check if corresponding requirement exists
                has_requirement = self._has_requirement(feat_id)
                if has_requirement:
                    # Has requirement -> PRD-based graph
                    prd_based_docs.append(doc)
                    spec_classification[feat_id] = "prd"
                else:
                    # No requirement -> Direct graph (from CONSTITUTION)
                    direct_docs.append(doc)
                    spec_classification[feat_id] = "direct"
            elif file_type == "task":
                # Task docs: classify based on link targets
                # If any link resolves to a requirement or PRD-classified spec, it's PRD-based
                task_is_prd = self._task_has_prd_link(doc, spec_classification)
                if task_is_prd:
                    prd_based_docs.append(doc)
                else:
                    direct_docs.append(doc)

        # Second pass: classify design docs based on their spec's classification
        for doc in filtered_docs:
            file_type = doc.get("file_type", "")
            feat_id = doc.get("feature_id", "")

            if file_type == "design":
                # Design docs: follow their spec's classification
                # Check if we classified the corresponding spec
                if feat_id in spec_classification:
                    if spec_classification[feat_id] == "prd":
                        prd_based_docs.append(doc)
                    else:
                        direct_docs.append(doc)
                else:
                    # No spec found, check if spec exists at all
                    has_spec = self._has_spec(feat_id)
                    if has_spec:
                        # Spec exists but wasn't classified (shouldn't happen)
                        prd_based_docs.append(doc)
                    else:
                        # No spec -> Direct graph (from CONSTITUTION)
                        direct_docs.append(doc)

        # Build PRD-based graph
        prd_graph = self._build_graph_from_docs(prd_based_docs, include_constitution=True)
        self._add_constitution_edges(prd_graph, prd_based_docs, {"requirement"})

        # Build direct graph (CONSTITUTION -> specs without PRD)
        direct_graph = self._build_graph_from_docs(direct_docs, include_constitution=True)
        self._add_constitution_edges(direct_graph, direct_docs, {"spec"})

        return prd_graph, direct_graph

    def _build_graph_from_docs(
        self,
        docs: list[DocumentRecord],
        include_constitution: bool = False,
    ) -> DependencyGraph:
        """Build graph from filtered documents.

        Args:
            docs: List of document metadata
            include_constitution: Whether to include CONSTITUTION node

        Returns:
            Dictionary with nodes and edges
        """
        if not docs:
            return DependencyGraph(nodes=[], edges=[])

        # Extract filtered paths
        filtered_paths = {doc["file_path"] for doc in docs}

        # Add CONSTITUTION if requested
        if include_constitution:
            filtered_paths.add("CONSTITUTION.md")

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

        # Add CONSTITUTION node if requested
        if include_constitution:
            nodes.insert(
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

    def _add_constitution_edges(
        self,
        graph: DependencyGraph,
        docs: list[DocumentRecord],
        file_types: set[str],
    ) -> None:
        """Add implicit CONSTITUTION edges for top-level nodes without incoming edges.

        Args:
            graph: Graph dict to modify in-place
            docs: Documents to check
            file_types: Set of file_type values eligible for CONSTITUTION edges
        """
        # Only count implicit edges as hierarchy incoming
        # Parent-Child or file-type-order implicit edges indicate the node already has a parent
        nodes_with_incoming = {edge["target"] for edge in graph["edges"] if edge["type"] == "implicit"}
        for doc in docs:
            if doc.get("file_type") in file_types and doc["file_path"] not in nodes_with_incoming:
                graph["edges"].append(
                    GraphEdge(
                        source="CONSTITUTION.md",
                        target=doc["file_path"],
                        type="implicit",
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
            resolved = self.analyzer._resolve_relative_link(doc["file_path"], link)
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
