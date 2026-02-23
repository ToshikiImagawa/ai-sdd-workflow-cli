"""Tests for DocumentParser."""

from pathlib import Path

from helpers import write_md

from sdd_cli.indexer.parser import DocumentParser

# ---------------------------------------------------------------------------
# _extract_title
# ---------------------------------------------------------------------------


class TestExtractTitle:
    def test_from_frontmatter(self):
        assert DocumentParser._extract_title({"title": "My Title"}, "") == "My Title"

    def test_from_h1_heading(self):
        content = "Some intro\n# Heading One\nBody text"
        assert DocumentParser._extract_title({}, content) == "Heading One"

    def test_fallback_untitled(self):
        assert DocumentParser._extract_title({}, "No heading here") == "Untitled"


# ---------------------------------------------------------------------------
# _extract_feature_id
# ---------------------------------------------------------------------------


class TestExtractFeatureId:
    def test_from_feature_dash_id(self):
        meta = {"feature-id": "auth-login"}
        assert DocumentParser._extract_feature_id(meta, Path("x.md")) == "auth-login"

    def test_from_feature_underscore_id(self):
        meta = {"feature_id": "auth-login"}
        assert DocumentParser._extract_feature_id(meta, Path("x.md")) == "auth-login"

    def test_from_id_key(self):
        meta = {"id": "feat-01"}
        assert DocumentParser._extract_feature_id(meta, Path("x.md")) == "feat-01"

    def test_priority_order(self):
        meta = {"feature-id": "first", "feature_id": "second", "id": "third"}
        assert DocumentParser._extract_feature_id(meta, Path("x.md")) == "first"

    def test_infer_from_filename(self):
        assert DocumentParser._extract_feature_id({}, Path("user-login.md")) == "user-login"

    def test_strip_spec_suffix(self):
        assert DocumentParser._extract_feature_id({}, Path("auth_spec.md")) == "auth"

    def test_strip_design_suffix(self):
        assert DocumentParser._extract_feature_id({}, Path("auth_design.md")) == "auth"

    def test_index_md_uses_parent_dir(self):
        assert DocumentParser._extract_feature_id({}, Path("requirement/auth/index.md")) == "auth"

    def test_tasks_md_uses_parent_dir(self):
        assert DocumentParser._extract_feature_id({}, Path("task/TICKET-123/tasks.md")) == "TICKET-123"

    def test_index_md_under_base_dir(self):
        # Parent is "requirement" itself → keep "index"
        assert DocumentParser._extract_feature_id({}, Path("requirement/index.md")) == "index"


# ---------------------------------------------------------------------------
# _extract_tags
# ---------------------------------------------------------------------------


class TestExtractTags:
    def test_list_tags(self):
        assert DocumentParser._extract_tags({"tags": ["a", "b"]}) == ["a", "b"]

    def test_csv_string_tags(self):
        assert DocumentParser._extract_tags({"tags": "a, b, c"}) == ["a", "b", "c"]

    def test_empty_tags(self):
        assert DocumentParser._extract_tags({}) == []


# ---------------------------------------------------------------------------
# _extract_dependencies
# ---------------------------------------------------------------------------


class TestExtractDependencies:
    def test_depends_on_list(self):
        assert DocumentParser._extract_dependencies({"depends_on": ["a", "b"]}) == ["a", "b"]

    def test_depends_dash_on_csv(self):
        assert DocumentParser._extract_dependencies({"depends-on": "x, y"}) == ["x", "y"]

    def test_dependencies_key(self):
        assert DocumentParser._extract_dependencies({"dependencies": ["z"]}) == ["z"]

    def test_no_deps(self):
        assert DocumentParser._extract_dependencies({}) == []


# ---------------------------------------------------------------------------
# _remove_code_blocks
# ---------------------------------------------------------------------------


class TestRemoveCodeBlocks:
    def test_fenced_block(self):
        text = "before\n```python\ncode()\n```\nafter"
        result = DocumentParser._remove_code_blocks(text)
        assert "code()" not in result
        assert "before" in result
        assert "after" in result

    def test_inline_code(self):
        text = "Use `my_var` here"
        result = DocumentParser._remove_code_blocks(text)
        assert "my_var" not in result
        assert "Use" in result

    def test_mixed(self):
        text = "A `inline` B\n```\nblock\n```\nC"
        result = DocumentParser._remove_code_blocks(text)
        assert "inline" not in result
        assert "block" not in result
        assert "A" in result
        assert "C" in result


# ---------------------------------------------------------------------------
# _extract_links
# ---------------------------------------------------------------------------


class TestExtractLinks:
    def test_markdown_link(self):
        content = "See [Auth](../requirement/auth.md) for details."
        links = DocumentParser._extract_links(content)
        assert "../requirement/auth.md" in links

    def test_backtick_link(self):
        content = "Refer to `specification/auth_spec.md` for specs."
        links = DocumentParser._extract_links(content)
        assert "specification/auth_spec.md" in links

    def test_http_excluded(self):
        content = "See [Docs](https://example.com/auth.md) for more."
        links = DocumentParser._extract_links(content)
        assert len(links) == 0

    def test_duplicate_dedup(self):
        content = "[A](auth.md) and [B](auth.md)"
        links = DocumentParser._extract_links(content)
        assert links == ["auth.md"]

    def test_sdd_prefix_stripped(self):
        content = "Refer to `.sdd/specification/auth_spec.md` file."
        links = DocumentParser._extract_links(content)
        assert "specification/auth_spec.md" in links

    def test_non_md_link_ignored(self):
        content = "See [Image](photo.png) and [Doc](readme.md)"
        links = DocumentParser._extract_links(content)
        assert links == ["readme.md"]


# ---------------------------------------------------------------------------
# _infer_file_type
# ---------------------------------------------------------------------------


class TestInferFileType:
    def test_task_directory(self):
        assert DocumentParser._infer_file_type(Path("task/TICKET-1/index.md")) == "task"

    def test_design_suffix(self):
        assert DocumentParser._infer_file_type(Path("specification/auth_design.md")) == "design"

    def test_spec_suffix(self):
        assert DocumentParser._infer_file_type(Path("specification/auth_spec.md")) == "spec"

    def test_requirement_directory(self):
        assert DocumentParser._infer_file_type(Path("requirement/auth/index.md")) == "requirement"

    def test_unknown_fallback(self):
        assert DocumentParser._infer_file_type(Path("other/notes.md")) == "unknown"


# ---------------------------------------------------------------------------
# _infer_parent_feature_id
# ---------------------------------------------------------------------------


class TestInferParentFeatureId:
    def test_flat_file_no_parent(self):
        # requirement/user-login.md → None
        assert DocumentParser._infer_parent_feature_id(Path("requirement/user-login.md")) is None

    def test_index_single_level_no_parent(self):
        # requirement/context-display/index.md → None (defines the feature itself)
        assert DocumentParser._infer_parent_feature_id(Path("requirement/context-display/index.md")) is None

    def test_non_index_file_parent(self):
        # requirement/context-display/context-behavior.md → 'context-display'
        result = DocumentParser._infer_parent_feature_id(Path("requirement/context-display/context-behavior.md"))
        assert result == "context-display"

    def test_nested_index_parent(self):
        # requirement/auth/login/index.md → 'auth'
        result = DocumentParser._infer_parent_feature_id(Path("requirement/auth/login/index.md"))
        assert result == "auth"

    def test_task_returns_none(self):
        # task/TICKET-123/index.md → None (task uses ticket ID)
        assert DocumentParser._infer_parent_feature_id(Path("task/TICKET-123/index.md")) is None

    def test_no_base_dir(self):
        assert DocumentParser._infer_parent_feature_id(Path("other/file.md")) is None


# ---------------------------------------------------------------------------
# parse() integration
# ---------------------------------------------------------------------------


class TestParse:
    def test_full_frontmatter(self, tmp_path):
        md = write_md(
            tmp_path / "requirement" / "auth" / "index.md",
            frontmatter={"title": "Auth", "feature-id": "auth", "tags": ["security", "core"]},
            body="# Auth\nContent here.",
        )
        result = DocumentParser.parse(md)
        assert result["title"] == "Auth"
        assert result["feature_id"] == "auth"
        assert result["tags"] == ["security", "core"]
        assert result["file_type"] == "requirement"

    def test_no_frontmatter(self, tmp_path):
        md = write_md(
            tmp_path / "requirement" / "login.md",
            body="# Login Feature\nLogin description.",
        )
        result = DocumentParser.parse(md)
        assert result["title"] == "Login Feature"
        assert result["feature_id"] == "login"

    def test_error_fallback(self, tmp_path):
        bad_file = tmp_path / "bad.md"
        bad_file.write_bytes(b"\x80\x81\x82")  # invalid UTF-8
        result = DocumentParser.parse(bad_file)
        assert result["title"] == "bad"
        assert result["feature_id"] == "bad"
        assert result["file_type"] == "unknown"

    def test_parse_with_custom_directory(self, tmp_path):
        md = write_md(
            tmp_path / "reqs" / "auth" / "index.md",
            frontmatter={"title": "Auth"},
            body="# Auth\nContent here.",
        )
        result = DocumentParser.parse(md, directory="requirement", rel_path="reqs/auth/index.md")
        assert result["file_type"] == "requirement"
        assert result["feature_id"] == "auth"

    def test_links_extracted(self, tmp_path):
        md = write_md(
            tmp_path / "specification" / "auth_spec.md",
            body="See [req](../requirement/auth.md) for details.",
        )
        result = DocumentParser.parse(md)
        assert "../requirement/auth.md" in result["links"]


# ---------------------------------------------------------------------------
# _infer_file_type with directory argument
# ---------------------------------------------------------------------------


class TestInferFileTypeWithDirectory:
    def test_task_with_custom_dir(self):
        assert DocumentParser._infer_file_type(Path("todos/TICKET-1/index.md"), directory="task") == "task"

    def test_requirement_with_custom_dir(self):
        assert DocumentParser._infer_file_type(Path("reqs/auth/index.md"), directory="requirement") == "requirement"

    def test_design_suffix_in_custom_dir(self):
        assert DocumentParser._infer_file_type(Path("specs/auth_design.md"), directory="specification") == "design"

    def test_spec_suffix_in_custom_dir(self):
        assert DocumentParser._infer_file_type(Path("specs/auth_spec.md"), directory="specification") == "spec"

    def test_specification_without_suffix(self):
        assert DocumentParser._infer_file_type(Path("specs/auth.md"), directory="specification") == "unknown"

    def test_directory_none_falls_back(self):
        assert DocumentParser._infer_file_type(Path("task/TICKET-1/index.md"), directory=None) == "task"


# ---------------------------------------------------------------------------
# _infer_parent_feature_id with directory/rel_path arguments
# ---------------------------------------------------------------------------


class TestInferParentWithDirectory:
    def test_custom_dir_nested_index(self):
        # reqs/auth/login/index.md → parent = 'auth'
        result = DocumentParser._infer_parent_feature_id(
            Path("/abs/reqs/auth/login/index.md"),
            directory="requirement",
            rel_path="reqs/auth/login/index.md",
        )
        assert result == "auth"

    def test_custom_dir_single_level_no_parent(self):
        # reqs/auth/index.md → None (defines the feature itself)
        result = DocumentParser._infer_parent_feature_id(
            Path("/abs/reqs/auth/index.md"),
            directory="requirement",
            rel_path="reqs/auth/index.md",
        )
        assert result is None

    def test_custom_dir_non_index_parent(self):
        # reqs/auth/login.md → parent = 'auth'
        result = DocumentParser._infer_parent_feature_id(
            Path("/abs/reqs/auth/login.md"),
            directory="requirement",
            rel_path="reqs/auth/login.md",
        )
        assert result == "auth"

    def test_custom_dir_flat_no_parent(self):
        # reqs/auth.md → None
        result = DocumentParser._infer_parent_feature_id(
            Path("/abs/reqs/auth.md"),
            directory="requirement",
            rel_path="reqs/auth.md",
        )
        assert result is None

    def test_custom_dir_task_returns_none(self):
        result = DocumentParser._infer_parent_feature_id(
            Path("/abs/todos/TICKET-1/index.md"),
            directory="task",
            rel_path="todos/TICKET-1/index.md",
        )
        assert result is None

    def test_none_rel_path_falls_back(self):
        result = DocumentParser._infer_parent_feature_id(
            Path("requirement/auth/login/index.md"),
            directory=None,
            rel_path=None,
        )
        assert result == "auth"


# ---------------------------------------------------------------------------
# _extract_feature_id with directory/rel_path arguments
# ---------------------------------------------------------------------------


class TestExtractFeatureIdWithDirectory:
    def test_index_md_in_custom_dir(self):
        # reqs/auth/index.md → 'auth' (parent dir is not "reqs")
        result = DocumentParser._extract_feature_id(
            {},
            Path("/abs/reqs/auth/index.md"),
            directory="requirement",
            rel_path="reqs/auth/index.md",
        )
        assert result == "auth"

    def test_index_md_directly_under_custom_base(self):
        # reqs/index.md → parent is "reqs" which is in skip list → keep "index"
        result = DocumentParser._extract_feature_id(
            {},
            Path("/abs/reqs/index.md"),
            directory="requirement",
            rel_path="reqs/index.md",
        )
        assert result == "index"

    def test_frontmatter_overrides(self):
        result = DocumentParser._extract_feature_id(
            {"feature-id": "my-feat"},
            Path("/abs/reqs/auth/index.md"),
            directory="requirement",
            rel_path="reqs/auth/index.md",
        )
        assert result == "my-feat"
