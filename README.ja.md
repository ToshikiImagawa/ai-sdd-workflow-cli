# SDD CLI

[![CI](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.11%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type--check-mypy-blue)](https://mypy-lang.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](https://github.com/ToshikiImagawa/ai-sdd-workflow-cli)

AI-SDD Workflow のドキュメント管理 CLI ツール。

[AI-SDD Workflow プラグイン](https://github.com/ToshikiImagawa/ai-sdd-workflow) と連携して、仕様書の全文検索・依存関係可視化を提供します。

[English README](README.md)

## 機能

- **プロジェクト初期化**: `.sdd-config.json` の生成と SDD 環境変数のエクスポート
- **インデックス構築**: `.sdd/` 配下のドキュメントを SQLite FTS5 でインデックス化
- **全文検索**: キーワード、feature ID、タグによる高速検索
- **依存関係可視化**: ドキュメント間の依存関係をインタラクティブ HTML ビューアで表示
- **キャッシュ管理**: プロジェクト別キャッシュの一覧・削除

## 動作要件

- Python 3.9 以上

## インストール

### pip

```bash
pip install git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git
```

### uv

```bash
uv tool install --from git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git sdd-cli
```

### uvx (インストールなしで実行)

```bash
uvx --from git+https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git sdd-cli --help
```

## 使用方法

### プロジェクト初期化

```bash
# デフォルト設定で .sdd-config.json を生成
sdd-cli init

# プロジェクトルートを指定
sdd-cli init --root /path/to/project

# SDD 環境変数をエクスポート（シェル eval 用）
eval $(sdd-cli init --env)
```

`CLAUDE_ENV_FILE` が設定されている場合、`--env` は stdout ではなくそのファイルに export 文を書き込みます。

### インデックス構築

```bash
sdd-cli index

# 出力を抑制
sdd-cli index --quiet
```

### ドキュメント検索

```bash
# キーワード検索
sdd-cli search "ログイン機能"

# Feature ID で検索
sdd-cli search --feature-id user-login

# タグで検索
sdd-cli search --tag authentication

# ディレクトリで絞り込み
sdd-cli search "認証" --dir specification

# JSON 形式で出力
sdd-cli search "ログイン" --format json --output results.json

# 結果数を制限
sdd-cli search "ログイン" --limit 5
```

### 依存関係可視化

```bash
# 依存関係を HTML ビューアで表示（ブラウザが自動的に開きます）
sdd-cli visualize

# ディレクトリで絞り込み
sdd-cli visualize --filter-dir specification

# 特定機能のみ
sdd-cli visualize --feature-id user-login

# グラフを JSON でエクスポート
sdd-cli visualize --output graph.json
```

### キャッシュ管理

```bash
# キャッシュ一覧表示
sdd-cli cache list

# JSON 形式で表示
sdd-cli cache list --format json

# 特定プロジェクトのキャッシュを削除
sdd-cli cache clean --project slide-presentation-app

# パターンに一致するキャッシュを削除
sdd-cli cache clean --project 'test-*'

# 削除されるものをプレビュー
sdd-cli cache clean --all --dry-run

# すべてのキャッシュを削除
sdd-cli cache clean --all
```

## CLI リファレンス

### `sdd-cli init`

| オプション              | 説明                                 |
|--------------------|------------------------------------|
| `--root DIRECTORY` | プロジェクトルートディレクトリ（デフォルト: カレントディレクトリ） |
| `--env`            | SDD 環境変数の export 文を出力              |

### `sdd-cli index`

| オプション              | 説明                                 |
|--------------------|------------------------------------|
| `--root DIRECTORY` | プロジェクトルートディレクトリ（デフォルト: カレントディレクトリ） |
| `--quiet`          | 出力メッセージを抑制                         |

### `sdd-cli search [QUERY]`

| オプション                                      | 説明                                 |
|--------------------------------------------|------------------------------------|
| `--root DIRECTORY`                         | プロジェクトルートディレクトリ（デフォルト: カレントディレクトリ） |
| `--feature-id TEXT`                        | Feature ID でフィルタ                   |
| `--tag TEXT`                               | タグでフィルタ                            |
| `--dir [requirement\|specification\|task]` | ディレクトリタイプでフィルタ                     |
| `--format [text\|json]`                    | 出力形式（デフォルト: text）                  |
| `--output PATH`                            | 出力ファイルパス（デフォルト: stdout）            |
| `--limit INTEGER`                          | 最大結果数（デフォルト: 10）                   |

### `sdd-cli visualize`

| オプション                                             | 説明                                 |
|---------------------------------------------------|------------------------------------|
| `--root DIRECTORY`                                | プロジェクトルートディレクトリ（デフォルト: カレントディレクトリ） |
| `--output PATH`                                   | グラフを JSON ファイルとしてエクスポート            |
| `--filter-dir [requirement\|specification\|task]` | ディレクトリタイプでフィルタ                     |
| `--feature-id TEXT`                               | Feature ID でフィルタ                   |

### `sdd-cli cache list`

| オプション                   | 説明                |
|-------------------------|-------------------|
| `--format [text\|json]` | 出力形式（デフォルト: text） |

### `sdd-cli cache clean`

| オプション            | 説明                     |
|------------------|------------------------|
| `--project TEXT` | プロジェクト名パターン（ワイルドカード対応） |
| `--all`          | すべてのキャッシュを削除           |
| `--dry-run`      | 実際に削除せず、削除対象を表示        |

## 環境変数

| 変数名                     | 説明                    | デフォルト           |
|-------------------------|-----------------------|-----------------|
| `SDD_ROOT`              | SDD ルートディレクトリ名        | `.sdd`          |
| `SDD_REQUIREMENT_DIR`   | requirement ディレクトリ名   | `requirement`   |
| `SDD_SPECIFICATION_DIR` | specification ディレクトリ名 | `specification` |
| `SDD_TASK_DIR`          | task ディレクトリ名          | `task`          |

環境変数は `.sdd-config.json` の設定よりも優先されます。

## キャッシュディレクトリ

インデックスと可視化結果は **XDG Base Directory** 仕様に従い、以下のディレクトリに保存されます：

```
~/.cache/sdd-cli/
├── my-project.a1b2c3d4/          # プロジェクト別キャッシュ
│   ├── index.db                  # SQLite FTS5 インデックス
│   ├── metadata.json             # インデックスメタデータ
│   ├── dependency-graph.json     # 依存関係グラフデータ
│   └── search-results.json      # 検索結果（スキル実行時）
└── another-project.e5f6g7h8/
    └── ...
```

## AI-SDD プラグインとの連携

このツールは [AI-SDD Workflow プラグイン](https://github.com/ToshikiImagawa/ai-sdd-workflow) のスキル（`/sdd-index`,
`/sdd-search`, `/sdd-visualize`）から自動的に呼び出されます。

プラグインをインストールしている場合、セッション開始時に `sdd-cli` が自動インストールされ、インデックスの初期構築も自動的に行われます。

## 開発

### セットアップ

```bash
git clone https://github.com/ToshikiImagawa/ai-sdd-workflow-cli.git
cd ai-sdd-workflow-cli
uv sync --dev
```

### テスト実行

```bash
uv run pytest
```

### Lint & フォーマット

```bash
uv run ruff check .
uv run ruff format --check .
```

### 型チェック

```bash
uv run mypy src/sdd_cli/
```

### パッケージビルド

```bash
uv build
```

## ライセンス

MIT License - [LICENSE](LICENSE) を参照してください。
