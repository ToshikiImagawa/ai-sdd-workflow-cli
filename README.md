# SDD CLI

[![CI](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type--check-mypy-blue)](https://mypy-lang.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli)

Document management CLI tool for the AI-SDD Workflow.

Works with the [AI-SDD Workflow Plugin](https://github.com/ToshikiImagawa/ai-sdd-workflow) to provide full-text search
and dependency visualization for specification documents.

[日本語版 README](README.ja.md)

## Features

- **Project Init**: Generate `.sdd-config.json` and export SDD environment variables
- **Index Building**: Index documents under `.sdd/` with SQLite FTS5
- **Full-Text Search**: Fast search by keyword, feature ID, or tag
- **Filter DSL**: Flexible metadata filtering with `--filter "field:op:value"` (exact / contains / regex)
- **OR Search**: Combine multiple filter conditions with OR using `--or`
- **Parent-Child Traversal**: Retrieve all descendant documents of a feature with `--parent`
- **Dependency Visualization**: Interactive HTML viewer for document dependencies
- **Cache Management**: List and clean per-project caches

## Requirements

- Python 3.9+

## Installation

### pip

```bash
pip install git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git
```

### uv

```bash
uv tool install --from git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git sdd-cli
```

### uvx (run without installing)

```bash
uvx --from git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git sdd-cli --help
```

## Usage

### Project Initialization

```bash
# Generate .sdd-config.json with default settings
sdd-cli init

# Specify project root
sdd-cli init --root /path/to/project

# Export SDD environment variables (for shell eval)
eval $(sdd-cli init --env)
```

When `CLAUDE_ENV_FILE` is set, `--env` writes export statements to that file instead of stdout.

### Build Index

```bash
sdd-cli index

# Suppress output
sdd-cli index --quiet
```

### Search Documents

```bash
# Keyword search
sdd-cli search "login feature"

# Filter by feature ID
sdd-cli search --feature-id user-login

# Filter by tag
sdd-cli search --tag authentication

# Filter by directory type
sdd-cli search "auth" --dir specification

# JSON output
sdd-cli search "login" --format json --output results.json

# Limit results
sdd-cli search "login" --limit 5

# Filter by metadata field (exact match)
sdd-cli search --filter "status:exact:implemented"

# Filter by metadata field (partial match)
sdd-cli search --filter "type:contains:spec"

# Filter by metadata field (regex)
sdd-cli search --filter "feature_id:regex:^auth-"

# Combine multiple filters with OR
sdd-cli search --filter "type:exact:spec" --filter "type:exact:design" --or

# Retrieve all descendant documents of a parent feature
sdd-cli search --parent auth
```

### Dependency Visualization

```bash
# Open interactive HTML viewer in browser
sdd-cli visualize

# Filter by directory
sdd-cli visualize --filter-dir specification

# Filter by feature
sdd-cli visualize --feature-id user-login

# Export graph as JSON
sdd-cli visualize --output graph.json
```

### Cache Management

```bash
# List cached projects
sdd-cli cache list

# List in JSON format
sdd-cli cache list --format json

# Delete specific project cache
sdd-cli cache clean --project slide-presentation-app

# Delete caches matching pattern
sdd-cli cache clean --project 'test-*'

# Preview what would be deleted
sdd-cli cache clean --all --dry-run

# Delete all caches
sdd-cli cache clean --all
```

## CLI Reference

### `sdd-cli init`

| Option             | Description                                            |
|--------------------|--------------------------------------------------------|
| `--root DIRECTORY` | Project root directory (default: current directory)    |
| `--env`            | Output export statements for SDD environment variables |

### `sdd-cli index`

| Option             | Description                                         |
|--------------------|-----------------------------------------------------|
| `--root DIRECTORY` | Project root directory (default: current directory) |
| `--quiet`          | Suppress output messages                            |

### `sdd-cli search [QUERY]`

| Option                                     | Description                                                                                    |
|--------------------------------------------|------------------------------------------------------------------------------------------------|
| `--root DIRECTORY`                         | Project root directory (default: current directory)                                            |
| `--feature-id TEXT`                        | Filter by feature ID                                                                           |
| `--tag TEXT`                               | Filter by tag                                                                                  |
| `--dir [requirement\|specification\|task]` | Filter by directory type                                                                       |
| `--filter TEXT`                            | Filter by metadata field: `"field:op:value"` (op: `exact`/`contains`/`regex`). Repeatable.   |
| `--or`                                     | Combine `--filter` conditions with OR (default: AND)                                           |
| `--parent TEXT`                            | Retrieve all descendant documents of the specified parent feature ID                           |
| `--format [text\|json]`                    | Output format (default: text)                                                                  |
| `--output PATH`                            | Output file path (default: stdout)                                                             |
| `--limit INTEGER`                          | Maximum number of results (default: 10)                                                        |

#### Filterable fields for `--filter`

| Field        | Description               |
|--------------|---------------------------|
| `status`     | Document status           |
| `type`       | Document type             |
| `feature_id` | Feature ID                |
| `tags`       | Tags                      |
| `category`   | Category                  |
| `directory`  | Directory type            |
| `file_type`  | File type classification  |

### `sdd-cli visualize`

| Option                                            | Description                                         |
|---------------------------------------------------|-----------------------------------------------------|
| `--root DIRECTORY`                                | Project root directory (default: current directory) |
| `--output PATH`                                   | Export graph as JSON file                           |
| `--filter-dir [requirement\|specification\|task]` | Filter by directory type                            |
| `--feature-id TEXT`                               | Filter by feature ID                                |

### `sdd-cli cache list`

| Option                  | Description                   |
|-------------------------|-------------------------------|
| `--format [text\|json]` | Output format (default: text) |

### `sdd-cli cache clean`

| Option           | Description                                 |
|------------------|---------------------------------------------|
| `--project TEXT` | Project name pattern (supports wildcards)   |
| `--all`          | Delete all cached projects                  |
| `--dry-run`      | Show what would be deleted without deleting |

## Environment Variables

| Variable                | Description                  | Default         |
|-------------------------|------------------------------|-----------------|
| `SDD_ROOT`              | SDD root directory name      | `.sdd`          |
| `SDD_REQUIREMENT_DIR`   | Requirement directory name   | `requirement`   |
| `SDD_SPECIFICATION_DIR` | Specification directory name | `specification` |
| `SDD_TASK_DIR`          | Task directory name          | `task`          |

Environment variables take priority over `.sdd-config.json` settings.

## Cache Directory

Indexes and visualization results are stored following the **XDG Base Directory** specification:

```
~/.cache/sdd-cli/
├── my-project.a1b2c3d4/
│   ├── index.db                  # SQLite FTS5 index
│   ├── metadata.json             # Index metadata
│   ├── dependency-graph.json     # Dependency graph data
│   └── search-results.json      # Search results (from plugin skills)
└── another-project.e5f6g7h8/
    └── ...
```

## AI-SDD Plugin Integration

This tool is called automatically by the [AI-SDD Workflow Plugin](https://github.com/ToshikiImagawa/ai-sdd-workflow)
skills (`/sdd-index`, `/sdd-search`, `/sdd-visualize`).

When the plugin is installed, `sdd-cli` is automatically installed at session start and the initial index build runs
automatically.

## Development

### Setup

```bash
git clone https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git
cd ai-sdd-workflow-cli
uv sync --dev
```

### Test

```bash
uv run pytest
```

### Lint & Format

```bash
uv run ruff check .
uv run ruff format --check .
```

### Type Check

```bash
uv run mypy src/sdd_cli/
```

### Build

```bash
uv build
```

## License

MIT License – See [LICENSE](LICENSE) for details.
