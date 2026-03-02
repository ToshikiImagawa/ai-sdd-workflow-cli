"""Static analysis checks for SDD documents."""

from __future__ import annotations

import re
from pathlib import Path

from sdd_cli.types import DocumentRecord, LintIssue, ParsedDocument

# ── Constants ────────────────────────────────────────────────────────

REQUIRED_FIELDS_BY_TYPE: dict[str, list[str]] = {
    "prd": ["id", "title", "type", "status", "created", "updated"],
    "spec": ["id", "title", "type", "status", "created", "updated"],
    "design": ["id", "title", "type", "status", "created", "updated", "impl-status"],
}

VALID_STATUS_VALUES = {"draft", "active", "review", "approved", "deprecated"}
VALID_IMPL_STATUS_VALUES = {"not-implemented", "in-progress", "implemented"}

_REQ_ID_PATTERN = re.compile(r"\b(UR|FR|NFR)-\d{3}\b")
_CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")


# ── check_circular_dependencies ──────────────────────────────────────


def check_circular_dependencies(
    documents: list[DocumentRecord],
) -> list[LintIssue]:
    """Detect circular dependencies in depends-on fields.

    Builds a directed graph from depends_on and uses DFS to find cycles.
    Unresolved IDs (not matching any document) are skipped.
    """
    # Build ID -> file_path mapping
    id_to_path: dict[str, str] = {}
    for doc in documents:
        doc_id = doc.get("id", "")
        if doc_id:
            id_to_path[doc_id] = doc["file_path"]

    # Build adjacency list (only resolved IDs)
    graph: dict[str, list[str]] = {}
    for doc in documents:
        doc_id = doc.get("id", "")
        if not doc_id:
            continue
        deps = doc.get("depends_on", [])
        graph[doc_id] = [d for d in deps if d in id_to_path]

    issues: list[LintIssue] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    reported_cycles: set[frozenset[str]] = set()

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:]
                cycle_key = frozenset(cycle)
                if cycle_key not in reported_cycles:
                    reported_cycles.add(cycle_key)
                    cycle_path = " → ".join(cycle) + " → " + cycle[0]
                    file_path = id_to_path.get(neighbor, "")
                    issues.append(
                        LintIssue(
                            severity="error",
                            rule="circular-dependency",
                            file_path=file_path,
                            line=None,
                            message=f"Circular dependency detected: {cycle_path}",
                            details=cycle_path,
                        )
                    )

        path.pop()
        rec_stack.discard(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return issues


# ── check_broken_links ───────────────────────────────────────────────


def check_broken_links(
    documents: list[DocumentRecord],
    sdd_root: Path,
) -> list[LintIssue]:
    """Verify that relative links in documents point to existing files.

    Uses the links field (already extracted by parser).
    Skips external URLs (http/https) and anchor links (#).
    Reports path traversal attempts as errors.
    """
    issues: list[LintIssue] = []

    for doc in documents:
        links = doc.get("links", [])
        if not links:
            continue

        doc_dir = (sdd_root / doc["file_path"]).parent

        for link in links:
            # Skip external URLs
            if link.startswith("http://") or link.startswith("https://"):
                continue
            # Skip anchor links
            if link.startswith("#"):
                continue

            # Resolve the link target
            target = (doc_dir / link).resolve()

            # Path traversal check
            try:
                target.relative_to(sdd_root.resolve())
            except ValueError:
                line = _find_link_line(sdd_root / doc["file_path"], link)
                issues.append(
                    LintIssue(
                        severity="error",
                        rule="broken-link",
                        file_path=doc["file_path"],
                        line=line,
                        message=f"Link target is outside SDD root: {link}",
                        details=link,
                    )
                )
                continue

            # Check file existence
            if not target.exists():
                line = _find_link_line(sdd_root / doc["file_path"], link)
                issues.append(
                    LintIssue(
                        severity="error",
                        rule="broken-link",
                        file_path=doc["file_path"],
                        line=line,
                        message=f"Link target does not exist: {link}",
                        details=link,
                    )
                )

    return issues


def _find_link_line(file_path: Path, link: str) -> int | None:
    """Find the line number where a link appears in a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            for i, line_text in enumerate(f, 1):
                if link in line_text:
                    return i
    except (OSError, UnicodeDecodeError):
        pass
    return None


# ── check_required_fields ────────────────────────────────────────────


def check_required_fields(
    documents: list[DocumentRecord],
) -> list[LintIssue]:
    """Detect missing or invalid required fields based on document type."""
    issues: list[LintIssue] = []

    for doc in documents:
        doc_type = doc.get("type")
        if not doc_type or doc_type not in REQUIRED_FIELDS_BY_TYPE:
            continue

        required = REQUIRED_FIELDS_BY_TYPE[doc_type]

        # Check each required field
        for field in required:
            if field == "impl-status":
                # impl-status is not in DocumentRecord; check via type
                # We check if it should exist but is missing by looking
                # at the document type being design
                # Since DocumentRecord doesn't have impl-status, we report it
                # if the doc is design type (it should have been in frontmatter)
                # For now, report as missing since DocumentRecord doesn't carry it
                issues.append(
                    LintIssue(
                        severity="warning",
                        rule="missing-required-field",
                        file_path=doc["file_path"],
                        line=None,
                        message=f"Required field 'impl-status' is missing for document type '{doc_type}'",
                        details=None,
                    )
                )
                continue

            value = doc.get(field)  # type: ignore[arg-type]
            if value is None or value == "":
                issues.append(
                    LintIssue(
                        severity="warning",
                        rule="missing-required-field",
                        file_path=doc["file_path"],
                        line=None,
                        message=f"Required field '{field}' is missing for document type '{doc_type}'",
                        details=None,
                    )
                )

        # Validate status value
        status = doc.get("status")
        if status and status not in VALID_STATUS_VALUES:
            issues.append(
                LintIssue(
                    severity="warning",
                    rule="invalid-field-value",
                    file_path=doc["file_path"],
                    line=None,
                    message=f"Invalid status value '{status}'. "
                    f"Expected one of: {', '.join(sorted(VALID_STATUS_VALUES))}",
                    details=None,
                )
            )

    return issues


# ── check_id_integrity ───────────────────────────────────────────────


def check_id_integrity(
    documents: list[DocumentRecord],
    parsed_docs: list[ParsedDocument],
) -> list[LintIssue]:
    """Verify ID uniqueness and reference integrity.

    - Detect duplicate document IDs
    - Detect unresolved depends-on references
    - Detect orphan requirement ID references (UR/FR/NFR-xxx in spec/design
      that don't exist in requirement/ documents)
    """
    issues: list[LintIssue] = []

    # Build ID sets
    all_ids: dict[str, list[str]] = {}  # id -> [file_paths]
    for doc in documents:
        doc_id = doc.get("id", "")
        if doc_id:
            all_ids.setdefault(doc_id, []).append(doc["file_path"])

    # Check duplicate IDs
    for doc_id, paths in all_ids.items():
        if len(paths) > 1:
            for path in paths[1:]:
                issues.append(
                    LintIssue(
                        severity="error",
                        rule="duplicate-id",
                        file_path=path,
                        line=None,
                        message=f"Duplicate document ID '{doc_id}' (also in {paths[0]})",
                        details=doc_id,
                    )
                )

    # Check unresolved depends-on
    id_set = set(all_ids.keys())
    for doc in documents:
        for dep in doc.get("depends_on", []):
            if dep and dep not in id_set:
                issues.append(
                    LintIssue(
                        severity="warning",
                        rule="unresolved-dependency",
                        file_path=doc["file_path"],
                        line=None,
                        message=f"depends-on references non-existent ID '{dep}'",
                        details=dep,
                    )
                )

    # Check orphan requirement ID references
    # Collect all requirement IDs defined in requirement/ documents
    defined_req_ids: set[str] = set()
    for doc, parsed in zip(documents, parsed_docs):
        if doc.get("file_type") == "requirement" or doc.get("directory") == "requirement":
            content = parsed.get("content", "")
            clean = _CODE_BLOCK_PATTERN.sub("", content)
            defined_req_ids.update(_REQ_ID_PATTERN.findall(clean))
            # findall returns the group, so we need full match
    # Re-extract with full match
    defined_req_ids_full: set[str] = set()
    for doc, parsed in zip(documents, parsed_docs):
        if doc.get("file_type") == "requirement" or doc.get("directory") == "requirement":
            content = parsed.get("content", "")
            clean = _CODE_BLOCK_PATTERN.sub("", content)
            for m in _REQ_ID_PATTERN.finditer(clean):
                defined_req_ids_full.add(m.group(0))

    # Check spec/design documents for references to undefined requirement IDs
    for doc, parsed in zip(documents, parsed_docs):
        ft = doc.get("file_type", "")
        if ft not in ("spec", "design"):
            continue

        content = parsed.get("content", "")
        clean = _CODE_BLOCK_PATTERN.sub("", content)
        for match in _REQ_ID_PATTERN.finditer(clean):
            req_id = match.group(0)
            if req_id not in defined_req_ids_full:
                issues.append(
                    LintIssue(
                        severity="warning",
                        rule="orphan-reference",
                        file_path=doc["file_path"],
                        line=None,
                        message=f"Referenced requirement ID '{req_id}' not found in requirement/",
                        details=req_id,
                    )
                )

    return issues
