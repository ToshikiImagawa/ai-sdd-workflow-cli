# SDD CLI

AI-SDD Workflow のドキュメント管理 CLI ツール。

[AI-SDD Workflow プラグイン](https://github.com/ToshikiImagawa/ai-sdd-workflow) と連携して、仕様書の全文検索・依存関係可視化を提供します。

## 機能

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

### インデックス構築

```bash
sdd-cli index --root .sdd
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
```

### 依存関係可視化

```bash
# 依存関係をHTMLビューアで表示（ブラウザが自動的に開きます）
sdd-cli visualize

# 特定ディレクトリのみ
sdd-cli visualize --filter-dir specification

# 特定機能のみ
sdd-cli visualize --feature-id user-login
```

### キャッシュ管理

```bash
# キャッシュ一覧表示
sdd-cli cache list

# JSON形式で表示
sdd-cli cache list --format json

# 特定プロジェクトのキャッシュを削除
sdd-cli cache clean --project slide-presentation-app

# すべてのキャッシュを削除
sdd-cli cache clean --all
```

## キャッシュディレクトリ

インデックスと可視化結果は **XDG Base Directory** 仕様に従い、以下のディレクトリに保存されます：

```
~/.cache/sdd-cli/
├── my-project.a1b2c3d4/          # プロジェクト別キャッシュ
│   ├── index.db                  # SQLite FTS5 インデックス
│   ├── metadata.json             # インデックスメタデータ
│   ├── dependency-graph.json      # 依存関係グラフデータ
│   └── search-results.json       # 検索結果（スキル実行時）
└── another-project.e5f6g7h8/
    └── ...
```

## AI-SDD プラグインとの連携

このツールは [AI-SDD Workflow プラグイン](https://github.com/ToshikiImagawa/ai-sdd-workflow) のスキル（`/sdd-index`, `/sdd-search`, `/sdd-visualize`）から自動的に呼び出されます。

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

### Lint

```bash
uv run ruff check .
```

### パッケージビルド

```bash
uv build
```

## ライセンス

MIT License - [LICENSE](LICENSE) を参照してください。
