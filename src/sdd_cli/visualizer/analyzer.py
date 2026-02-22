"""Dependency analyzer for SDD documents."""

from pathlib import Path
from typing import Optional

from sdd_cli.types import DocumentRecord


class DependencyAnalyzer:
    """Analyzes dependencies between SDD documents."""

    def __init__(self, documents: list[DocumentRecord], root: Path):
        """Initialize analyzer with document list.

        Args:
            documents: List of document metadata from IndexDB
            root: SDD root directory
        """
        self.documents = documents
        self.root = root
        self.dependencies: list[tuple[str, str, str]] = []

    def analyze(self) -> list[tuple[str, str, str]]:
        """Analyze all dependencies.

        Returns:
            List of (source, target, link_type) tuples where:
                - source: Source document path
                - target: Target document path
                - link_type: Type of dependency (explicit/implicit/link)
        """
        self.dependencies = []

        for doc in self.documents:
            file_path = doc["file_path"]

            # 1. Explicit dependencies from frontmatter
            if doc.get("depends_on"):
                for dep in doc["depends_on"]:
                    target = self._resolve_feature_id_to_path(dep)
                    if target:
                        self.dependencies.append((file_path, target, "explicit"))

            # 2. Implicit dependencies based on naming convention
            implicit_deps = self._infer_implicit_dependencies(doc)
            for target in implicit_deps:
                self.dependencies.append((file_path, target, "implicit"))

            # 3. Parent-child nesting (parent -> child direction)
            parent_feature_id = doc.get("parent_feature_id")
            if parent_feature_id:
                parent_doc = self._find_document_by_feature_id(parent_feature_id, doc.get("file_type", ""))
                if parent_doc:
                    self.dependencies.append((parent_doc["file_path"], file_path, "implicit"))

            # 4. Dependencies from markdown links (task files only)
            # Task files use links to reference their parent spec/requirement docs.
            # Only keep edges to the deepest nodes in the dependency chain.
            if doc.get("file_type") == "task" and doc.get("links"):
                targets = []
                for link in doc["links"]:
                    target = self._resolve_relative_link(file_path, link)
                    if target:
                        targets.append(target)
                # Filter to leaf targets only
                leaf_targets = self._filter_to_leaf_targets(targets)
                for target in leaf_targets:
                    self.dependencies.append((file_path, target, "link"))

        return self.dependencies

    def _filter_to_leaf_targets(self, targets: list[str]) -> list[str]:
        """Filter targets to keep only leaf nodes (deepest in dependency chain).

        If A -> B -> C are all in targets, only C is kept.
        """
        if len(targets) <= 1:
            return list(set(targets))

        target_set = set(targets)
        ancestors = set()

        for target in target_set:
            # BFS from this target through existing implicit/explicit dependencies
            visited = set()
            queue = [target]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for src, tgt, link_type in self.dependencies:
                    if src == current and link_type in ("implicit", "explicit"):
                        if tgt in target_set and tgt != target:
                            ancestors.add(target)
                        queue.append(tgt)

        return [t for t in set(targets) if t not in ancestors]

    def _resolve_feature_id_to_path(self, feature_id: str) -> Optional[str]:
        """Resolve feature ID to document path.

        Args:
            feature_id: Feature ID to resolve

        Returns:
            Document path or None if not found
        """
        for doc in self.documents:
            if doc.get("feature_id") == feature_id:
                return doc["file_path"]
        return None

    def _infer_implicit_dependencies(self, doc: DocumentRecord) -> list[str]:
        """Infer implicit dependencies based on file type and feature ID.

        Dependency flow:
            CONSTITUTION -> requirement -> spec -> design -> task

        Args:
            doc: Document metadata

        Returns:
            List of inferred dependency paths
        """
        deps = []
        file_type = doc.get("file_type", "")
        feature_id = doc.get("feature_id", "")

        # Pattern 1: requirement -> spec (if spec exists)
        if file_type == "requirement":
            spec_doc = self._find_document_by_feature_id(feature_id, "spec")
            if spec_doc:
                deps.append(spec_doc["file_path"])

        # Pattern 2: spec -> design (if design exists)
        elif file_type == "spec":
            design_doc = self._find_document_by_feature_id(feature_id, "design")
            if design_doc:
                deps.append(design_doc["file_path"])

        # Pattern 3: design -> task (if task exists with same feature_id)
        elif file_type == "design":
            for task_doc in self.documents:
                if task_doc.get("file_type") == "task" and task_doc.get("feature_id") == feature_id:
                    deps.append(task_doc["file_path"])

        return deps

    def _resolve_relative_link(self, source_path: str, link: str) -> Optional[str]:
        """Resolve relative markdown link to absolute path.

        Args:
            source_path: Source document path
            link: Relative link

        Returns:
            Resolved document path or None
        """
        # 1. Try file-relative resolution (for ../../path/to/file.md)
        try:
            source_dir = self.root / Path(source_path).parent
            target_path = (source_dir / link).resolve()
            rel_path = target_path.relative_to(self.root)
            rel_path_str = str(rel_path)

            if self._document_exists(rel_path_str):
                return rel_path_str
        except (ValueError, OSError):
            pass

        # 2. Try root-relative resolution (for backtick paths like specification/xxx.md)
        if self._document_exists(link):
            return link

        return None

    def _document_exists(self, path: str) -> bool:
        """Check if document exists in the indexed documents.

        Args:
            path: Document path to check

        Returns:
            True if document exists
        """
        return any(doc["file_path"] == path for doc in self.documents)

    def _find_document_by_feature_id(self, feature_id: str, file_type: str) -> Optional[DocumentRecord]:
        """Find document by feature ID and file type.

        Args:
            feature_id: Feature ID to search
            file_type: File type to match (requirement/spec/design/task)

        Returns:
            Document metadata or None if not found
        """
        for doc in self.documents:
            if doc.get("feature_id") == feature_id and doc.get("file_type") == file_type:
                return doc
        return None
