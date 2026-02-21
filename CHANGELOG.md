# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-21

### Added

- Initial release as standalone PyPI package
- **`sdd-cli index`**: Build full-text search index using SQLite FTS5 with trigram tokenizer
- **`sdd-cli search`**: Fast keyword, feature ID, tag, and directory-based document search
- **`sdd-cli visualize`**: Generate dependency graphs with interactive HTML viewer
- **`sdd-cli cache list`**: List cached project indexes
- **`sdd-cli cache clean`**: Clean up cached project indexes
- XDG Base Directory compliant cache storage (`~/.cache/sdd-cli/`)
- Multi-language support (optimized for 3+ character keywords via trigram tokenizer)

### Notes

- Previously bundled with [ai-sdd-workflow](https://github.com/ToshikiImagawa/ai-sdd-workflow) plugin (`plugins/sdd-workflow/cli/`)
- Now distributed independently via PyPI for easier installation and updates
