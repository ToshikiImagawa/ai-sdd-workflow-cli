"""Core lint logic extracted for reuse by both lint and visualize commands."""

from __future__ import annotations

import re
from pathlib import Path

from sdd_cli.config import resolve_config
from sdd_cli.indexer.parser import DocumentParser
from sdd_cli.indexer.scanner import DocumentScanner
from sdd_cli.linter.checks import (
    check_broken_links,
    check_circular_dependencies,
    check_id_integrity,
    check_required_fields,
)
from sdd_cli.types import DocumentRecord, LintIssue, LintResult, ParsedDocument


def run_lint_issues(root: Path) -> LintResult:
    """Run all lint checks and return the result.

    This is the core lint logic extracted from commands/lint.py.
    Used by both `sdd-cli lint` and `sdd-cli visualize`.

    Args:
        root: Project root directory

    Returns:
        LintResult with all detected issues
    """
    config = resolve_config(root)
    sdd_root = root / config["root"]

    if not sdd_root.exists():
        return LintResult(issues=[], error_count=0, warning_count=0, files_checked=0)

    scanner = DocumentScanner(sdd_root)
    scan_results = scanner.scan_all()

    # Exclude task/ directory and sort for deterministic output
    scan_results = [sr for sr in scan_results if sr["directory"] != "task"]
    scan_results.sort(key=lambda sr: sr["file_path"])

    documents: list[DocumentRecord] = []
    parsed_docs: list[ParsedDocument] = []
    yaml_issues: list[LintIssue] = []
    files_checked = len(scan_results)

    for sr in scan_results:
        try:
            parsed = DocumentParser.parse(
                sr["full_path"],
                directory=sr["directory"],
                rel_path=sr["file_path"],
            )
        except Exception:
            yaml_issues.append(
                LintIssue(
                    severity="error",
                    rule="yaml-parse-error",
                    file_path=sr["file_path"],
                    line=None,
                    message=f"Failed to parse YAML frontmatter in {sr['file_path']}",
                    details=None,
                )
            )
            continue

        # Skip files without frontmatter (id is empty)
        if not parsed.get("id"):
            continue

        doc = DocumentRecord(
            file_path=sr["file_path"],
            file_name=sr["file_name"],
            directory=sr["directory"],
            file_type=parsed["file_type"],
            title=parsed["title"],
            feature_id=parsed["feature_id"],
            parent_feature_id=parsed.get("parent_feature_id"),
            tags=parsed.get("tags", []),
            depends_on=parsed.get("depends_on", []),
            links=parsed.get("links", []),
            id=parsed.get("id", ""),
            type=parsed.get("type"),
            status=parsed.get("status"),
            created=parsed.get("created"),
            updated=parsed.get("updated"),
            category=parsed.get("category"),
        )
        documents.append(doc)
        parsed_docs.append(parsed)

    # Run all checks
    all_issues: list[LintIssue] = []
    all_issues.extend(yaml_issues)
    all_issues.extend(check_circular_dependencies(documents))
    all_issues.extend(check_broken_links(documents, sdd_root))
    all_issues.extend(check_required_fields(documents))
    all_issues.extend(check_id_integrity(documents, parsed_docs))

    error_count = sum(1 for i in all_issues if i["severity"] == "error")
    warning_count = sum(1 for i in all_issues if i["severity"] == "warning")

    return LintResult(
        issues=all_issues,
        error_count=error_count,
        warning_count=warning_count,
        files_checked=files_checked,
    )


def group_issues_by_file(issues: list[LintIssue]) -> dict[str, list[LintIssue]]:
    """Group lint issues by file_path.

    Args:
        issues: List of lint issues

    Returns:
        Dictionary mapping file_path to list of issues for that file
    """
    grouped: dict[str, list[LintIssue]] = {}
    for issue in issues:
        path = issue["file_path"]
        if path not in grouped:
            grouped[path] = []
        grouped[path].append(issue)
    return grouped


def extract_cycle_edges(issues: list[LintIssue]) -> list[tuple[str, str]]:
    """Extract cycle edge pairs from circular-dependency issues.

    Parses the details field which contains cycle paths like:
    "prd-a -> prd-b -> prd-c -> prd-a"

    Returns list of (source_file_path, target_file_path) tuples.
    Note: Returns (file_path of issue, file_path of issue) pairs
    since the circular-dependency issues report per-file.
    """
    edges: list[tuple[str, str]] = []
    seen_cycles: set[str] = set()

    for issue in issues:
        if issue["rule"] != "circular-dependency":
            continue
        details = issue.get("details")
        if not details:
            continue

        # Normalize cycle to avoid duplicate reporting
        if details in seen_cycles:
            continue
        seen_cycles.add(details)

        # Parse cycle path: "id-a -> id-b -> id-c -> id-a"
        ids = [part.strip() for part in details.split("->")]
        for i in range(len(ids) - 1):
            edges.append((ids[i], ids[i + 1]))

    return edges


def extract_unresolved_deps(issues: list[LintIssue]) -> list[tuple[str, str]]:
    """Extract unresolved dependency pairs from issues.

    Returns list of (source_file_path, unresolved_id) tuples.
    """
    result: list[tuple[str, str]] = []
    # Match unresolved-dependency rule
    unresolved_pattern = re.compile(r"Unresolved depends-on reference: (.+)")

    for issue in issues:
        if issue["rule"] != "unresolved-dependency":
            continue
        match = unresolved_pattern.search(issue["message"])
        if match:
            unresolved_id = match.group(1)
            result.append((issue["file_path"], unresolved_id))

    return result
