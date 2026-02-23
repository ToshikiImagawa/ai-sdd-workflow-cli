---
name: prepare-release
description: "Prepare a release by updating CHANGELOG and version manifests. Analyzes git history, supplements existing [Unreleased] entries, and generates release notes."
version: 1.0.0
license: MIT
user-invocable: true
argument-hint: "<version>"
allowed-tools: Read, Edit, Glob, Grep, Bash
---

# Prepare Release - リリース準備スキル

CHANGELOG を更新し、バージョンマニフェストファイル（pyproject.toml, __init__.py）を一括更新するリリース準備スキル。

**ハイブリッド方式**: `[Unreleased]` セクションに既存内容があればそれを活用し、git 変更履歴から不足分を補完する。

## Input

$ARGUMENTS

バージョン番号を引数として受け取る（`v` プレフィックスなし）。

### Input Examples

```
/prepare-release 0.2.0
/prepare-release 1.0.0-alpha
```

### Validation

- 引数が空の場合はエラー終了し、使用例を表示する
- セマンティックバージョニング形式（`X.Y.Z` または `X.Y.Z-prerelease`）であることを確認する

## Target Files

### CHANGELOG File

| ファイル | 言語 |
|:---|:---|
| `CHANGELOG.md` | English |

### Version Manifest Files

| ファイル | フィールド |
|:---|:---|
| `pyproject.toml` | `version` |
| `src/sdd_cli/__init__.py` | `__version__` |

## Processing Flow

### Step 1: Validate Version Argument

1. `$ARGUMENTS` からバージョン番号をパースする
2. セマンティックバージョニング形式を検証する
3. 不正な場合はエラーメッセージと使用例を表示して終了する

### Step 2: Detect Previous Release

1. `git tag --list 'v*' --sort=-version:refname` で最新のリリースタグを取得する
2. タグが存在しない場合は初回リリースとして扱う
3. 比較基点を記録する（例: `v0.1.0`）

### Step 3: Read Current [Unreleased] Content

CHANGELOG ファイルを Read で読み込み、`## [Unreleased]` セクションの内容を抽出する。

- **内容あり**: 既存エントリをベースとして保持する
- **内容なし**: Step 4 で全エントリを生成する

### Step 4: Analyze Git Changes

前回タグから HEAD までの変更を分析する。

```bash
# コミット一覧
git log <previous-tag>..HEAD --oneline --no-merges

# 変更ファイル統計
git diff <previous-tag>..HEAD --stat
```

変更内容を以下のカテゴリに分類する:

| Category | 判定基準 |
|:---|:---|
| Breaking Changes | 互換性を破る変更、CLI API 変更 |
| Added | 新機能、新コマンド、新オプション |
| Changed | 既存機能の変更、リファクタリング |
| Fixed | バグ修正、不具合対応 |
| Removed | 機能やオプションの削除 |

### Step 5: Generate / Supplement CHANGELOG Entries

**重要: CHANGELOG はパッケージ利用者向けである。**

以下の変更は CHANGELOG に**含めない**:

- CI/CD ワークフロー（`.github/workflows/`）の追加・変更
- 開発者向けスクリプト（`scripts/`）の追加・変更
- テストコード・テストフィクスチャ（`tests/`）の追加・変更
- `.claude/skills/` 配下の開発者向けスキル
- `.gitignore`、PR テンプレート等のリポジトリ管理ファイル
- その他、パッケージをインストールしたユーザーに影響しない変更

以下の変更は CHANGELOG に**含める**:

- `src/sdd_cli/` 配下のコード変更（コマンド、機能、バグ修正）
- `pyproject.toml` の依存関係や設定変更（ユーザーに影響する場合）
- パッケージ利用者に影響するバグ修正・機能追加・破壊的変更

**ハイブリッドロジック:**

1. `[Unreleased]` に既存内容がある場合:
   - 既存エントリをベースとする
   - git 変更履歴と照合し、カバーされていない**利用者向け変更**を特定する
   - 不足分のエントリのみ追加生成する
2. `[Unreleased]` が空の場合:
   - git 変更履歴から**利用者向け変更**のエントリを生成する
3. 利用者向け変更が存在しない場合:
   - ユーザーに「パッケージ利用者向けの変更がありません」と報告し、CHANGELOG 更新をスキップするか確認する

**記述スタイル（既存 CHANGELOG に準拠）:**

- 各エントリは `- **対象名** - 変更内容の要約` 形式または `- 変更内容の要約` 形式
- サブ項目はインデント2スペースで `- 詳細内容`
- カテゴリは `###` ヘッダーで分類（Added, Changed, Fixed, Removed, Breaking Changes）

### Step 6: Update CHANGELOG File

CHANGELOG ファイルに対して以下を実行する:

1. `## [Unreleased]` セクションの既存内容をクリアする
2. `## [Unreleased]` の直後に空行を挟んで新バージョンセクションを挿入する:
   ```
   ## [VERSION] - YYYY-MM-DD
   ```
3. 日付は実行日（`date +%Y-%m-%d` で取得）を使用する
4. Step 5 で生成/統合したエントリを配置する

### Step 7: Update Version Manifests

2箇所のバージョンフィールドをすべて新バージョンに更新する:

1. `pyproject.toml` → `version = "NEW_VERSION"`
2. `src/sdd_cli/__init__.py` → `__version__ = "NEW_VERSION"`

**更新方法:**

- `pyproject.toml`: Edit tool で `version = "OLD_VERSION"` → `version = "NEW_VERSION"` に置換
- `__init__.py`: Edit tool で `__version__ = "OLD_VERSION"` → `__version__ = "NEW_VERSION"` に置換

### Step 8: Summary

更新結果のサマリーを表示する:

- 更新されたバージョン: `OLD_VERSION` → `NEW_VERSION`
- CHANGELOG エントリ数（カテゴリ別）
- 更新されたファイル一覧
- 次のステップ（レビュー → コミット → タグ → プッシュ）

## Output Format

```
## Release Preparation Complete

**Version**: OLD_VERSION → NEW_VERSION
**Date**: YYYY-MM-DD

### CHANGELOG Updates

| Category | Entries | Source |
|:---|:---|:---|
| Added | N | existing / generated / mixed |
| Changed | N | ... |
| Fixed | N | ... |

### Updated Files

- [ ] `CHANGELOG.md`
- [ ] `pyproject.toml`
- [ ] `src/sdd_cli/__init__.py`

### Next Steps

1. 変更内容をレビューする
2. コミットする: `git add -A && git commit -m "[add] v{VERSION} リリース準備"`
3. タグを作成する: `git tag v{VERSION}`
4. プッシュする: `git push origin main --tags`
5. GitHub Actions の Release ワークフローが自動実行される
```

## Notes

- このスキルは CHANGELOG の **生成・編集** と **バージョン更新** を行う。コミットやタグ作成は行わない
- 生成されたエントリは必ずユーザーにレビューを促す
- プレリリースバージョン（`-alpha`, `-rc.1` 等）もサポートする
- pyproject.toml と src/sdd_cli/__init__.py のバージョンは必ず一致させる
