# ai-ir システムアーキテクチャ

## 概要

`ai-ir` は、インシデントレスポンス用 Slack 会話履歴を AI で解析するコマンドラインツールセットです。
scat/stail によるエクスポートを処理し、セキュリティ前処理を施した上で、
OpenAI 互換の LLM API を使って構造化された分析結果を生成します。

## コンポーネント図

```
入力（scat/stail JSON エクスポート）
         │
         ▼
┌─────────────────────┐
│   aiir ingest       │  ← parser/loader.py
│                     │    parser/defang.py
│  - 読み込み・検証   │    parser/sanitizer.py
│  - IoC デファング   │
│  - インジェクション │
│    検出             │
└─────────┬───────────┘
          │ ProcessedExport（JSON）
          ▼
┌─────────────────────────────────────────────────────┐
│                    LLM クライアント                  │
│                  llm/client.py                      │
│                                                     │
│  OpenAI 互換 API（エンドポイント設定可）             │
└─────────────────────────────────────────────────────┘
          │
          ├──────────────────────────────────────────┐
          ▼                                          ▼
┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐
│ analyze/         │  │ analyze/     │  │ analyze/           │
│ summarizer.py    │  │ activity.py  │  │ roles.py           │
│                  │  │              │  │                    │
│ IncidentSummary  │  │ ActivityAna- │  │ RoleAnalysis       │
└──────────────────┘  │ lysis        │  └────────────────────┘
                      └──────────────┘
          │
          ▼
┌──────────────────┐
│ knowledge/       │
│ extractor.py     │  → list[Tactic]
│ formatter.py     │  → YAML ファイル
└──────────────────┘
          │
          ▼
┌──────────────────┐
│ report/          │
│ generator.py     │  → Markdown / JSON レポート
└──────────────────┘
```

## モジュール責務

### `aiir.config`
`pydantic-settings` を使って環境変数から設定を読み込みます。
`python-dotenv` を通じて `.env` ファイルにも対応しています。
LLM 関連の設定はすべて `AIIR_LLM_` プレフィックスを使用します。

### `aiir.models`
すべての Pydantic データモデルを定義します：
- **入力モデル**: `SlackMessage`、`SlackExport`
- **前処理済みモデル**: `IoC`、`ProcessedMessage`、`ProcessedExport`
- **分析モデル**: `IncidentSummary`、`ActivityAnalysis`、`RoleAnalysis`
- **ナレッジモデル**: `Tactic`、`TacticSource`

### `aiir.parser`
3 段階のパイプライン：
1. **loader**: JSON を `SlackExport` スキーマに対してデシリアライズ・検証
2. **defang**: IoC（IP アドレス、URL、ハッシュ、メールアドレス）を抽出してデファング
3. **sanitizer**: プロンプトインジェクションパターンを検出し、安全タグでテキストをラップ

### `aiir.llm`
OpenAI Python SDK の薄いラッパーです。以下をサポートします：
- 通常のチャット補完（`complete`）
- JSON モード補完（`complete_json`）
- OpenAI 互換エンドポイントへの接続（`base_url` 設定可能）

### `aiir.analyze`
3 つのアナライザー。それぞれ専用のシステムプロンプトと構造化された JSON 出力を持ちます：
- **summarizer**: タイムライン、深刻度、根本原因、解決策
- **activity**: ユーザーごとのアクション（目的・手法・調査結果）
- **roles**: 信頼度と根拠付きの IR ロール推定

### `aiir.knowledge`
- **extractor**: 再利用可能な調査戦術を LLM に抽出させる
- **formatter**: 戦術を生成 ID 付きの YAML にシリアライズする

### `aiir.report`
すべての分析結果を集約して、統合された Markdown または JSON レポートを生成します。

### `aiir.cli`
Click ベースの CLI で 6 つのサブコマンドを提供します。各分析コマンドは、
入力がローエクスポートか前処理済みファイルかを自動検出し（`security_warnings`
フィールドの有無で判定）、必要に応じてインジェスト処理を実行します。

## データフロー

```
生 JSON → SlackExport → ProcessedExport → LLM API → 分析モデル → レポート/YAML
```

## セキュリティアーキテクチャ

ユーザー由来のデータはすべて、LLM に渡される前に 2 段階のセキュリティパイプラインを通ります：

1. **デファング**（`parser/defang.py`）: IoC をデファング済みの表現に置換することで、
   悪意のある URL や IP アドレスが誤って有効化されないようにします。
2. **サニタイズ**（`parser/sanitizer.py`）: テキストを 14 種類以上のプロンプトインジェクション
   パターンに対してスキャンし、`<user_message>` XML タグでラップして、その内容がデータであり
   命令ではないことを LLM に伝えます。

LLM クライアントはネットワークリクエストを行う唯一のコンポーネントであり、
通信先は設定されたエンドポイントのみです。
