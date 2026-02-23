# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

AI-SDD Workflow のドキュメント管理 CLI ツール（`sdd-cli`）。`.sdd/` 配下の Markdown ドキュメントを SQLite FTS5 でインデックス化し、全文検索・依存関係可視化を提供する。[AI-SDD Workflow プラグイン](https://github.com/ToshikiImagawa/ai-sdd-workflow) と連携して動作する。

## 開発コマンド

```bash
# セットアップ（依存関係インストール）
uv sync --dev

# テスト実行
uv run pytest

# 単一テストファイル実行
uv run pytest tests/test_cli.py

# 単一テスト関数実行
uv run pytest tests/test_cli.py::test_cli_help

# Lint
uv run ruff check .

# Lint（自動修正）
uv run ruff check --fix .

# フォーマットチェック
uv run ruff format --check .

# 型チェック（src のみ対象、テストは対象外）
uv run mypy src/sdd_cli/

# CLI 実行（開発環境）
uv run sdd-cli --help

# パッケージビルド
uv build
```

## アーキテクチャ

### パッケージ構成（`src/sdd_cli/`）

- **`__init__.py`**: バージョン定義（`__version__`）
- **`cache.py`**: キャッシュディレクトリ管理。XDG Base Directory 準拠で `~/.cache/sdd-cli/{project}.{hash}/` にプロジェクト別キャッシュを生成
- **`cli.py`**: Click ベースの CLI エントリーポイント。`main` コマンドグループを定義（`pyproject.toml` の `[project.scripts]` から参照）
- **`types.py`**: TypedDict 型定義の一元管理（`DocumentInfo`, `ScanResult`, `ParsedDocument`, `DocumentRecord`, `SearchResult`, `GraphNode`, `GraphEdge`, `DependencyGraph`）
- **`commands/`**: CLI サブコマンド実装（`index`, `search`, `visualize`, `cache`）
- **`indexer/`**: ドキュメントのスキャン・パース・インデックス構築
- **`visualizer/`**: 依存関係分析・HTTP サーバー・Web ビューア

### 主要な処理フロー

**インデックス構築** (`sdd-cli index`):
`DocumentScanner` → `.sdd/` 配下の Markdown スキャン → `DocumentParser` → frontmatter 解析・メタデータ抽出 → `IndexDB` → SQLite FTS5 (trigram tokenizer) に登録

**検索** (`sdd-cli search`):
`IndexDB.search()` → FTS5 クエリ + フィルタ（feature_id, tag, directory）→ snippet 付き結果出力

**可視化** (`sdd-cli visualize`):
`IndexDB.get_all_documents()` → `DependencyAnalyzer` → 依存関係グラフ生成（explicit/implicit/parent-child/link）→ JSON 出力 → HTTP サーバー起動 → Mermaid.js でブラウザ表示

### 型システム

`types.py` で主要データ構造を TypedDict として定義。データフローに沿った型の流れ:
- Scanner: `ScanResult`（`DocumentInfo` を継承、`full_path` 追加）
- Parser: `ParsedDocument`
- DB: `DocumentInfo` + `ParsedDocument` → `DocumentRecord` / `SearchResult`
- Analyzer: `DocumentRecord` → `DependencyGraph`（`GraphNode` + `GraphEdge`）

### ドキュメント分類ルール（`parser.py`）

- パス内 `/requirement/` → "requirement"
- パス内 `/task/` → "task"
- ファイル名 `_design.md` → "design"
- ファイル名 `_spec.md` → "spec"
- feature_id は frontmatter (`feature-id`, `feature_id`, `id`) またはファイル名から推定
- parent_feature_id はディレクトリネスト階層から算出

### 依存関係の推定方法（`analyzer.py`）

1. **Explicit**: frontmatter `depends_on` フィールド
2. **Implicit**: ファイルタイプ順序（requirement → spec → design → task）
3. **Parent-Child**: ディレクトリ階層の親子関係
4. **Link**: Markdown 内の相対リンク（task ファイルのみ）

## 環境変数

- `SDD_ROOT`: SDD ルートディレクトリ（デフォルト: `.sdd`）
- `SDD_REQUIREMENT_DIR`: requirement ディレクトリ名（デフォルト: `requirement`）
- `SDD_SPECIFICATION_DIR`: specification ディレクトリ名（デフォルト: `specification`）
- `SDD_TASK_DIR`: task ディレクトリ名（デフォルト: `task`）

## テスト構成

- `conftest.py` にはフィクスチャのみ配置し、ヘルパー関数は `tests/helpers.py` に分離
- テスト用ヘルパー: `write_md()`（Markdown ファイル作成）、`sample_doc_info()`、`sample_parsed_data()`（サンプルデータ生成）
- `pyproject.toml` に `pythonpath = ["tests"]` を設定済み（`helpers.py` の import を可能にするため）

## CI パイプライン

GitHub Actions (`.github/workflows/ci.yml`):
- **Lint**: Ubuntu / Python 3.13 で `ruff check`, `ruff format --check`, `mypy`
- **Test**: Ubuntu + macOS × Python 3.9, 3.11, 3.13 のマトリックス

## コードスタイル

- Ruff: `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`, `RUF` ルールセット、行長 120 文字、Python 3.9 ターゲット
- mypy: `check_untyped_defs = true`, `disallow_untyped_defs = false`（段階的導入）
- Python 3.9〜3.13 互換性を維持する（`importlib.resources` の互換処理あり）

## AI-SDD Instructions (v3.1.1)

<!-- sdd-workflow version: "3.1.1" -->

This project follows AI-SDD (AI-driven Specification-Driven Development) workflow.

### Document Operations

When operating files under `.sdd/` directory, refer to `.sdd/AI-SDD-PRINCIPLES.md` to ensure proper AI-SDD workflow compliance.

**Trigger Conditions**:

- Reading or modifying files under `.sdd/`
- Creating new specifications, design docs, or requirement docs
- Implementing features that reference `.sdd/` documents

### Directory Structure

Supports both flat and hierarchical structures.

**Flat Structure (for small to medium projects)**:

    .sdd/
    |- CONSTITUTION.md               # Project principles (top-level)
    |- PRD_TEMPLATE.md               # PRD template for this project
    |- SPECIFICATION_TEMPLATE.md     # Abstract specification template
    |- DESIGN_DOC_TEMPLATE.md        # Technical design template
    |- requirement/                  # PRD (Product Requirements Documents)
    |   |- {feature-name}.md
    |- specification/                # Specifications and designs
    |   |- {feature-name}_spec.md    # Abstract specification
    |   |- {feature-name}_design.md  # Technical design
    |- task/                         # Temporary task logs
        |- {ticket-number}/

**Hierarchical Structure (for medium to large projects)**:

    .sdd/
    |- CONSTITUTION.md               # Project principles (top-level)
    |- PRD_TEMPLATE.md               # PRD template for this project
    |- SPECIFICATION_TEMPLATE.md     # Abstract specification template
    |- DESIGN_DOC_TEMPLATE.md        # Technical design template
    |- requirement/                  # PRD (Product Requirements Documents)
    |   |- {feature-name}.md         # Top-level feature
    |   |- {parent-feature}/         # Parent feature directory
    |       |- index.md              # Parent feature overview & requirements list
    |       |- {child-feature}.md    # Child feature requirements
    |- specification/                # Specifications and designs
    |   |- {feature-name}_spec.md    # Top-level feature
    |   |- {feature-name}_design.md
    |   |- {parent-feature}/         # Parent feature directory
    |       |- index_spec.md         # Parent feature abstract spec
    |       |- index_design.md       # Parent feature technical design
    |       |- {child-feature}_spec.md   # Child feature abstract spec
    |       |- {child-feature}_design.md # Child feature technical design
    |- task/                         # Temporary task logs
        |- {ticket-number}/

### File Naming Convention (Important)

**Warning: The presence of suffixes differs between requirement and specification. Do not confuse them.**

| Directory         | File Type        | Naming Pattern                                 | Example                                   |
|:------------------|:-----------------|:-----------------------------------------------|:------------------------------------------|
| **requirement**   | All files        | `{name}.md` (no suffix)                        | `user-login.md`, `index.md`               |
| **specification** | Abstract spec    | `{name}_spec.md` (`_spec` suffix required)     | `user-login_spec.md`, `index_spec.md`     |
| **specification** | Technical design | `{name}_design.md` (`_design` suffix required) | `user-login_design.md`, `index_design.md` |

#### Naming Pattern Quick Reference

```
# Correct Naming
requirement/auth/index.md              # Parent feature overview (no suffix)
requirement/auth/user-login.md         # Child feature requirements (no suffix)
specification/auth/index_spec.md       # Parent feature abstract spec (_spec required)
specification/auth/index_design.md     # Parent feature technical design (_design required)
specification/auth/user-login_spec.md  # Child feature abstract spec (_spec required)
specification/auth/user-login_design.md # Child feature technical design (_design required)

# Incorrect Naming (never use these)
requirement/auth/index_spec.md         # requirement doesn't need _spec
specification/auth/user-login.md       # specification requires _spec/_design
specification/auth/index.md            # specification requires _spec/_design
```

### Document Link Convention

Follow these formats for markdown links within documents:

| Link Target    | Format                                     | Link Text             | Example                                              |
|:---------------|:-------------------------------------------|:----------------------|:-----------------------------------------------------|
| **File**       | `[filename.md](path or URL)`               | Include filename      | `[user-login.md](../requirement/auth/user-login.md)` |
| **Directory**  | `[directory-name](path or URL/index.md)`   | Directory name only   | `[auth](../requirement/auth/index.md)`               |

This convention makes it visually clear whether the link target is a file or directory.
