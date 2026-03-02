"""Dependency analyzer for SDD documents."""

import re
from pathlib import Path
from typing import Optional

from sdd_cli.types import DocumentRecord

# --- File type constants ---
FILE_TYPE_REQUIREMENT = "requirement"
FILE_TYPE_SPEC = "spec"
FILE_TYPE_DESIGN = "design"
FILE_TYPE_TASK = "task"

# --- Type hierarchy (upstream → downstream) ---
TYPE_HIERARCHY = [FILE_TYPE_REQUIREMENT, FILE_TYPE_SPEC, FILE_TYPE_DESIGN, FILE_TYPE_TASK]

# --- Edge type constants ---
EDGE_EXPLICIT = "explicit"
EDGE_IMPLICIT = "implicit"
EDGE_LINK = "link"
EDGE_CONSTITUTION = "constitution"


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

        # Lookup dictionaries for O(1) access
        self._doc_by_key: dict[tuple[str, str], DocumentRecord] = {
            (doc["feature_id"], doc["file_type"]): doc for doc in documents
        }
        self._doc_paths: frozenset[str] = frozenset(doc["file_path"] for doc in documents)
        self._first_path_by_feature: dict[str, str] = {}
        for doc in documents:
            self._first_path_by_feature.setdefault(doc["feature_id"], doc["file_path"])

        # Full ID → feature_id mapping (e.g. "prd-auth" → "auth")
        self._full_id_to_feature_id: dict[str, str] = {}
        for doc in documents:
            full_id = doc.get("id", "")
            if full_id and full_id != doc["feature_id"]:
                self._full_id_to_feature_id[full_id] = doc["feature_id"]

    def analyze(self) -> list[tuple[str, str, str]]:
        """Analyze all dependencies.

        Returns:
            List of (source, target, link_type) tuples where:
                - source: Source document path
                - target: Target document path
                - link_type: Type of dependency (explicit/implicit/link)
        """
        self.dependencies = []

        # Pass 1: explicit + implicit + parent-child (all documents)
        # These must be fully populated before Pass 2, because _filter_to_leaf_targets
        # reads self.dependencies to determine ancestor relationships.
        for doc in self.documents:
            file_path = doc["file_path"]

            # 1. Explicit dependencies from frontmatter
            if doc.get("depends_on"):
                source_type = doc.get("file_type", "")
                for dep in doc["depends_on"]:
                    target = self._resolve_feature_id_to_path(dep, source_type)
                    if target:
                        self.dependencies.append((file_path, target, EDGE_EXPLICIT))

            # 2. Implicit dependencies based on naming convention
            implicit_deps = self._infer_implicit_dependencies(doc)
            for target in implicit_deps:
                self.dependencies.append((file_path, target, EDGE_IMPLICIT))

            # 3. Parent-child nesting (child → parent direction, same as other edges)
            parent_feature_id = doc.get("parent_feature_id")
            if parent_feature_id:
                parent_doc = self._find_document_by_feature_id(parent_feature_id, doc.get("file_type", ""))
                if parent_doc:
                    self.dependencies.append((file_path, parent_doc["file_path"], EDGE_IMPLICIT))

        # Pass 2: link edges (task documents only)
        # _filter_to_leaf_targets uses self.dependencies to BFS ancestor chains,
        # so it requires all explicit/implicit edges to be present.
        for doc in self.documents:
            if doc.get("file_type") != FILE_TYPE_TASK or not doc.get("links"):
                continue
            file_path = doc["file_path"]
            targets = []
            for link in doc["links"]:
                target = self._resolve_relative_link(file_path, link)
                if target:
                    targets.append(target)
            # Filter to leaf targets only
            leaf_targets = self._filter_to_leaf_targets(targets)
            for target in leaf_targets:
                self.dependencies.append((file_path, target, EDGE_LINK))

        # Post-processing
        self.dependencies = self._deduplicate_edges(self.dependencies)
        self.dependencies = self._remove_transitive_redundant_edges(self.dependencies)

        return self.dependencies

    def resolve_link(self, source_path: str, link: str) -> Optional[str]:
        """Resolve a relative markdown link to a document path.

        Args:
            source_path: Source document path
            link: Relative link to resolve

        Returns:
            Resolved document path or None if not found
        """
        return self._resolve_relative_link(source_path, link)

    @staticmethod
    def _deduplicate_edges(
        dependencies: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        """Deduplicate edges between same pair of nodes, keeping highest priority type.

        Treats (A→B) and (B→A) as the same relationship.
        Priority: explicit > implicit > link
        """
        priority = {EDGE_EXPLICIT: 0, EDGE_IMPLICIT: 1, EDGE_LINK: 2}
        best: dict[frozenset[str], tuple[str, str, str]] = {}
        for edge in dependencies:
            src, tgt, lt = edge
            key = frozenset((src, tgt))
            if key not in best or priority.get(lt, 99) < priority.get(best[key][2], 99):
                best[key] = edge
        return list(best.values())

    @staticmethod
    def _remove_transitive_redundant_edges(
        dependencies: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        """Remove link/explicit edges that are reachable through other edges.

        If A -> B (any edge) and B -> C (any edge), then A -> C (link or explicit) is redundant.
        Implicit and constitution edges are always preserved.
        """
        # Build adjacency map from all edges
        adjacency: dict[str, set[str]] = {}
        for src, tgt, _ in dependencies:
            adjacency.setdefault(src, set()).add(tgt)

        def is_reachable_without_direct(source: str, target: str) -> bool:
            """Check if target is reachable from source without the direct edge."""
            visited: set[str] = set()
            queue = list(adjacency.get(source, set()) - {target})
            while queue:
                current = queue.pop(0)
                if current == target:
                    return True
                if current in visited:
                    continue
                visited.add(current)
                queue.extend(adjacency.get(current, set()) - visited)
            return False

        return [
            (src, tgt, lt)
            for src, tgt, lt in dependencies
            if lt not in (EDGE_LINK, EDGE_EXPLICIT) or not is_reachable_without_direct(src, tgt)
        ]

    def _filter_to_leaf_targets(self, targets: list[str]) -> list[str]:
        """Filter targets to keep only leaf nodes (deepest in dependency chain).

        Edges are in child→parent direction. A target is an ancestor if
        another target depends on it (directly or transitively).
        If requirement and design are both targets, only design is kept.
        """
        if len(targets) <= 1:
            return list(set(targets))

        target_set = set(targets)
        ancestors = set()

        for target in target_set:
            # BFS: follow reverse edges (find who depends on this target)
            visited: set[str] = set()
            queue = [target]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for src, tgt, link_type in self.dependencies:
                    if tgt == current and link_type in (EDGE_IMPLICIT, EDGE_EXPLICIT):
                        if src in target_set and src != target:
                            ancestors.add(target)
                        queue.append(src)

        return [t for t in set(targets) if t not in ancestors]

    def _resolve_feature_id_to_path(self, feature_id: str, source_file_type: str = "") -> Optional[str]:
        """Resolve feature ID or full document ID to the nearest upstream document path.

        Accepts both feature_id (e.g. "auth") and full ID with prefix (e.g. "prd-auth").
        Uses the type hierarchy (requirement → spec → design → task) to find
        the closest ancestor type that has a document with the given feature_id.

        For example, if source is "design" and depends_on "auth":
          1. Look for auth spec (one level up) → found → return it
          2. If not found, look for auth requirement (two levels up)

        If source_file_type is not in the hierarchy, falls back to first match.

        Args:
            feature_id: Feature ID or full document ID to resolve
            source_file_type: File type of the source document

        Returns:
            Document path or None if not found
        """
        # Normalize: if given a full ID (e.g. "prd-auth"), convert to feature_id
        resolved_id = self._normalize_to_feature_id(feature_id)

        if source_file_type in TYPE_HIERARCHY:
            source_idx = TYPE_HIERARCHY.index(source_file_type)
            # Search upward from direct parent type
            for i in range(source_idx - 1, -1, -1):
                doc = self._find_document_by_feature_id(resolved_id, TYPE_HIERARCHY[i])
                if doc:
                    return doc["file_path"]

        # Fallback: first match (for same-level deps or unknown types)
        return self._first_path_by_feature.get(resolved_id)

    def _infer_implicit_dependencies(self, doc: DocumentRecord) -> list[str]:
        """Infer implicit dependencies based on file type and feature ID.

        Each document depends on its upstream type (child → parent direction):
            design -> spec -> requirement
        Note: task is excluded from implicit dependencies (connected via link edges only)

        Args:
            doc: Document metadata

        Returns:
            List of inferred dependency paths (upstream documents this doc depends on)
        """
        deps = []
        file_type = doc.get("file_type", "")
        feature_id = doc.get("feature_id", "")

        # Pattern 1: spec depends on requirement
        if file_type == FILE_TYPE_SPEC:
            req_doc = self._find_document_by_feature_id(feature_id, FILE_TYPE_REQUIREMENT)
            if req_doc:
                deps.append(req_doc["file_path"])

        # Pattern 2: design depends on spec
        elif file_type == FILE_TYPE_DESIGN:
            spec_doc = self._find_document_by_feature_id(feature_id, FILE_TYPE_SPEC)
            if spec_doc:
                deps.append(spec_doc["file_path"])

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
            rel_path = target_path.relative_to(self.root.resolve())
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
        return path in self._doc_paths

    def _find_document_by_feature_id(self, feature_id: str, file_type: str) -> Optional[DocumentRecord]:
        """Find document by feature ID and file type.

        Args:
            feature_id: Feature ID to search
            file_type: File type to match (requirement/spec/design/task)

        Returns:
            Document metadata or None if not found
        """
        return self._doc_by_key.get((feature_id, file_type))

    # Common AI-SDD ID prefixes (same as parser._extract_feature_id)
    _ID_PREFIX_PATTERN = re.compile(r"^(prd|spec|design|task|impl)-")

    def _normalize_to_feature_id(self, raw_id: str) -> str:
        """Normalize a full document ID or feature_id to a feature_id.

        First checks the full_id→feature_id mapping built from actual documents.
        Falls back to stripping known AI-SDD prefixes (prd-, spec-, design-, task-, impl-).

        Args:
            raw_id: Full document ID (e.g. "prd-auth") or feature_id (e.g. "auth")

        Returns:
            Normalized feature_id
        """
        # 1. Try exact mapping from existing documents
        if raw_id in self._full_id_to_feature_id:
            return self._full_id_to_feature_id[raw_id]

        # 2. If already a known feature_id, return as-is
        if raw_id in self._first_path_by_feature:
            return raw_id

        # 3. Try stripping common prefixes
        stripped = self._ID_PREFIX_PATTERN.sub("", raw_id)
        if stripped != raw_id and stripped in self._first_path_by_feature:
            return stripped

        # 4. Return as-is (may not resolve)
        return raw_id
