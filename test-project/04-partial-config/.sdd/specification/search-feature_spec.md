---
id: spec-search-feature
type: spec
title: "Search Feature Specification"
feature-id: search-feature
status: draft
created: 2026-02-26
updated: 2026-02-26
sdd-phase: specify
depends-on: [prd-search-feature]
tags: [search]
---

# Search Feature Specification

## Search Engine

- SQLite FTS5 with trigram tokenizer
- Snippet highlighting

## API

- GET /api/search?q=keyword
- GET /api/search/suggestions
