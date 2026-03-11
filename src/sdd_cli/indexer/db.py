"""SQLite FTS5 index manager for SDD documents."""

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional, cast

from sdd_cli.types import DocumentInfo, DocumentRecord, FilterCondition, ParsedDocument, SearchResult

# Fields allowed in filter DSL to prevent injection via field names
_ALLOWED_FILTER_FIELDS = frozenset({"feature_id", "status", "type", "tags", "category", "directory", "file_type"})


def _regexp_func(pattern: str, value: Optional[str]) -> bool:
    """SQLite REGEXP UDF backed by Python re.search().

    Raises ValueError on invalid regex pattern.
    """
    try:
        return bool(re.search(pattern, value or ""))
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e


class IndexDB:
    """Manages SQLite FTS5 index for document search."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.create_function("REGEXP", 2, _regexp_func)
        self._create_tables()

    def _create_tables(self):
        """Create FTS5 table and metadata table."""
        cursor = self.conn.cursor()

        # Create FTS5 virtual table for full-text search
        # Use trigram tokenizer for better Japanese support
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                file_path,
                file_name,
                directory,
                file_type,
                title,
                feature_id,
                tags,
                content,
                tokenize = 'trigram'
            )
        """)

        # Create metadata table for structured data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents_meta (
                file_path TEXT PRIMARY KEY,
                file_type TEXT,
                feature_id TEXT,
                parent_feature_id TEXT,
                tags TEXT,
                depends_on TEXT,
                links TEXT,
                id TEXT,
                type TEXT,
                status TEXT,
                created TEXT,
                updated TEXT,
                category TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on feature_id for faster filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feature_id
            ON documents_meta(feature_id)
        """)

        self.conn.commit()

    def clear(self):
        """Clear all indexed documents."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents_fts")
        cursor.execute("DELETE FROM documents_meta")
        self.conn.commit()

    def index_document(self, doc_info: DocumentInfo, parsed_data: ParsedDocument) -> None:
        """Index a single document.

        Args:
            doc_info: Document info from scanner (file_path, file_name, directory)
            parsed_data: Parsed metadata from parser (title, feature_id, tags, file_type, parent_feature_id, etc.)
        """
        cursor = self.conn.cursor()

        # Prepare tags as searchable text
        tags_text = " ".join(parsed_data["tags"])

        # Insert into FTS5 table
        cursor.execute(
            """
            INSERT INTO documents_fts (
                file_path, file_name, directory, file_type, title,
                feature_id, tags, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                doc_info["file_path"],
                doc_info["file_name"],
                doc_info["directory"],
                parsed_data["file_type"],
                parsed_data["title"],
                parsed_data["feature_id"],
                tags_text,
                parsed_data["content"],
            ),
        )

        # Insert into metadata table
        cursor.execute(
            """
            INSERT OR REPLACE INTO documents_meta (
                file_path, file_type, feature_id, parent_feature_id, tags, depends_on, links,
                id, type, status, created, updated, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                doc_info["file_path"],
                parsed_data["file_type"],
                parsed_data["feature_id"],
                parsed_data.get("parent_feature_id"),
                json.dumps(parsed_data["tags"]),
                json.dumps(parsed_data["depends_on"]),
                json.dumps(parsed_data["links"]),
                parsed_data.get("id"),
                parsed_data.get("type"),
                parsed_data.get("status"),
                parsed_data.get("created"),
                parsed_data.get("updated"),
                parsed_data.get("category"),
            ),
        )

        self.conn.commit()

    def get_descendants(self, feature_id: str) -> set[str]:
        """Iteratively traverse parent_feature_id chain and return all descendant feature_ids.

        Args:
            feature_id: Starting feature ID (excluded from result)

        Returns:
            Set of descendant feature_ids (excluding the given feature_id itself)
        """
        visited: set[str] = set()
        queue = [feature_id]
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT feature_id FROM documents_meta WHERE parent_feature_id = ?",
                (current,),
            )
            children = [row[0] for row in cursor.fetchall()]
            queue.extend(children)
        return visited - {feature_id}

    def search(
        self,
        query: Optional[str] = None,
        feature_id: Optional[str] = None,
        tag: Optional[str] = None,
        directory: Optional[str] = None,
        filters: Optional[list[FilterCondition]] = None,
        or_operator: bool = False,
        parent: Optional[str] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search indexed documents.

        Args:
            query: Full-text search query
            feature_id: Filter by feature ID
            tag: Filter by tag
            directory: Filter by directory type
            filters: List of DSL filter conditions (field:op:value)
            or_operator: If True, combine filters with OR instead of AND
            parent: Retrieve all descendants of this feature_id
            limit: Maximum number of results

        Returns:
            List of matching documents with metadata
        """
        cursor = self.conn.cursor()

        # Build query
        params: list[Any] = []

        if query:
            # FTS5 search
            sql = """
                SELECT
                    fts.file_path,
                    fts.file_name,
                    fts.directory,
                    fts.file_type,
                    fts.title,
                    fts.feature_id,
                    meta.parent_feature_id,
                    meta.tags,
                    meta.id,
                    meta.type,
                    meta.status,
                    meta.created,
                    meta.updated,
                    meta.category,
                    snippet(documents_fts, 7, '...', '...', '', 50) as snippet,
                    rank
                FROM documents_fts fts
                LEFT JOIN documents_meta meta ON fts.file_path = meta.file_path
                WHERE documents_fts MATCH ?
            """
            params.append(query)
        else:
            # Non-FTS search
            sql = """
                SELECT
                    fts.file_path,
                    fts.file_name,
                    fts.directory,
                    fts.file_type,
                    fts.title,
                    fts.feature_id,
                    meta.parent_feature_id,
                    meta.tags,
                    meta.id,
                    meta.type,
                    meta.status,
                    meta.created,
                    meta.updated,
                    meta.category,
                    substr(fts.content, 1, 150) as snippet
                FROM documents_fts fts
                LEFT JOIN documents_meta meta ON fts.file_path = meta.file_path
                WHERE 1=1
            """

        # Add legacy filters
        if feature_id:
            sql += " AND fts.feature_id = ?"
            params.append(feature_id)

        if tag:
            sql += " AND fts.tags LIKE ?"
            params.append(f"%{tag}%")

        if directory:
            sql += " AND fts.directory = ?"
            params.append(directory)

        # Resolve --parent: collect all descendant feature_ids
        if parent is not None:
            descendants = self.get_descendants(parent)
            if not descendants:
                # No descendants found; return empty result immediately
                return []
            placeholders = ", ".join("?" for _ in descendants)
            sql += f" AND meta.feature_id IN ({placeholders})"
            params.extend(sorted(descendants))

        # Apply DSL filters
        if filters:
            filter_clauses: list[str] = []
            for cond in filters:
                field = cond["field"]
                op = cond["op"]
                value = cond["value"]
                if field not in _ALLOWED_FILTER_FIELDS:
                    raise ValueError(f"Invalid filter field: '{field}'. Allowed: {sorted(_ALLOWED_FILTER_FIELDS)}")
                col = f"meta.{field}"
                if op == "exact":
                    filter_clauses.append(f"{col} = ?")
                    params.append(value)
                elif op == "contains":
                    filter_clauses.append(f"{col} LIKE ?")
                    params.append(f"%{value}%")
                elif op == "regex":
                    # Validate pattern before sending to DB
                    try:
                        re.compile(value)
                    except re.error as e:
                        raise ValueError(f"Invalid regex pattern '{value}': {e}") from e
                    filter_clauses.append(f"REGEXP(?, {col})")
                    params.append(value)
            if filter_clauses:
                joiner = " OR " if or_operator else " AND "
                combined = joiner.join(filter_clauses)
                sql += f" AND ({combined})"

        # Add ordering and limit
        if query:
            sql += " ORDER BY rank"
        else:
            sql += " ORDER BY fts.file_path"

        sql += " LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert to dictionaries
        results: list[SearchResult] = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            if result.get("tags"):
                try:
                    result["tags"] = json.loads(result["tags"])
                except (json.JSONDecodeError, TypeError, ValueError):
                    result["tags"] = []
            results.append(cast(SearchResult, result))

        return results

    def get_all_documents(self) -> list[DocumentRecord]:
        """Get all indexed documents with metadata.

        Returns:
            List of all documents with metadata
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                fts.file_path,
                fts.file_name,
                fts.directory,
                fts.file_type,
                fts.title,
                fts.feature_id,
                meta.parent_feature_id,
                meta.tags,
                meta.depends_on,
                meta.links,
                meta.id,
                meta.type,
                meta.status,
                meta.created,
                meta.updated,
                meta.category
            FROM documents_fts fts
            LEFT JOIN documents_meta meta ON fts.file_path = meta.file_path
            ORDER BY fts.file_path
        """)

        results: list[DocumentRecord] = []
        for row in cursor.fetchall():
            result = dict(row)
            # Parse JSON fields
            for field in ["tags", "depends_on", "links"]:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError, ValueError):
                        result[field] = []
            results.append(cast(DocumentRecord, result))

        return results

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
