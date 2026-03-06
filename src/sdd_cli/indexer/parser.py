"""Markdown frontmatter parser for SDD documents."""

import re
from pathlib import Path
from typing import Any, Optional

import frontmatter

from sdd_cli.types import ParsedDocument


class DocumentParser:
    """Parses SDD Markdown documents and extracts metadata."""

    @staticmethod
    def parse(
        file_path: Path,
        directory: Optional[str] = None,
        rel_path: Optional[str] = None,
    ) -> ParsedDocument:
        """Parse a Markdown document and extract metadata.

        Args:
            file_path: Path to the Markdown file
            directory: Logical directory name from scanner (e.g. "task", "requirement")
            rel_path: Relative path from SDD root (e.g. "reqs/auth/index.md")

        Returns:
            Dictionary with keys:
                - title: str (from frontmatter or first heading)
                - feature_id: str (extracted from id field with prefix removed, or inferred from filename)
                - file_type: str (requirement/spec/design/task)
                - parent_feature_id: str or None (inferred from directory nesting)
                - tags: List[str] (from frontmatter)
                - depends_on: List[str] (from frontmatter 'depends-on' field)
                - content: str (Markdown body without code blocks)
                - links: List[str] (relative links to other documents)
                - id: str (full id value from frontmatter, e.g., 'prd-document-indexing')
                - type: str or None (from frontmatter 'type' field)
                - status: str or None (from frontmatter 'status' field)
                - created: str or None (from frontmatter 'created' field, format: 'YYYY-MM-DD')
                - updated: str or None (from frontmatter 'updated' field, format: 'YYYY-MM-DD')
                - category: str or None (from frontmatter 'category' field)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                post = frontmatter.load(f)

            metadata = post.metadata
            content = post.content

            # Extract title
            title = DocumentParser._extract_title(metadata, content)

            # Extract or infer feature ID
            feature_id = DocumentParser._extract_feature_id(metadata, file_path, directory, rel_path)

            # Infer file type
            file_type = DocumentParser._infer_file_type(file_path, directory)

            # Infer parent feature ID from directory nesting
            parent_feature_id = DocumentParser._infer_parent_feature_id(file_path, directory, rel_path)

            # Extract tags
            tags = DocumentParser._extract_tags(metadata)

            # Extract dependencies
            depends_on = DocumentParser._extract_dependencies(metadata)

            # Extract content (remove code blocks for better search)
            clean_content = DocumentParser._remove_code_blocks(content)

            # Extract relative links
            links = DocumentParser._extract_links(content)

            # Extract AI-SDD common fields
            doc_id = DocumentParser._extract_id(metadata)
            doc_type = DocumentParser._extract_type(metadata)
            status = DocumentParser._extract_status(metadata)
            created = DocumentParser._extract_created(metadata)
            updated = DocumentParser._extract_updated(metadata)
            category = DocumentParser._extract_category(metadata)

            return {
                "title": title,
                "feature_id": feature_id,
                "file_type": file_type,
                "parent_feature_id": parent_feature_id,
                "tags": tags,
                "depends_on": depends_on,
                "content": clean_content,
                "links": links,
                "id": doc_id,
                "type": doc_type,
                "status": status,
                "created": created,
                "updated": updated,
                "category": category,
            }

        except Exception:
            # Return minimal metadata on error
            return {
                "title": file_path.stem,
                "feature_id": file_path.stem,
                "file_type": "unknown",
                "parent_feature_id": None,
                "tags": [],
                "depends_on": [],
                "content": "",
                "links": [],
                "id": "",
                "type": None,
                "status": None,
                "created": None,
                "updated": None,
                "category": None,
            }

    @staticmethod
    def _extract_title(metadata: dict[str, Any], content: str) -> str:
        """Extract title from frontmatter or first heading."""
        # First try frontmatter
        if "title" in metadata:
            return str(metadata["title"])

        # Then try first H1 heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        return "Untitled"

    @staticmethod
    def _extract_feature_id(
        metadata: dict[str, Any],
        file_path: Path,
        directory: Optional[str] = None,
        rel_path: Optional[str] = None,
    ) -> str:
        """Extract feature ID from frontmatter id field or infer from filename.

        If frontmatter contains 'id' field with format '{prefix}-{name}',
        extracts the name part by removing the prefix.
        Common prefixes: prd-, spec-, design-, task-, impl-
        """
        # Try frontmatter id field
        if "id" in metadata:
            id_value = str(metadata["id"])
            # Remove common AI-SDD prefixes
            for prefix in ["prd-", "spec-", "design-", "task-", "impl-"]:
                if id_value.startswith(prefix):
                    return id_value[len(prefix) :]
            # If no prefix matches, return the id as-is
            return id_value

        # Infer from filename (remove _spec or _design suffix)
        name = file_path.stem
        name = re.sub(r"_(spec|design)$", "", name)

        # If filename is "index" or "tasks", use parent directory name as feature-id
        # This handles cases like: requirement/{feature-name}/index.md, task/{ticket-id}/tasks.md
        if name in ("index", "tasks"):
            parent_name = file_path.parent.name
            # Build skip list: standard dirs + actual base dir from rel_path
            skip_dirs = {"requirement", "specification", "task"}
            if rel_path:
                base_dir = Path(rel_path).parts[0]
                skip_dirs.add(base_dir)
            # Avoid using directory names like "requirement", "specification", "task"
            if parent_name not in skip_dirs:
                return parent_name

        return name

    @staticmethod
    def _extract_tags(metadata: dict[str, Any]) -> list[str]:
        """Extract tags from frontmatter."""
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            # Handle comma-separated string
            return [t.strip() for t in tags.split(",")]
        elif isinstance(tags, list):
            return [str(t) for t in tags]
        return []

    @staticmethod
    def _extract_id(metadata: dict[str, Any]) -> str:
        """Extract document ID from frontmatter.

        Returns the full id value (e.g., 'prd-document-indexing').
        Returns empty string if not present.
        """
        if "id" in metadata:
            return str(metadata["id"])
        return ""

    @staticmethod
    def _extract_type(metadata: dict[str, Any]) -> Optional[str]:
        """Extract document type from frontmatter.

        Returns 'prd', 'spec', 'design', 'task', or other custom types.
        Returns None if not present.
        """
        if "type" in metadata:
            return str(metadata["type"])
        return None

    @staticmethod
    def _extract_status(metadata: dict[str, Any]) -> Optional[str]:
        """Extract document status from frontmatter.

        Common values: 'draft', 'review', 'approved', 'deprecated'.
        Returns None if not present.
        """
        if "status" in metadata:
            return str(metadata["status"])
        return None

    @staticmethod
    def _extract_created(metadata: dict[str, Any]) -> Optional[str]:
        """Extract creation date from frontmatter.

        Expected format: 'YYYY-MM-DD'.
        Returns None if not present.
        """
        if "created" in metadata:
            return str(metadata["created"])
        return None

    @staticmethod
    def _extract_updated(metadata: dict[str, Any]) -> Optional[str]:
        """Extract update date from frontmatter.

        Expected format: 'YYYY-MM-DD'.
        Returns None if not present.
        """
        if "updated" in metadata:
            return str(metadata["updated"])
        return None

    @staticmethod
    def _extract_category(metadata: dict[str, Any]) -> Optional[str]:
        """Extract category from frontmatter.

        Returns None if not present.
        """
        if "category" in metadata:
            return str(metadata["category"])
        return None

    @staticmethod
    def _extract_dependencies(metadata: dict[str, Any]) -> list[str]:
        """Extract dependencies from frontmatter.

        Only supports the AI-SDD standard field name 'depends-on'.
        """
        if "depends-on" in metadata:
            deps = metadata["depends-on"]
            if isinstance(deps, str):
                return [d.strip() for d in deps.split(",")]
            elif isinstance(deps, list):
                return [str(d) for d in deps]
        return []

    @staticmethod
    def _remove_code_blocks(content: str) -> str:
        """Remove code blocks from content for better search."""
        # Remove fenced code blocks
        content = re.sub(r"```[\s\S]*?```", "", content)
        # Remove inline code
        content = re.sub(r"`[^`]+`", "", content)
        return content.strip()

    @staticmethod
    def _extract_links(content: str) -> list[str]:
        """Extract relative Markdown links and backtick-quoted paths."""
        links = []
        seen = set()

        # Match [text](path) format
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
            link = match.group(2)
            if link.endswith(".md") and not link.startswith("http") and link not in seen:
                links.append(link)
                seen.add(link)

        # Match `path/to/file.md` format (backtick-quoted paths)
        for match in re.finditer(r"`([^`]*\.md)`", content):
            link = match.group(1)
            if not link.startswith("http"):
                # Strip leading .sdd/ prefix if present
                link = re.sub(r"^\.sdd/", "", link)
                if link not in seen:
                    links.append(link)
                    seen.add(link)

        return links

    @staticmethod
    def _infer_file_type(file_path: Path, directory: Optional[str] = None) -> str:
        """Infer the file type from the file path and name.

        Args:
            file_path: Path to the file
            directory: Logical directory name from scanner (e.g. "task", "requirement")

        Returns:
            File type: 'requirement', 'spec', 'design', or 'task'
        """
        # If a directory is provided, use it for primary classification
        if directory is not None:
            if directory == "task":
                return "task"

            file_name = file_path.name
            if file_name.endswith("_design.md") or file_name == "index_design.md":
                return "design"
            if file_name.endswith("_spec.md") or file_name == "index_spec.md":
                return "spec"

            if directory == "requirement":
                return "requirement"

            # specification directory without _design/_spec suffix
            if directory == "specification":
                return "unknown"

            return "unknown"

        # Fallback: infer from path string (backward compatibility)
        path_str = file_path.as_posix()
        file_name = file_path.name

        # Check if file is in task directory
        if "/task/" in path_str or path_str.startswith("task/"):
            return "task"

        # Check if file ends with _design.md or is index_design.md
        if file_name.endswith("_design.md") or file_name == "index_design.md":
            return "design"

        # Check if file ends with _spec.md or is index_spec.md
        if file_name.endswith("_spec.md") or file_name == "index_spec.md":
            return "spec"

        # Check if file is in requirement directory
        if "/requirement/" in path_str or path_str.startswith("requirement/"):
            return "requirement"

        # Default fallback
        return "unknown"

    @staticmethod
    def _infer_parent_feature_id(
        file_path: Path,
        directory: Optional[str] = None,
        rel_path: Optional[str] = None,
    ) -> Optional[str]:
        """Infer parent feature ID from directory nesting.

        Args:
            file_path: Path to the file
            directory: Logical directory name from scanner (e.g. "task", "requirement")
            rel_path: Relative path from SDD root (e.g. "reqs/auth/index.md")

        Returns:
            Parent feature ID or None if no parent exists

        Examples:
            requirement/auth/login/index.md → 'auth'
            requirement/user-login.md → None
            specification/auth/login/index_spec.md → 'auth'
            task/TICKET-123/index.md → None (task uses ticket ID, not feature hierarchy)
        """
        # If rel_path is provided, use it to find the base directory
        if rel_path is not None and directory is not None:
            # For task directories, we don't infer parent from path
            if directory == "task":
                return None

            rel_parts = Path(rel_path).parts
            # rel_path starts with the actual base dir name (e.g. "reqs/auth/index.md")
            # parts[0] is the base dir
            if len(rel_parts) < 1:
                return None

            # Use rel_path parts, treating parts[0] as the base directory
            base_dir_index = 0
            depth_from_base = len(rel_parts) - base_dir_index - 1
            is_index = Path(rel_path).name in ["index.md", "index_spec.md", "index_design.md"]

            if depth_from_base >= 2:
                if is_index:
                    if depth_from_base >= 3:
                        parent_dir = rel_parts[base_dir_index + depth_from_base - 2]
                        return parent_dir
                    else:
                        return None
                else:
                    parent_dir = rel_parts[base_dir_index + depth_from_base - 1]
                    return parent_dir

            return None

        # Fallback: infer from file_path (backward compatibility)
        parts = file_path.parts

        # Find the base directory (requirement, specification, task)
        found_index: Optional[int] = None
        for i, part in enumerate(parts):
            if part in ["requirement", "specification", "task"]:
                found_index = i
                break

        if found_index is None:
            return None
        base_dir_index = found_index

        # For task directories, we don't infer parent from path
        # (ticket ID is not feature hierarchy)
        if parts[base_dir_index] == "task":
            return None

        # Calculate depth from base directory
        # Example cases:
        #   requirement/user-login.md
        #     parts = ['requirement', 'user-login.md']
        #     depth = 1 → No parent (flat structure)
        #
        #   requirement/context-display/index.md
        #     parts = ['requirement', 'context-display', 'index.md']
        #     depth = 2, is_index = True → No parent (index.md defines the feature itself)
        #
        #   requirement/context-display/context-behavior.md
        #     parts = ['requirement', 'context-display', 'context-behavior.md']
        #     depth = 2, is_index = False → parent = 'context-display'
        #
        #   requirement/auth/login/index.md
        #     parts = ['requirement', 'auth', 'login', 'index.md']
        #     depth = 3, is_index = True → parent = 'auth' (parent of the feature directory)
        depth_from_base = len(parts) - base_dir_index - 1
        is_index = file_path.name in ["index.md", "index_spec.md", "index_design.md"]

        # If depth >= 2, there's at least one directory between base and file
        if depth_from_base >= 2:
            if is_index:
                # index.md defines the feature itself, so parent is one level up
                # Example: requirement/auth/login/index.md → parent = 'auth'
                if depth_from_base >= 3:
                    # Multi-level nesting: parent is two directories up
                    parent_dir = parts[base_dir_index + depth_from_base - 2]
                    return parent_dir
                else:
                    # Single-level nesting: no parent (index.md defines top-level feature)
                    return None
            else:
                # Non-index file: parent is the immediate parent directory
                # Example: requirement/context-display/context-behavior.md → parent = 'context-display'
                parent_dir = parts[base_dir_index + depth_from_base - 1]
                return parent_dir

        # Flat structure (file directly under base directory)
        return None
