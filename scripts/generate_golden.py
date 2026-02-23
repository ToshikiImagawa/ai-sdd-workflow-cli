#!/usr/bin/env python3
"""Generate golden JSON files for index/search regression tests.

Usage:
    python scripts/generate_golden.py              # Generate index golden (all)
    python scripts/generate_golden.py 01-default-config  # Generate specific project
    python scripts/generate_golden.py --search     # Generate search golden (all)
    python scripts/generate_golden.py --search 01-default-config  # Search golden for specific project
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# Add src to path so we can import sdd_cli
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sdd_cli.config import resolve_config
from sdd_cli.indexer.db import IndexDB
from sdd_cli.indexer.parser import DocumentParser
from sdd_cli.indexer.scanner import DocumentScanner

_TEST_PROJECTS_DIR = Path(__file__).resolve().parent.parent / "test-project"

# (project_name, sdd_root_name)
_TEST_PROJECTS = [
    ("01-default-config", ".sdd"),
    ("02-custom-dirs", ".sdd"),
    ("03-custom-root", "docs"),
    ("04-partial-config", ".sdd"),
    ("05-nested-features", ".sdd"),
    ("06-minimal", ".sdd"),
    ("07-multi-feature", ".sdd"),
]


class _Scenario:
    """Search scenario definition."""

    def __init__(
        self,
        name: str,
        query: Optional[str] = None,
        feature_id: Optional[str] = None,
        tag: Optional[str] = None,
        directory: Optional[str] = None,
        limit: int = 10,
    ):
        self.name = name
        self.query = query
        self.feature_id = feature_id
        self.tag = tag
        self.directory = directory
        self.limit = limit

    def params(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "feature_id": self.feature_id,
            "tag": self.tag,
            "directory": self.directory,
            "limit": self.limit,
        }


# Common scenario for all projects + project-specific scenarios
_COMMON_SCENARIOS = [
    _Scenario("all"),
]

_SEARCH_SCENARIOS: dict[str, list[_Scenario]] = {
    "01-default-config": [
        _Scenario("feature_id=auth", feature_id="auth"),
        _Scenario("tag=security", tag="security"),
        _Scenario("directory=task", directory="task"),
        _Scenario("query=Payment", query="Payment"),
    ],
    "02-custom-dirs": [],
    "03-custom-root": [],
    "04-partial-config": [],
    "05-nested-features": [
        _Scenario("feature_id=cart", feature_id="cart"),
        _Scenario("directory=specification", directory="specification"),
    ],
    "06-minimal": [],
    "07-multi-feature": [
        _Scenario("tag=security", tag="security"),
        _Scenario("directory=requirement", directory="requirement"),
        _Scenario("query=Dashboard", query="Dashboard"),
    ],
}


def build_and_get_documents(project_name: str, sdd_root_name: str) -> list[dict]:
    """Run Scanner -> Parser -> IndexDB pipeline and return all documents."""
    project_dir = _TEST_PROJECTS_DIR / project_name
    sdd_root = project_dir / sdd_root_name

    config = resolve_config(project_dir)
    scanner = DocumentScanner(sdd_root, directories=config["directories"])
    scan_results = scanner.scan_all()

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "index.db"
        with IndexDB(db_path) as db:
            for doc_info in scan_results:
                parsed_data = DocumentParser.parse(
                    doc_info["full_path"],
                    directory=doc_info["directory"],
                    rel_path=doc_info["file_path"],
                )
                db.index_document(doc_info, parsed_data)
            return [dict(doc) for doc in db.get_all_documents()]


def _build_index(project_name: str, sdd_root_name: str, db_path: Path) -> IndexDB:
    """Build index and return open IndexDB instance."""
    project_dir = _TEST_PROJECTS_DIR / project_name
    sdd_root = project_dir / sdd_root_name

    config = resolve_config(project_dir)
    scanner = DocumentScanner(sdd_root, directories=config["directories"])
    scan_results = scanner.scan_all()

    db = IndexDB(db_path)
    for doc_info in scan_results:
        parsed_data = DocumentParser.parse(
            doc_info["full_path"],
            directory=doc_info["directory"],
            rel_path=doc_info["file_path"],
        )
        db.index_document(doc_info, parsed_data)
    return db


def _strip_snippet(result: dict) -> dict:
    """Remove snippet field from a search result."""
    return {k: v for k, v in result.items() if k not in ("snippet", "rank")}


def generate(project_name: str, sdd_root_name: str) -> None:
    """Generate index_expected.json for a single project."""
    documents = build_and_get_documents(project_name, sdd_root_name)
    output_path = _TEST_PROJECTS_DIR / project_name / "index_expected.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"  {project_name}: {len(documents)} docs -> {output_path}")


def generate_search(project_name: str, sdd_root_name: str) -> None:
    """Generate search_expected.json for a single project."""
    scenarios = _COMMON_SCENARIOS + _SEARCH_SCENARIOS.get(project_name, [])

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "index.db"
        db = _build_index(project_name, sdd_root_name, db_path)
        try:
            golden: list[dict[str, Any]] = []
            for scenario in scenarios:
                results = db.search(**scenario.params())
                cleaned = [_strip_snippet(dict(r)) for r in results]
                # query ありの場合は file_path ソートで順序を安定させる
                if scenario.query:
                    cleaned.sort(key=lambda d: d["file_path"])
                golden.append(
                    {
                        "name": scenario.name,
                        "params": scenario.params(),
                        "results": cleaned,
                    }
                )
        finally:
            db.close()

    output_path = _TEST_PROJECTS_DIR / project_name / "search_expected.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(golden, f, indent=2, ensure_ascii=False)
    print(f"  {project_name}: {len(scenarios)} scenarios -> {output_path}")


def main() -> None:
    args = sys.argv[1:]
    search_mode = "--search" in args
    if search_mode:
        args.remove("--search")

    gen_func = generate_search if search_mode else generate
    mode_label = "search" if search_mode else "index"

    if args:
        project_map = {name: root for name, root in _TEST_PROJECTS}
        for name in args:
            if name not in project_map:
                print(f"Unknown project: {name}")
                sys.exit(1)
            gen_func(name, project_map[name])
    else:
        print(f"Generating {mode_label} golden JSON for all test projects...")
        for name, root in _TEST_PROJECTS:
            gen_func(name, root)
        print("Done.")


if __name__ == "__main__":
    main()
