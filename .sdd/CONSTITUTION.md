# Project Constitution

**Version**: 1.0.0
**Last Updated**: 2026-02-23
**Status**: Active

## Purpose

This document defines the non-negotiable principles and standards that govern the sdd-cli project's development. All code, specifications, and design decisions must align with these principles.

## Principle Hierarchy

```
1. Business Principles (Highest Priority)
   ↓
2. Architecture Principles
   ↓
3. Development Methodology Principles
   ↓
4. Technical Constraints
```

Higher priority principles take precedence over lower priority principles.

---

## 1. Business Principles (Highest Priority)

### B-001: AI-SDD Workflow Integration

**Principle**: sdd-cli は AI-SDD Workflow プラグインと連携して動作する CLI ツールであり、SDD ワークフロー（Specify → Plan → Tasks → Implement）を支援することが最優先目的である

**Scope**: All features and design decisions

**Validation Method**:

- [ ] 新機能が SDD ワークフローのいずれかのフェーズを支援するか
- [ ] `.sdd/` ディレクトリ構造の規約に準拠しているか
- [ ] AI-SDD プラグインとの互換性が維持されているか

**Violation Examples**:

- SDD ワークフローと無関係な機能の追加
- `.sdd/` ディレクトリ構造の規約を無視した実装

**Compliant Examples**:

- ドキュメントインデックス・検索機能による仕様参照の効率化
- 依存関係可視化によるドキュメント間トレーサビリティの支援

---

### B-002: CLI First

**Principle**: すべての機能は CLI インターフェースを第一に設計し、スクリプトやパイプラインから利用可能であること

**Scope**: All user-facing features

**Validation Method**:

- [ ] CLI コマンドとして利用可能か
- [ ] `--quiet` や `--json` 等のマシンフレンドリーな出力オプションがあるか
- [ ] 非対話的実行が可能か（CI/CD 対応）

**Violation Examples**:

- GUI のみで利用可能な機能
- 対話的入力を必須とするコマンド（オプションでのバイパスなし）

**Compliant Examples**:

- `sdd-cli index` でバッチ実行可能なインデックス構築
- `sdd-cli search --json` で他ツールとパイプ連携可能な検索

---

## 2. Architecture Principles

### A-001: Library-First

**Principle**: 既存ライブラリを最大限活用し、車輪の再発明を避ける

**Scope**: All implementations

**Validation Method**:

- [ ] 実装前に既存ライブラリを調査したか
- [ ] カスタム実装の場合、明確な理由があるか

**Violation Examples**:

- ライブラリ調査なしのカスタム実装
- 既知の問題（YAML パース、SQLite 操作等）の独自実装

**Compliant Examples**:

- YAML frontmatter 解析に python-frontmatter を使用
- CLI フレームワークに Click を使用
- 全文検索に SQLite FTS5 を活用

---

### A-002: Layered Architecture

**Principle**: レイヤーを分離し、上位から下位への単方向の依存フローを維持する

**Scope**: All module designs

**Validation Method**:

- [ ] 依存方向が CLI (commands/) → 処理層 (indexer/, visualizer/) → データ層 (db, cache) に従っているか
- [ ] 下位レイヤーが上位レイヤーに依存していないか
- [ ] 型定義 (types.py) が独立しているか

**Violation Examples**:

- `indexer/db.py` が `commands/` モジュールに依存
- `types.py` が具体的な実装モジュールに依存
- `cache.py` が CLI コマンドロジックに依存

**Compliant Examples**:

- `commands/index.py` → `indexer/scanner.py` → `indexer/parser.py` → `indexer/db.py` の単方向フロー
- `types.py` は TypedDict 定義のみで外部依存なし

### Layer Structure

```
commands/          # CLI layer (presentation)
    ↓
indexer/           # Processing layer (application)
visualizer/        # Processing layer (application)
    ↓
indexer/db.py      # Data access layer
cache.py           # Data access layer
config.py          # Configuration layer
    ↓
types.py           # Type definitions (no dependencies)
```

---

### A-003: Minimal Dependencies

**Principle**: 外部依存を最小限に保つ。ランタイム依存は Click と python-frontmatter のみ

**Scope**: All production code

**Validation Method**:

- [ ] 新しいランタイム依存の追加に明確な正当性があるか
- [ ] 標準ライブラリで実現可能な場合は標準ライブラリを優先しているか
- [ ] 開発依存（dev dependencies）とランタイム依存を分離しているか

**Violation Examples**:

- HTTP クライアントライブラリの追加（標準ライブラリの urllib で十分な場合）
- 大規模な ORM ライブラリの導入（sqlite3 で十分な場合）

**Compliant Examples**:

- SQLite は Python 標準ライブラリの sqlite3 を使用
- HTTP サーバーは Python 標準ライブラリの http.server を使用
- Ruff, mypy, pytest は開発依存として分離

---

## 3. Development Methodology Principles

### D-001: Specification-Driven Development

**Principle**: 仕様書なしに実装を開始しない。AI-SDD ワークフローに従い Specify → Plan → Tasks → Implement の順序で開発する

**Scope**: All new features and significant changes

**Validation Method**:

- [ ] PRD（`requirement/*.md`）が存在するか
- [ ] `*_spec.md` が存在するか
- [ ] `*_design.md` が存在するか
- [ ] 仕様書が最新の状態（実装前に更新）か

**Violation Examples**:

- 口頭指示のみでの実装開始
- 古い仕様書のままでの実装
- 仕様書の作成を実装後に回す

**Compliant Examples**:

- Specify → Plan → Tasks → Implement フローの遵守
- 仕様書を Single Source of Truth として管理

---

### D-002: Test Coverage 80%+

**Principle**: 主要機能のユニットテスト + 統合テストでカバレッジ 80% 以上を維持する

**Scope**: All core features

**Validation Method**:

- [ ] テストカバレッジが 80% 以上か
- [ ] 主要パスのテストが存在するか
- [ ] エッジケース（境界値、エラーケース）がテストされているか
- [ ] CI マトリックス（Python 3.9, 3.11, 3.13 × Ubuntu, macOS）で全テスト通過するか

**Violation Examples**:

- テストなしでのマージ
- カバレッジ 80% 未満の状態でのリリース
- 特定の Python バージョンでのみ動作するコード

**Compliant Examples**:

- 新機能追加時にユニットテスト + 統合テストを同時作成
- conftest.py にフィクスチャ、tests/helpers.py にヘルパー関数を配置
- `uv run pytest` で全テスト通過を確認してからコミット

---

## Development Standards

### Code Quality

| Standard        | Requirement                    | Tool         | Enforcement     |
|:----------------|:-------------------------------|:-------------|:----------------|
| **Linting**     | Zero errors, zero warnings     | Ruff         | CI/CD + pre-commit |
| **Type Safety** | check_untyped_defs enabled     | mypy         | CI/CD           |
| **Line Length** | Maximum 120 characters         | Ruff         | CI/CD           |
| **Import Sort** | isort-compatible ordering      | Ruff (I)     | CI/CD           |

### Documentation

| Standard           | Requirement                            | Location              | Update Frequency      |
|:-------------------|:---------------------------------------|:----------------------|:----------------------|
| **PRD**            | All features have `requirement/*.md`   | `.sdd/requirement/`   | Before specification  |
| **Specifications** | All features have `*_spec.md`          | `.sdd/specification/` | Before implementation |
| **Design Docs**    | All implementations have `*_design.md` | `.sdd/specification/` | During design phase   |
| **README**         | Up-to-date setup instructions          | Project root          | As needed             |

### Testing

| Standard              | Requirement                | Enforcement    | Exemptions |
|:----------------------|:---------------------------|:---------------|:-----------|
| **Unit Coverage**     | >= 80% line coverage       | CI/CD          | -          |
| **Integration Tests** | All main flows covered     | Manual review  | -          |
| **Edge Cases**        | Boundary conditions tested | Code review    | -          |
| **Multi-version**     | Python 3.9, 3.11, 3.13    | CI matrix      | -          |

### Security

| Standard                | Requirement                    | Enforcement         | Review Frequency |
|:------------------------|:-------------------------------|:--------------------|:-----------------|
| **Input Validation**    | All user inputs validated      | Code review         | Every PR         |
| **Path Traversal**      | No path traversal allowed      | Code review         | Every PR         |
| **Secrets Management**  | No secrets in code             | .gitignore review   | Every commit     |
| **SQL Injection**       | Parameterized queries only     | Code review         | Every PR         |

---

## Architectural Constraints

### Technology Stack

| Layer            | Allowed Technologies                      | Prohibited                          | Rationale                      |
|:-----------------|:------------------------------------------|:------------------------------------|:-------------------------------|
| **Language**     | Python 3.9+                               | Python 2.x, < 3.9                  | LTS support, type hints        |
| **CLI**          | Click                                     | argparse (direct), sys.argv        | Consistency, composability     |
| **Database**     | SQLite (stdlib sqlite3), FTS5             | External DB engines                 | Zero-config, embedded          |
| **Frontmatter**  | python-frontmatter                        | Manual YAML parsing                 | Reliability, edge cases        |
| **Build**        | Hatchling, uv                             | setuptools (legacy), pip (direct)   | Modern Python packaging        |
| **Linting**      | Ruff                                      | flake8, pylint, black, isort        | All-in-one, fast               |
| **Type Check**   | mypy                                      | pyright (for now)                   | Consistency                    |
| **Testing**      | pytest                                    | unittest (direct)                   | Fixtures, plugins              |

**Exception Process**: Propose changes via Issue with team approval

### Module Organization

```
src/sdd_cli/
├── __init__.py          # Version definition
├── cli.py               # Click CLI entry point
├── config.py            # Configuration resolution
├── cache.py             # XDG cache management
├── types.py             # TypedDict definitions (no dependencies)
├── commands/            # CLI subcommands
│   ├── init.py          # Project initialization
│   ├── index.py         # Index building
│   ├── search.py        # Document search
│   ├── visualize.py     # Dependency visualization
│   └── cache.py         # Cache management
├── indexer/             # Document processing
│   ├── scanner.py       # File scanning
│   ├── parser.py        # Frontmatter parsing
│   └── db.py            # SQLite FTS5 operations
└── visualizer/          # Visualization processing
    ├── analyzer.py      # Dependency analysis
    ├── graph_builder.py # Graph construction
    └── server.py        # HTTP server
```

**Dependency Rules**:

- `types.py` depends on nothing
- `config.py`, `cache.py` depend on `types.py` only
- `indexer/` depends on `types.py`, `config.py`, `cache.py`
- `visualizer/` depends on `types.py`, `indexer/db.py`
- `commands/` depends on all layers (orchestration)

---

## Decision-Making Framework

When facing technical trade-offs, prioritize in this order:

1. **Correctness** - Does it meet specifications?
2. **Compatibility** - Does it work on Python 3.9-3.13?
3. **Simplicity** - Is it the simplest solution?
4. **Security** - Is it safe (SQL injection, path traversal)?
5. **Performance** - Is it fast enough for typical project sizes?
6. **Maintainability** - Can we maintain it?

**Tiebreaker**: Choose option that's easier to change later.

---

## Quality Gates

### Pre-Commit

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run pytest` passes locally

### Pre-PR

- [ ] All tests pass on target Python versions
- [ ] Coverage >= 80%
- [ ] `uv run mypy src/sdd_cli/` passes
- [ ] Spec/design docs updated if applicable

### Pre-Merge

- [ ] CI/CD pipeline green (lint + test matrix)
- [ ] No merge conflicts
- [ ] Documentation updated

### Pre-Release

- [ ] All PRDs have corresponding specs
- [ ] CHANGELOG updated
- [ ] Version bumped in `__init__.py`

---

## 4. Technical Constraints

### T-001: Python Version Compatibility

**Principle**: Python 3.9 から 3.13 までの全バージョンで動作すること

**Scope**: All source code

**Validation Method**:

- [ ] Python 3.9 で利用できない構文を使用していないか（`match` 文、`X | Y` 型構文等）
- [ ] `from __future__ import annotations` が必要な場合は追加しているか
- [ ] `importlib.resources` の互換処理が適切か
- [ ] CI マトリックスで全バージョンテストが通過するか

**Violation Examples**:

- Python 3.10+ の `match` 文の使用
- Python 3.10+ の `X | Y` 型ユニオン構文の使用
- Python 3.9 で利用不可な標準ライブラリ API の使用

**Compliant Examples**:

- `Union[X, Y]` や `Optional[X]` の使用（3.9 互換）
- `if/elif` チェーンの使用（`match` の代替）
- `importlib.resources` の互換ラッパーの利用

---

### T-002: SQL Safety

**Principle**: すべての SQL クエリはパラメータ化クエリを使用し、SQL インジェクションを防止する

**Scope**: All database operations (indexer/db.py)

**Validation Method**:

- [ ] 文字列フォーマットによる SQL 構築をしていないか
- [ ] `?` プレースホルダーによるパラメータ化を使用しているか
- [ ] FTS5 クエリ入力が適切にサニタイズされているか

**Violation Examples**:

- `f"SELECT * FROM docs WHERE id = '{user_input}'"` のような文字列補間
- ユーザー入力をそのまま FTS5 MATCH クエリに渡す

**Compliant Examples**:

- `cursor.execute("SELECT * FROM docs WHERE id = ?", (user_input,))`
- FTS5 クエリのトークンをエスケープ処理してから使用

---

### T-003: Path Safety

**Principle**: ファイルパス操作は安全に行い、パストラバーサル攻撃を防止する

**Scope**: All file operations (scanner, config, cache)

**Validation Method**:

- [ ] `pathlib.Path` を使用しているか
- [ ] ユーザー入力パスを `.resolve()` で正規化しているか
- [ ] プロジェクトルート外へのアクセスを防止しているか

**Violation Examples**:

- `os.path.join(base, user_input)` でパストラバーサル可能な状態
- `../../../etc/passwd` のような入力を検証なしに受け入れ

**Compliant Examples**:

- `pathlib.Path` による安全なパス構築
- `resolve()` 後にプロジェクトルート配下であることを確認

---

## Compliance

### Enforcement Mechanisms

**Automated**:

- CI/CD pipeline: Ruff lint, Ruff format, mypy, pytest (multi-version matrix)
- `.gitignore`: Secrets and build artifacts excluded

**Manual**:

- Code review (architecture, design decisions)
- Specification review (PRD/spec/design consistency)

### Violation Handling

| Severity     | Action                         | Example                              |
|:-------------|:-------------------------------|:-------------------------------------|
| **Critical** | Block merge immediately        | No tests, SQL injection, 3.9 incompatible |
| **Major**    | Require explicit justification | New runtime dependency, missing spec |
| **Minor**    | Fix in current PR or follow-up | Minor doc updates, style issues      |

### Exception Process

When principle compliance is not possible:

1. **Document**: Create Issue describing the exception
2. **Justify**: Explain why principle cannot be followed
3. **Mitigate**: Describe compensating controls
4. **Track**: Add to technical debt log
5. **Plan**: Set timeline for resolution (if temporary)

---

## Version History

### v1.0.0 (2026-02-23)

**Initial constitution established**

- B-001: AI-SDD Workflow Integration
- B-002: CLI First
- A-001: Library-First
- A-002: Layered Architecture
- A-003: Minimal Dependencies
- D-001: Specification-Driven Development
- D-002: Test Coverage 80%+
- T-001: Python Version Compatibility (3.9-3.13)
- T-002: SQL Safety
- T-003: Path Safety

---

## Amendment Process

### Minor Version (x.Y.z)

**Scope**: Clarifications, additional examples, enforcement method updates

**Process**:

1. Propose change in PR
2. Review and approval
3. Update version
4. Communicate changes

### Major Version (X.y.z)

**Scope**: New principles, changes to existing principles, removal of principles

**Process**:

1. Create Issue describing the change
2. Discussion and review
3. Update version
4. Create migration guide for affected code

---

## Related Documents

| Document                         | How to Reference                                          |
|:---------------------------------|:----------------------------------------------------------|
| `.sdd/PRD_TEMPLATE.md`          | PRD must follow this template structure                   |
| `.sdd/SPECIFICATION_TEMPLATE.md` | Specifications reference principles                      |
| `.sdd/DESIGN_DOC_TEMPLATE.md`   | Design docs include principle compliance checklist        |
| `requirement/*.md`               | PRDs define business requirements                         |
| `*_spec.md`                      | Specifications describe system design based on principles |
| `*_design.md`                    | Design documents clearly state principle compliance       |

---

*This constitution is a living document. It should evolve with the project's needs.*
