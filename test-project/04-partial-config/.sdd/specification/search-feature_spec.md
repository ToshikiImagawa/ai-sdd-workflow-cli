---
title: "Search Feature Specification"
feature-id: search-feature
tags: [search]
depends_on: [search-feature]
---

# Search Feature Specification

## Search Engine

- SQLite FTS5 with trigram tokenizer
- Snippet highlighting

## API

- GET /api/search?q=keyword
- GET /api/search/suggestions
