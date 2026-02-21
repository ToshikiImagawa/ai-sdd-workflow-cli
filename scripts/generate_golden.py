#!/usr/bin/env python3
"""Generate golden JSON files for index regression tests.

Usage:
    python scripts/generate_golden.py              # Generate all
    python scripts/generate_golden.py 01-default-config  # Generate specific project
"""

import json
import sys
import tempfile
from pathlib import Path

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
                parsed_data = DocumentParser.parse(doc_info["full_path"])
                db.index_document(doc_info, parsed_data)
            return [dict(doc) for doc in db.get_all_documents()]


def generate(project_name: str, sdd_root_name: str) -> None:
    """Generate expected.json for a single project."""
    documents = build_and_get_documents(project_name, sdd_root_name)
    output_path = _TEST_PROJECTS_DIR / project_name / "expected.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"  {project_name}: {len(documents)} docs -> {output_path}")


def main() -> None:
    targets = sys.argv[1:]

    if targets:
        project_map = {name: root for name, root in _TEST_PROJECTS}
        for name in targets:
            if name not in project_map:
                print(f"Unknown project: {name}")
                sys.exit(1)
            generate(name, project_map[name])
    else:
        print("Generating golden JSON for all test projects...")
        for name, root in _TEST_PROJECTS:
            generate(name, root)
        print("Done.")


if __name__ == "__main__":
    main()
