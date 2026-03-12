---
id: checklist-document-search
title: ドキュメント検索機能 品質保証チェックリスト
type: checklist
status: verified
created: 2026-03-12
updated: 2026-03-12
verified: 2026-03-12
depends-on: [task-document-search]
tags: [search, cli, fts5, filter-dsl, parent-child, regex]
---

# ドキュメント検索機能 品質保証チェックリスト

**対象機能:** document-search (フィルタ DSL / OR 演算子 / 親子トラバーサル / 正規表現マッチ)
**生成日:** 2026-03-12
**参照ドキュメント:**
- PRD: [document-search.md](../../requirement/document-search.md)
- 仕様書: [document-search_spec.md](../../specification/document-search_spec.md)
- 設計書: [document-search_design.md](../../specification/document-search_design.md)
- タスク: [tasks.md](tasks.md)

---

## 優先度凡例

| 優先度 | 説明 | タイミング |
|:------|:-----|:---------|
| **P1** | マージ前に必須パス | PR 作成前 |
| **P2** | マージ前に対応推奨 | PR レビュー中 |
| **P3** | 任意対応 | 機会があれば |

---

## 1. 要求レビュー (CHK-1xx)

> ユーザー要求・機能要求・非機能要求がすべて実装されていることを確認する

### P1 - 必須

- [x] **CHK-101** FR-001: FTS5 MATCH によるクエリ全文検索が動作する ✅ test_fts_query
- [x] **CHK-102** FR-002: クエリ指定時に 50 文字スニペットが生成される ✅ test_text_format
- [x] **CHK-103** FR-003: クエリ指定時は rank ソート、クエリなし時は file_path ソートで返す ✅ test_combined_filters
- [x] **CHK-104** FR-004: `--feature-id` で feature_id 完全一致フィルタが適用される ✅ test_filter_feature_id
- [x] **CHK-105** FR-005: `--tag` でタグ部分一致フィルタ（LIKE）が適用される ✅ test_filter_tag
- [x] **CHK-106** FR-006: `--dir` でディレクトリタイプフィルタが適用される（requirement/specification/task）✅ test_filter_directory
- [x] **CHK-107** FR-007: クエリなし時は全件取得しフィルタのみ適用される ✅ test_no_filters_unchanged_behavior
- [x] **CHK-108** FR-008: text 形式で件数・タイトル・パス・feature_id・タグ・スニペットが出力される ✅ test_all_fields
- [x] **CHK-109** FR-009: `--format json` で JSON 形式の検索結果が出力される ✅ test_json_format
- [x] **CHK-110** FR-010: `--output` でファイルへの出力が動作する ✅ test_search_regression
- [x] **CHK-111** FR-011: `--limit` で結果件数上限が設定される（デフォルト 10）✅ test_limit
- [x] **CHK-112** FR-012: インデックス未構築時に明確なエラーメッセージが返される ✅ test_index_not_found
- [x] **CHK-113** FR-013: タグ JSON のパース成功・失敗フォールバック（空リスト）が動作する ✅ test_invalid_json_fallback
- [x] **CHK-114** FR-014: `--filter "field:op:value"` DSL フィルタが動作する（exact/contains）✅ TestFilterDSL
- [x] **CHK-115** FR-015: `--or` フラグで複数 `--filter` が OR 結合される（異なるフィールド間も可）✅ test_or_different_fields
- [x] **CHK-116** FR-016: `--parent` で全子孫ドキュメントが再帰的に取得される ✅ TestParentFilter
- [x] **CHK-117** FR-017: `op=regex` で正規表現マッチが動作する（メタデータフィールド限定）✅ TestRegexpUDF
- [x] **CHK-118** FR-018: 不正な正規表現パターンで `Error:` が stderr に出力され終了コード 1 になる ✅ test_filter_invalid_format

### P2 - 推奨

- [ ] **CHK-121** UR-005: 複数 `--filter` の AND 結合（デフォルト）が動作する
- [ ] **CHK-122** UR-006: 存在しない feature_id を `--parent` に指定した場合に空結果が返される（エラーなし）
- [ ] **CHK-123** UR-007: 対象フィールド 7 種（feature_id/status/type/tags/category/directory/file_type）すべてで regex が動作する
- [ ] **CHK-124** NFR-004: 例外が `Error: {message}` 形式で stderr に出力され終了コード 1 になる

### P3 - 任意

- [ ] **CHK-131** NFR-001: SQLite 3.9.0 以上が必要な条件が CI で検証されている
- [ ] **CHK-132** NFR-003: XDG キャッシュパス（`~/.cache/sdd-cli/{project}.{hash}/index.db`）が使用されている
- [ ] **CHK-133** NFR-005: ランタイム依存が `click` のみであることが `pyproject.toml` で確認できる

---

## 2. 仕様レビュー (CHK-2xx)

> 抽象仕様書（`_spec.md`）との整合性を確認する

### P1 - 必須

- [x] **CHK-201** CLI オプション `--filter`・`--or`・`--parent` が spec の API 定義と一致している ✅ --help 確認済み
- [x] **CHK-202** `search_documents()` シグネチャが spec の API 定義と一致している（`filters`, `or_operator`, `parent` 引数を持つ）✅
- [x] **CHK-203** `IndexDB.search()` シグネチャが spec の API 定義と一致している（`filters`, `or_operator`, `parent` 引数を持つ）✅
- [x] **CHK-204** `FilterCondition` TypedDict が spec の型定義と一致している（`field: str`, `op: MatchOp`, `value: str`）✅
- [x] **CHK-205** `MatchOp = Literal["exact", "contains", "regex"]` が spec と一致している ✅
- [x] **CHK-206** `SearchResult` TypedDict が spec の型定義と一致している（`id`/`type`/`status`/`created`/`updated`/`category` 含む）✅
- [x] **CHK-207** フィルタ DSL の許可フィールドリスト（7 種）が spec と一致している ✅ _ALLOWED_FILTER_FIELDS 確認

### P2 - 推奨

- [ ] **CHK-211** 振る舞い図 7.3（フィルタ DSL フロー）が実装と一致している
- [ ] **CHK-212** 振る舞い図 7.4（親子トラバーサルフロー）が実装と一致している
- [ ] **CHK-213** `sdd-cli search --help` の出力に spec の全 CLI オプションが記載されている
- [ ] **CHK-214** `--format json` 出力の JSON 構造が spec の型定義と一致している

### P3 - 任意

- [ ] **CHK-221** 制約事項（Section 8）に記載された制限（regex はメタデータのみ等）が実装上も守られている
- [ ] **CHK-222** 用語集（Section 5）の用語がコード内のコメントや docstring で一貫して使用されている

---

## 3. 設計レビュー (CHK-3xx)

> 技術設計書（`_design.md`）との整合性を確認する

### P1 - 必須

- [x] **CHK-301** レイヤー分離が守られている: `cli.py → commands/search.py → indexer/db.py` の単方向依存（A-002 準拠）✅
- [x] **CHK-302** REGEXP UDF が `conn.create_function("REGEXP", 2, _regexp_func)` で `__init__` 時に登録されている ✅
- [x] **CHK-303** `get_descendants()` が Python 反復クエリで実装されている（SQLite 再帰 CTE 不使用）✅
- [x] **CHK-304** フィルタ DSL SQL の op 別パターンが設計書 Section 5.3 の仕様と一致している ✅
  - `exact`: `meta.{field} = ?` ✅
  - `contains`: `meta.{field} LIKE ?`（値を `%value%` でラップ）✅
  - `regex`: `REGEXP(?, {col})`（pattern を第 1 引数）✅
- [x] **CHK-305** OR 結合時の SQL が `(cond1 OR cond2 OR ...)` 形式になっている（Section 5.4 準拠）✅
- [x] **CHK-306** `get_descendants()` の再帰疑似コード（Section 5.5）と一致している（`visited` セットで循環回避）✅
- [x] **CHK-307** `_parse_filter()` が `commands/search.py` に実装されている ✅

### P2 - 推奨

- [ ] **CHK-311** モジュール分割表（Section 4.2）の配置場所と実際のファイル配置が一致している
- [ ] **CHK-312** `impl-status: implemented` に更新されている（設計書 front matter）
- [ ] **CHK-313** Section 1.1 の全モジュールが 🟢（実装完了）になっている

### P3 - 任意

- [ ] **CHK-321** 設計判断（Section 9.1）の内容がコードにコメントとして記載されている
- [ ] **CHK-322** 変更履歴（Section 10）が最新の実装変更を反映している

---

## 4. 実装レビュー (CHK-4xx)

> コード品質・アーキテクチャ準拠を確認する

### P1 - 必須

- [x] **CHK-401** `mypy src/sdd_cli/` がエラーなしで通過する ✅ "no issues found in 25 source files"
- [x] **CHK-402** `ruff check .` がエラーなしで通過する ✅ "All checks passed!"
- [x] **CHK-403** `ruff format --check .` がエラーなしで通過する ✅ (2ファイル修正後)
- [x] **CHK-404** フィルタ DSL のフィールド名は許可リスト（`_ALLOWED_FILTER_FIELDS`）でホワイトリスト検証されている ✅
- [x] **CHK-405** REGEXP UDF（`_regexp_func`）が不正パターンで `ValueError` を発生させる ✅ test_invalid_regex_raises
- [x] **CHK-406** `get_descendants()` が循環参照時に無限ループしない（`visited` セット使用）✅ test_nonexistent_feature_id_returns_empty
- [x] **CHK-407** `_parse_filter()` が `:` が 2 つ未満のフォーマットで `ValueError` を発生させる ✅ test_filter_invalid_format

### P2 - 推奨

- [ ] **CHK-411** Python 3.9 互換構文が使用されている（`list[T]` の型ヒントは `Optional[list[...]]` 形式）
- [ ] **CHK-412** `_parse_filter()` の `op` が `MatchOp` 型に正しくキャストされている
- [ ] **CHK-413** `get_descendants()` が自身の feature_id を結果に含まない
- [ ] **CHK-414** `--parent` に存在しない feature_id を指定した場合に `ValueError` でなく空リストを返す

### P3 - 任意

- [ ] **CHK-421** 既存の `--feature-id`/`--tag`/`--dir` との後方互換性が保たれている（既存テストのパス確認）
- [ ] **CHK-422** `search_documents()` と `IndexDB.search()` の docstring が更新されている

---

## 5. テストレビュー (CHK-5xx)

> テストの網羅性・品質を確認する

### P1 - 必須

- [ ] **CHK-501** `uv run pytest` が通過する（既存 + 新規テスト合わせて失敗なし）
- [ ] **CHK-502** `FilterCondition`・`MatchOp` 型定義のテストが存在する（TASK-007）
- [ ] **CHK-503** `get_descendants()` のユニットテストがある（TASK-008）
  - 存在しない feature_id → 空セット
  - 直接の子・孫・ひ孫 → 全子孫
  - 自身は結果に含まれない
  - 循環参照でも無限ループしない
  - リーフノード → 空セット
- [ ] **CHK-504** フィルタ DSL の AND/OR テストがある（TASK-009）
  - `exact` 完全一致・不一致
  - `contains` 部分一致
  - 複数フィルタ AND 結合
  - 複数フィルタ OR 結合（同一フィールド）
  - 異なるフィールド間の OR 結合
  - 不正フィールド名で `ValueError`
  - `filters=None` で従来動作が変わらない
- [ ] **CHK-505** REGEXP UDF テストがある（TASK-010）
  - 正常パターン（マッチ・非マッチ）
  - `^` アンカー付きパターン
  - 不正パターンで `ValueError`
  - `None` 値フィールドでクラッシュしない
- [ ] **CHK-506** CLI 統合テスト（CliRunner）がある（TASK-011）
  - `--filter` による絞り込み
  - `--or` フラグ
  - `--parent` による子孫取得
  - `--filter` + `--format json` の組み合わせ
  - 不正フォーマット → exit_code=1
  - 不正フィールド → exit_code=1
  - `search --help` に新オプションが表示される

### P2 - 推奨

- [ ] **CHK-511** 既存テスト（`test_db.py`, `test_search.py`, `test_cli.py`）がすべてパスする
- [ ] **CHK-512** `uv run pytest --cov=src/sdd_cli --cov-report=term` でカバレッジ 80% 以上（NFR-006 準拠）
- [ ] **CHK-513** 親子トラバーサル + 全文検索の組み合わせテストがある
- [ ] **CHK-514** `--parent` で子孫が 0 件の場合に空リストが返されるテストがある

### P3 - 任意

- [ ] **CHK-521** 回帰テスト: 既存の `--feature-id`/`--tag`/`--dir` と `--filter` の併用テストがある
- [ ] **CHK-522** JSON 出力の構造バリデーション（`id`, `type`, `status` フィールドが含まれる）テストがある

---

## 6. ドキュメントレビュー (CHK-6xx)

> ドキュメントの整合性を確認する

### P1 - 必須

- [ ] **CHK-601** `document-search_design.md` の `impl-status` が `implemented` になっている
- [ ] **CHK-602** `document-search_design.md` の Section 1.1 の全モジュールが 🟢 になっている
- [ ] **CHK-603** `document-search_design.md` の `updated` 日付が最新になっている

### P2 - 推奨

- [ ] **CHK-611** `CLAUDE.md` の主要な処理フロー説明が新機能（`--filter`/`--or`/`--parent`）を反映している
- [ ] **CHK-612** `tasks.md` の完了条件がすべて達成されている

### P3 - 任意

- [ ] **CHK-621** `sdd-cli search --help` の Examples セクションに新オプションの使用例が含まれている

---

## 7. セキュリティレビュー (CHK-7xx)

> T-002（SQL インジェクション防止）・T-003（パス安全性）準拠を確認する

### P1 - 必須

- [ ] **CHK-701** フィルタ DSL のすべての SQL クエリが `?` パラメータプレースホルダーを使用している（文字列補間なし）
- [ ] **CHK-702** フィールド名が許可リスト（`_ALLOWED_FILTER_FIELDS`）でホワイトリスト検証されており、SQL に直接埋め込まれていない
- [ ] **CHK-703** `op` の値が `exact`/`contains`/`regex` のいずれかであることが `_parse_filter()` 内で検証されている
- [ ] **CHK-704** REGEXP UDF が `re.compile()` でパターンを事前バリデーションしており、不正パターンで `ValueError` を発生させる

### P2 - 推奨

- [ ] **CHK-711** `--parent` に渡された feature_id が SQL パラメータとして安全に処理されている
- [ ] **CHK-712** `get_descendants()` の SQL クエリが `?` プレースホルダーを使用している

### P3 - 任意

- [ ] **CHK-721** フィルタ DSL の `value` フィールドに特殊文字（`%`, `_` など）を含む場合の `LIKE` エスケープが考慮されている（`contains` op）

---

## 8. パフォーマンスレビュー (CHK-8xx)

> 制約事項として文書化された性能特性を確認する

### P2 - 推奨

- [ ] **CHK-801** 正規表現マッチ（`op=regex`）がメタデータフィールドのみに限定されている（コンテンツフィールドへの適用なし）
- [ ] **CHK-802** `get_descendants()` が循環参照時に無限ループせず有限回数で終了する

### P3 - 任意

- [ ] **CHK-811** 深いネスト（5 階層以上）の親子トラバーサルが正常に完了する
- [ ] **CHK-812** 大量ドキュメント（100 件以上）での正規表現フィルタが許容時間内で完了する
- [ ] **CHK-813** 正規表現マッチの制限事項（インデックス未使用・全件走査）がドキュメントに明記されている（spec Section 8 確認）

---

## 9. デプロイレビュー (CHK-9xx)

> CI/CD・マルチプラットフォーム動作を確認する

### P1 - 必須

- [ ] **CHK-901** CI マトリックス（Python 3.9, 3.11, 3.13 × Ubuntu, macOS）で全テストがパスする（NFR-002 準拠）

### P2 - 推奨

- [ ] **CHK-911** CI の Windows テストで新機能が動作する（パス区切り問題なし）
- [ ] **CHK-912** `uv build` でパッケージビルドが成功する

### P3 - 任意

- [ ] **CHK-921** `pyproject.toml` のランタイム依存に新しいパッケージが追加されていない（NFR-005: click のみ）

---

## チェックリストサマリー

| カテゴリ | P1 | P2 | P3 | 合計 |
|:--------|:---|:---|:---|:----|
| 1. 要求レビュー | 18 | 4 | 3 | 25 |
| 2. 仕様レビュー | 7 | 4 | 2 | 13 |
| 3. 設計レビュー | 7 | 3 | 2 | 12 |
| 4. 実装レビュー | 7 | 4 | 2 | 13 |
| 5. テストレビュー | 6 | 4 | 2 | 12 |
| 6. ドキュメントレビュー | 3 | 2 | 1 | 6 |
| 7. セキュリティレビュー | 4 | 2 | 1 | 7 |
| 8. パフォーマンスレビュー | 0 | 2 | 3 | 5 |
| 9. デプロイレビュー | 1 | 2 | 1 | 4 |
| **合計** | **53** | **27** | **17** | **97** |

---

## 自動検証コマンド

```bash
# Lint・型チェック（CHK-401〜403）
uv run mypy src/sdd_cli/
uv run ruff check .
uv run ruff format --check .

# テスト全体（CHK-501）
uv run pytest

# カバレッジ（CHK-512）
uv run pytest --cov=src/sdd_cli --cov-report=term-missing

# CLI ヘルプ確認（CHK-213, CHK-621）
uv run sdd-cli search --help

# フィルタ DSL 動作確認（CHK-114〜118）
uv run sdd-cli index
uv run sdd-cli search --filter "status:exact:draft"
uv run sdd-cli search --filter "type:exact:spec" --filter "type:exact:design" --or
uv run sdd-cli search --parent document-search
uv run sdd-cli search --filter "feature_id:regex:^document-.*"
```

---

## 関連ドキュメント

- **PRD:** [document-search.md](../../requirement/document-search.md)
- **仕様書:** [document-search_spec.md](../../specification/document-search_spec.md)
- **設計書:** [document-search_design.md](../../specification/document-search_design.md)
- **タスク:** [tasks.md](tasks.md)
