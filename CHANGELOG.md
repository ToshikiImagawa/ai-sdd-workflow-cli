# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-03-06

### Fixed

- **Windows path handling** - Normalized path separators to POSIX format (`/`) in parser, scanner, and analyzer, fixing document indexing and dependency resolution failures on Windows

## [1.0.0] - 2026-03-02

### Added

- **`sdd-cli lint`**: New document linting command for validating `.sdd/` documents
  - Checks frontmatter field validity (required fields, format, allowed values)
  - Detects broken `depends-on` references and circular dependencies
  - Validates document naming conventions and directory placement
  - Supports `--format` option (`text` / `json`) for CI integration
  - Exit code `1` when lint errors are found for use in pre-commit hooks
- **Lint error overlay in dependency visualization**: `sdd-cli visualize` now displays lint errors directly on the dependency graph
  - Error/warning badges shown on document nodes
  - Toggle button to show/hide lint annotations
  - Color-coded severity indicators (error: red, warning: yellow)

## [0.2.1] - 2026-03-02

### Fixed

- **Dependency graph visualization** - `depends-on` with full document IDs (e.g., `prd-auth`, `spec-login`) now correctly resolved to target documents
  - Previously, prefixed IDs in `depends-on` frontmatter failed to match internal `feature_id` (which has prefixes stripped), resulting in missing edges in the dependency graph
  - Added `_normalize_to_feature_id()` to handle both bare feature IDs and full document IDs with AI-SDD prefixes (`prd-`, `spec-`, `design-`, `task-`, `impl-`)

## [0.2.0] - 2026-02-26

### Added

- **AI-SDD Workflow standard frontmatter support**: Added support for common frontmatter fields
  - New fields: `id`, `type`, `status`, `created`, `updated`, `category`
  - Automatic prefix removal from `id` field (e.g., `prd-feature` → `feature` as `feature_id`)
  - Supported prefixes: `prd-`, `spec-`, `design-`, `task-`, `impl-`

### Changed

- **Standardized dependency field**: Now only supports `depends-on` (AI-SDD standard)
  - Removed support for legacy field names: `depends_on`, `dependencies`
- **Database schema**: Extended `documents_meta` table with new AI-SDD common fields
- **Codebase internationalization**: Converted all Japanese comments and docstrings to English

### Fixed

- Improved backward compatibility by maintaining `feature_id` field alongside new `id` field

## [0.1.0] - 2026-02-21

### Added

- Initial release as standalone PyPI package
- **`sdd-cli init`**: Generate `.sdd-config.json` and export SDD environment variables
  - `--env` flag: Output `export SDD_*=...` statements for shell eval
  - `CLAUDE_ENV_FILE` support: Write env vars to Claude Code environment file when set
- **`sdd-cli index`**: Build full-text search index using SQLite FTS5 with trigram tokenizer
- **`sdd-cli search`**: Fast keyword, feature ID, tag, and directory-based document search
- **`sdd-cli visualize`**: Generate dependency graphs with interactive HTML viewer
  - Split view: PRD-based and direct dependency graphs
- **`sdd-cli cache list`**: List cached project indexes
- **`sdd-cli cache clean`**: Clean up cached project indexes with wildcard pattern support
- `.sdd-config.json` configuration file for per-project directory settings
- Environment variable overrides (`SDD_ROOT`, `SDD_REQUIREMENT_DIR`, `SDD_SPECIFICATION_DIR`, `SDD_TASK_DIR`)
- XDG Base Directory compliant cache storage (`~/.cache/sdd-cli/`)
- Multi-language support (optimized for 3+ character keywords via trigram tokenizer)
- GitHub Actions CI pipeline (lint + test matrix: Ubuntu/macOS × Python 3.9/3.11/3.13)
- Regression test suite for init, index, search, and visualize commands

### Notes

- Previously bundled with [ai-sdd-workflow](https://github.com/ToshikiImagawa/ai-sdd-workflow) plugin (`plugins/sdd-workflow/cli/`)
- Now distributed independently via PyPI for easier installation and updates
