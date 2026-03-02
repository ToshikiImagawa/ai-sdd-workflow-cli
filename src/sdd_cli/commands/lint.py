"""Lint command for SDD document static analysis."""

from __future__ import annotations

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
from sdd_cli.linter.formatter import format_issues
from sdd_cli.types import DocumentRecord, LintIssue, LintResult, ParsedDocument


def run_lint(root: Path, json_output: bool, quiet: bool) -> tuple[str, bool]:
    """Core lint logic. Testable entry point.

    Processing flow:
    1. DocumentScanner.scan_all() to collect files
    2. Exclude task/ directory files
    3. DocumentParser.parse() each file
       - YAML parse errors reported as yaml-parse-error error, file skipped
       - Files without frontmatter are skipped
    4. Build DocumentRecord-like data from ParsedDocument
    5. Run 4 checks (pass parsed_docs to check_id_integrity)
    6. Build LintResult and format with format_issues
    7. If quiet=True and 0 issues, return empty string

    Returns:
        Tuple of (formatted output, whether error-level issues exist)
    """
    config = resolve_config(root)
    sdd_root = root / config["root"]

    if not sdd_root.exists():
        result = LintResult(issues=[], error_count=0, warning_count=0, files_checked=0)
        output = format_issues(result, json_output)
        return (output, False)

    scanner = DocumentScanner(sdd_root)
    scan_results = scanner.scan_all()

    # Exclude task/ directory and sort for deterministic output across platforms
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
            # YAML parse error
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

    result = LintResult(
        issues=all_issues,
        error_count=error_count,
        warning_count=warning_count,
        files_checked=files_checked,
    )

    if quiet and error_count == 0 and warning_count == 0:
        return ("", False)

    output = format_issues(result, json_output)
    return (output, error_count > 0)
