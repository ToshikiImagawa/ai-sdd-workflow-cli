---
feature-id: document-search
title: ドキュメント検索機能 要求仕様書
tags: [ search, cli, fts5, query ]
---

# ドキュメント検索機能 要求仕様書

## 概要

本ドキュメントは、sdd-cli のドキュメント検索機能に関する要求仕様書（PRD）です。

SQLite FTS5 によるインデックス済みドキュメントに対して全文検索を行い、フィルタ（feature_id, tag,
directory）と組み合わせて結果を取得する機能を対象とします。CLI コマンド `sdd-cli search` がこの機能のエントリーポイントです。

---

# 1. 要求図の読み方

## 1.1. 要求タイプ

- **requirement**: 一般的な要求（ユーザー要求）
- **functionalRequirement**: 機能要求
- **designConstraint**: 設計制約（非機能要求含む）

## 1.2. リスクレベル

- **High**: 高リスク（実装が複雑、ビジネスクリティカル）
- **Medium**: 中リスク（重要だが代替可能）
- **Low**: 低リスク（実装が単純）

## 1.3. 検証方法

- **Test**: テストによる検証（自動テスト）
- **Demonstration**: デモンストレーションによる検証
- **Inspection**: インスペクション（レビュー）による検証

## 1.4. 関係タイプ

- **contains**: 包含関係（親要求が子要求を含む）
- **derives**: 派生関係（要求から別の要求が導出される）
- **traces**: トレース関係（要求間の追跡可能性）

---

# 2. 要求一覧

## 2.1. ユースケース図（概要）

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    Developer((開発者))
    IndexDB((インデックス<br/>DB))

    subgraph SddCliSearch [sdd-cli ドキュメント検索機能]
        UC1(["全文検索"])
        UC2(["フィルタ検索"])
        UC3(["結果フォーマット"])
        UC4(["ファイル出力"])
        UC5(["インデックス存在確認"])
        UC6(["スニペット生成"])
        UC7(["スコアソート"])
    end

    Developer --- UC1
    Developer --- UC2
    UC1 -.->|" &lt;&lt;include&gt;&gt; "| UC5
    UC2 -.->|" &lt;&lt;include&gt;&gt; "| UC5
    UC1 -.->|" &lt;&lt;include&gt;&gt; "| UC6
    UC1 -.->|" &lt;&lt;include&gt;&gt; "| UC7
    UC1 -.->|" &lt;&lt;include&gt;&gt; "| UC3
    UC2 -.->|" &lt;&lt;include&gt;&gt; "| UC3
    UC4 -.->|" &lt;&lt;extend&gt;&gt; "| UC3
    UC5 --- IndexDB
    UC1 --- IndexDB
    UC2 --- IndexDB
    classDef actor fill: #4a148c, stroke: #ba68c8, color: #fff
    classDef usecase fill: #bf360c, stroke: #ff8a65, color: #fff
    class Developer,IndexDB actor
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7 usecase
```

## 2.2. ユースケース図（詳細）

### 全文検索

| Actor     | Use Case      | Description                                          |
|:----------|:--------------|:-----------------------------------------------------|
| 開発者       | 全文検索 (UC1)    | `sdd-cli search "クエリ"` で FTS5 MATCH によりドキュメントを全文検索する |
| インデックス DB | スニペット生成 (UC6) | FTS5 snippet() 関数でマッチ箇所の前後文脈付きスニペットを生成する             |
| インデックス DB | スコアソート (UC7)  | FTS5 rank によるスコア順で結果をソートする                           |

### フィルタ検索

| Actor | Use Case         | Description                                   |
|:------|:-----------------|:----------------------------------------------|
| 開発者   | フィルタ検索 (UC2)     | `--feature-id`/`--tag`/`--dir` オプションで絞り込み検索する |
| -     | インデックス存在確認 (UC5) | 検索実行前にインデックス DB の存在を確認し、未構築時はエラーを返す           |

### 結果出力

| Actor | Use Case       | Description                          |
|:------|:---------------|:-------------------------------------|
| -     | 結果フォーマット (UC3) | text（デフォルト）または json 形式で検索結果をフォーマットする |
| -     | ファイル出力 (UC4)   | `--output` オプションで結果をファイルに書き出す        |

## 2.3. 機能一覧（テキスト形式）

- 全文検索
    - FTS5 MATCH によるクエリ検索（trigram tokenizer）
    - クエリなし時の全件取得（フィルタのみ適用）
    - FTS5 rank によるスコア順ソート
    - FTS5 snippet() によるスニペット生成（50 文字）
- フィルタリング
    - `--feature-id`: feature_id 完全一致フィルタ
    - `--tag`: タグ部分一致フィルタ（LIKE）
    - `--dir`: ディレクトリタイプフィルタ（requirement/specification/task）
    - 複数フィルタの AND 結合
- 結果出力
    - text 形式出力（デフォルト）
    - json 形式出力（`--format json`）
    - ファイル出力（`--output`）
    - 結果件数上限（`--limit`、デフォルト 10）
- エラーハンドリング
    - インデックス未構築時のエラーメッセージ
    - 結果なし時の "No results found." メッセージ

---

# 3. 要求図（SysML Requirements Diagram）

## 3.1. 全体要求図

```mermaid
%%{init: {'theme': 'dark'}}%%
requirementDiagram
    requirement Full_Text_Search {
        id: UR_001
        text: "開発者はインデックス済みドキュメントを全文検索できる"
        risk: high
        verifymethod: test
    }

    requirement Filtered_Search {
        id: UR_002
        text: "開発者は feature_id/tag/directory で検索結果を絞り込める"
        risk: medium
        verifymethod: test
    }

    requirement Flexible_Output {
        id: UR_003
        text: "検索結果を text/json 形式で取得しファイルにも出力できる"
        risk: low
        verifymethod: test
    }

    requirement Clear_Error_Handling {
        id: UR_004
        text: "インデックス未構築時や結果なし時に明確なメッセージを返す"
        risk: low
        verifymethod: test
    }

    functionalRequirement FTS5_Match_Query {
        id: FR_001
        text: "FTS5 MATCH でクエリ文字列にマッチするドキュメントを検索する"
        risk: high
        verifymethod: test
    }

    functionalRequirement Feature_Id_Filter {
        id: FR_004
        text: "--feature-id で feature_id 完全一致フィルタを適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Tag_Filter {
        id: FR_005
        text: "--tag でタグ部分一致フィルタ（LIKE）を適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Directory_Filter {
        id: FR_006
        text: "--dir でディレクトリタイプフィルタを適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Text_Output {
        id: FR_008
        text: "text 形式で件数・タイトル・パス・feature_id・タグ・スニペットを出力する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Json_Output {
        id: FR_009
        text: "--format json で JSON 形式の検索結果を出力する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Index_Existence_Check {
        id: FR_012
        text: "インデックス DB が存在しない場合に明確なエラーメッセージを返す"
        risk: low
        verifymethod: test
    }

    designConstraint FTS5_Trigram_Dependency {
        id: NFR_001
        text: "FTS5 trigram tokenizer に依存し SQLite 3.9.0 以上が必要"
        risk: medium
        verifymethod: test
    }

    designConstraint Python_Compat {
        id: NFR_002
        text: "Python 3.9 から 3.13 で動作する"
        risk: medium
        verifymethod: test
    }

    Full_Text_Search - contains -> FTS5_Match_Query
    Filtered_Search - contains -> Feature_Id_Filter
    Filtered_Search - contains -> Tag_Filter
    Filtered_Search - contains -> Directory_Filter
    Flexible_Output - contains -> Text_Output
    Flexible_Output - contains -> Json_Output
    Clear_Error_Handling - contains -> Index_Existence_Check
    FTS5_Match_Query - derives -> Feature_Id_Filter
    FTS5_Match_Query - derives -> Tag_Filter
    FTS5_Match_Query - derives -> Directory_Filter
    NFR_001 - traces -> FTS5_Match_Query
    NFR_002 - traces -> FTS5_Match_Query
```

## 3.2. 全文検索 詳細図

```mermaid
%%{init: {'theme': 'dark'}}%%
requirementDiagram
    requirement Full_Text_Search {
        id: UR_001
        text: "開発者はインデックス済みドキュメントを全文検索できる"
        risk: high
        verifymethod: test
    }

    functionalRequirement FTS5_Match_Query {
        id: FR_001
        text: "FTS5 MATCH でクエリ文字列にマッチするドキュメントを検索する"
        risk: high
        verifymethod: test
    }

    functionalRequirement Snippet_Generation {
        id: FR_002
        text: "FTS5 snippet() で前後文脈付きマッチ部分を 50 文字で生成する"
        risk: medium
        verifymethod: test
    }

    functionalRequirement Rank_Sort {
        id: FR_003
        text: "クエリ指定時は FTS5 rank によるスコア順でソートする"
        risk: medium
        verifymethod: test
    }

    Full_Text_Search - contains -> FTS5_Match_Query
    Snippet_Generation - derives -> FTS5_Match_Query
    Rank_Sort - derives -> FTS5_Match_Query
```

## 3.3. フィルタ検索 詳細図

```mermaid
%%{init: {'theme': 'dark'}}%%
requirementDiagram
    requirement Filtered_Search {
        id: UR_002
        text: "開発者は feature_id/tag/directory で検索結果を絞り込める"
        risk: medium
        verifymethod: test
    }

    functionalRequirement Feature_Id_Filter {
        id: FR_004
        text: "--feature-id で feature_id 完全一致フィルタを適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Tag_Filter {
        id: FR_005
        text: "--tag でタグ部分一致フィルタ（LIKE）を適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Directory_Filter {
        id: FR_006
        text: "--dir でディレクトリタイプフィルタを適用する"
        risk: low
        verifymethod: test
    }

    functionalRequirement No_Query_Full_Scan {
        id: FR_007
        text: "クエリなし時は FTS5 MATCH を使わず全件取得しフィルタのみ適用する"
        risk: medium
        verifymethod: test
    }

    Filtered_Search - contains -> Feature_Id_Filter
    Filtered_Search - contains -> Tag_Filter
    Filtered_Search - contains -> Directory_Filter
    No_Query_Full_Scan - derives -> Filtered_Search
```

## 3.4. 結果出力 詳細図

```mermaid
%%{init: {'theme': 'dark'}}%%
requirementDiagram
    requirement Flexible_Output {
        id: UR_003
        text: "検索結果を text/json 形式で取得しファイルにも出力できる"
        risk: low
        verifymethod: test
    }

    functionalRequirement Text_Output {
        id: FR_008
        text: "text 形式で件数・タイトル・パス・feature_id・タグ・スニペットを出力する"
        risk: low
        verifymethod: test
    }

    functionalRequirement Json_Output {
        id: FR_009
        text: "--format json で JSON 形式の検索結果を出力する"
        risk: low
        verifymethod: test
    }

    functionalRequirement File_Output {
        id: FR_010
        text: "--output でファイルに結果を書き出す"
        risk: low
        verifymethod: test
    }

    functionalRequirement Result_Limit {
        id: FR_011
        text: "--limit で結果件数の上限を設定する（デフォルト 10）"
        risk: low
        verifymethod: test
    }

    Flexible_Output - contains -> Text_Output
    Flexible_Output - contains -> Json_Output
    File_Output - derives -> Text_Output
    File_Output - derives -> Json_Output
    Result_Limit - derives -> Flexible_Output
```

---

# 4. 要求の詳細説明

## 4.1. ユーザー要求

### UR-001: 全文検索

開発者は `sdd-cli search "クエリ"` コマンドを実行することで、インデックス済みの `.sdd/` 配下ドキュメントに対して FTS5
全文検索を行い、関連するドキュメントをスコア順に取得できる。検索結果にはマッチ箇所のスニペットが付与される。

**検証方法:** テストによる検証

### UR-002: フィルタ検索

開発者は `--feature-id`、`--tag`、`--dir` オプションを組み合わせて検索結果を絞り込める。クエリ文字列なしでフィルタのみの検索も可能。複数のフィルタは
AND 条件で結合される。

**検証方法:** テストによる検証

### UR-003: 柔軟な出力形式

検索結果を text（人間可読）または json（プログラム連携用）形式で取得できる。`--output` オプションでファイルへの書き出しにも対応し、他ツールとの連携が容易。

**検証方法:** テストによる検証

### UR-004: 明確なエラーハンドリング

インデックスが未構築の場合は `sdd-cli index` の実行を促すエラーメッセージを返す。検索結果がゼロ件の場合は "No results
found." メッセージを返す。

**検証方法:** テストによる検証

## 4.2. 機能要求

### FR-001: FTS5 MATCH クエリ検索

クエリ文字列が指定された場合、`documents_fts MATCH ?` で FTS5 全文検索を実行する。trigram tokenizer
により日本語を含む任意の文字列でマッチングが可能。

**検証方法:** テストによる検証

### FR-002: スニペット生成

FTS5 の `snippet(documents_fts, 7, '...', '...', '', 50)` 関数を使用し、マッチしたコンテンツ列（content、インデックス
7）から前後に `...` を付与した 50 文字のスニペットを生成する。クエリなし時は `substr(content, 1, 150)` で先頭 150 文字を切り出す。

**検証方法:** テストによる検証

### FR-003: スコア順ソート

クエリ指定時は FTS5 の `rank` 値（スコア）で昇順ソートし、関連度の高い結果を上位に表示する。クエリなし時は `file_path`
のアルファベット順でソートする。

**検証方法:** テストによる検証

### FR-004: feature_id 完全一致フィルタ

`--feature-id` オプションで `fts.feature_id = ?` による完全一致フィルタを適用する。特定機能に関連するドキュメントのみを抽出できる。

**検証方法:** テストによる検証

### FR-005: タグ部分一致フィルタ

`--tag` オプションで `fts.tags LIKE ?` による部分一致フィルタを適用する。タグはスペース区切りの文字列として FTS5
テーブルに格納されており、指定タグを含むドキュメントを抽出する。

**検証方法:** テストによる検証

### FR-006: ディレクトリタイプフィルタ

`--dir` オプションで `fts.directory = ?` によるフィルタを適用する。選択肢は `requirement`、`specification`、`task` の 3
種類（Click の `Choice` で制約）。

**検証方法:** テストによる検証

### FR-007: クエリなし全件取得

クエリ文字列が未指定の場合、FTS5 MATCH を使用せず `WHERE 1=1` で全件取得し、フィルタ条件のみを適用する。フィルタも未指定の場合はインデックス内の全ドキュメントを返す。

**検証方法:** テストによる検証

### FR-008: text 形式出力

デフォルトの出力形式。以下の情報を整形して表示する:

- 結果件数（`Found N result(s)`）
- クエリ文字列（指定時のみ）
- 各結果: 番号付きタイトル、パス、feature_id、タグ（存在時）、スニペット（存在時）

スニペット内の改行はスペースに置換して 1 行表示する。

**検証方法:** テストによる検証

### FR-009: json 形式出力

`--format json` オプションで `json.dumps(results, indent=2, ensure_ascii=False)` による JSON 形式の出力を返す。SearchResult
型の辞書リストをそのままシリアライズする。

**含まれる機能:**

- tags フィールドは JSON 文字列からパースされた Python リストとして出力される

**検証方法:** テストによる検証

### FR-010: ファイル出力

`--output` オプションで指定されたファイルパスに検索結果を書き出す。text 形式の場合は書き出し完了メッセージを stdout
に表示する。

**検証方法:** テストによる検証

### FR-011: 結果件数上限

`--limit` オプション（デフォルト 10）で SQL クエリの `LIMIT ?` 句を制御し、返却される結果件数の上限を設定する。

**検証方法:** テストによる検証

### FR-012: インデックス存在確認

検索実行前に XDG キャッシュディレクトリ内の `index.db` の存在を確認する。存在しない場合は `ValueError` を発生させ、
`"Index not found at {db_path}. Please run 'sdd-cli index' first."` というメッセージを返す。

**検証方法:** テストによる検証

### FR-013: タグの JSON パース

`documents_meta` テーブルに JSON 文字列として格納されたタグを `json.loads()` でパースし、Python リストとして返却する。パース失敗時は空リスト
`[]` にフォールバックする。

**検証方法:** テストによる検証

## 4.3. 設計制約（非機能要求）

### NFR-001: FTS5 trigram tokenizer 依存

検索機能は SQLite FTS5 の trigram tokenizer に依存する。これにより日本語を含む多言語対応の部分文字列検索が可能だが、SQLite
3.9.0 以上が必須となる。

**検証方法:** テストによる検証（CI マトリックスで複数バージョンテスト）

### NFR-002: Python バージョン互換性

Python 3.9〜3.13 のすべてのバージョンで動作する。型ヒントや標準ライブラリの API 差異に対応が必要。

**検証方法:** テストによる検証（CI マトリックスで複数バージョンテスト）

### NFR-003: XDG キャッシュディレクトリ準拠

インデックス DB のパスは XDG Base Directory 仕様に準拠した `~/.cache/sdd-cli/{project}.{hash}/index.db`
を使用する。document-indexing 機能で生成されたキャッシュを参照する。

**検証方法:** テストによる検証

### NFR-004: SDDGroup 統一エラーハンドリング

`SDDGroup` カスタムクラスにより、検索中の例外は `Error: {message}` 形式で stderr に出力され、終了コード 1 で終了する。

**検証方法:** テストによる検証

### NFR-005: 外部依存の最小化

検索機能のランタイム依存は `click`（CLI フレームワーク）のみ。SQLite は Python 標準ライブラリの `sqlite3`
モジュールを使用し、追加パッケージは不要。

**検証方法:** インスペクションによる検証

---

# 5. 制約事項

## 5.1. 技術的制約

- SQLite FTS5 の trigram tokenizer を使用するため、SQLite 3.9.0 以上が必要
- FTS5 MATCH クエリの構文は SQLite の仕様に依存する（不正な構文はランタイムエラーとなる）
- tags の LIKE フィルタはスペース区切り文字列に対する部分一致のため、短いタグ名で意図しないマッチが発生する可能性がある

## 5.2. ビジネス的制約

- 検索対象は `sdd-cli index` で事前にインデックス構築されたドキュメントに限定される
- document-indexing 機能（`sdd-cli index`）が正常に動作していることが前提

---

# 6. 前提条件

- `sdd-cli index` によりインデックスが事前に構築されていること
- XDG キャッシュディレクトリ（`~/.cache/sdd-cli/{project}.{hash}/index.db`）にアクセス可能であること
- Python 3.9 以上がインストールされていること

---

# 7. スコープ外

以下は本 PRD のスコープ外とします：

- インデックスの構築・更新機能（document-indexing PRD で定義）
- 依存関係の可視化機能（dependency-visualization PRD で定義）
- キャッシュの一覧・削除機能（cache-management PRD で定義）
- FTS5 クエリ構文のバリデーション・サニタイズ
- 検索結果のページネーション
- インクリメンタル検索・リアルタイム検索
- 検索履歴の保存・管理
- 検索結果のハイライト表示（ターミナル色付け）

---

# 8. 用語集

| 用語                 | 定義                                                                                                            |
|--------------------|---------------------------------------------------------------------------------------------------------------|
| SDD                | Specification-Driven Development。仕様駆動開発                                                                       |
| FTS5               | Full-Text Search 5。SQLite の全文検索拡張モジュール                                                                        |
| trigram tokenizer  | 3 文字ずつの部分文字列に分割するトークナイザー。日本語検索に有効                                                                             |
| MATCH              | FTS5 の全文検索演算子。クエリ文字列との一致を判定する                                                                                 |
| snippet            | FTS5 の snippet() 関数が生成する、マッチ箇所の前後文脈付き抜粋テキスト                                                                   |
| rank               | FTS5 が算出する検索結果のスコア値。値が小さいほど関連度が高い                                                                             |
| feature_id         | ドキュメントが属する機能を識別する ID                                                                                          |
| file_type          | ドキュメントの分類（requirement/spec/design/task）                                                                       |
| XDG Base Directory | Linux/macOS のディレクトリ配置標準仕様                                                                                     |
| frontmatter        | Markdown ファイル先頭の `---` で囲まれた YAML メタデータ領域                                                                     |
| SearchResult       | 検索結果の TypedDict 型。file_path/file_name/directory/file_type/title/feature_id/parent_feature_id/tags/snippet を含む |
