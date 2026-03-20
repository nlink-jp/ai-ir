# データフォーマット仕様

## 入力フォーマット：scat/stail JSON エクスポート

[scat](https://github.com/magifd2/scat) および [stail](https://github.com/magifd2/stail)
は、いずれも同一の JSON スキーマでエクスポートを生成します。

### スキーマ

```json
{
  "export_timestamp": "2026-03-19T10:00:00Z",
  "channel_name": "#incident-response",
  "messages": [
    {
      "user_id": "U12345ABC",
      "user_name": "alice",
      "post_type": "user",
      "timestamp": "2026-03-19T09:55:00Z",
      "timestamp_unix": "1742378100.000000",
      "text": "Server at 192.168.1.100 is down.",
      "files": [],
      "thread_timestamp_unix": "",
      "is_reply": false
    }
  ]
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `export_timestamp` | ISO 8601 日時 | エクスポートが生成された日時 |
| `channel_name` | string | Slack チャンネル名（例：`#incident-response`） |
| `messages` | array | メッセージオブジェクトの一覧 |

#### メッセージフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `user_id` | string | Slack ユーザー ID（例：`U12345ABC`） |
| `user_name` | string | 表示名 |
| `post_type` | `"user"` \| `"bot"` | メッセージの発信元種別 |
| `timestamp` | ISO 8601 日時 | メッセージのタイムスタンプ |
| `timestamp_unix` | string | Unix タイムスタンプ（10 進数文字列） |
| `text` | string | メッセージ本文 |
| `files` | array | 添付ファイルオブジェクト（空の場合あり） |
| `thread_timestamp_unix` | string | 親スレッドのタイムスタンプ、またはスレッド外の場合は空文字列 |
| `is_reply` | boolean | スレッド返信かどうか |

## 前処理済みフォーマット

`aiir ingest` の出力。入力フォーマットにセキュリティメタデータを追加した形式です。

```json
{
  "export_timestamp": "2026-03-19T10:00:00Z",
  "channel_name": "#incident-response",
  "messages": [
    {
      "user_id": "U12345ABC",
      "user_name": "alice",
      "post_type": "user",
      "timestamp": "2026-03-19T09:55:00Z",
      "timestamp_unix": "1742378100.000000",
      "text": "<user_message>\nServer at 192[.]168[.]1[.]100 is down.\n</user_message>",
      "files": [],
      "thread_timestamp_unix": "",
      "is_reply": false,
      "iocs": [
        {
          "original": "192.168.1.100",
          "defanged": "192[.]168[.]1[.]100",
          "type": "ip"
        }
      ],
      "has_injection_risk": false,
      "injection_warnings": []
    }
  ],
  "security_warnings": []
}
```

### 追加フィールド

#### トップレベル
| フィールド | 型 | 説明 |
|---|---|---|
| `security_warnings` | string[] | 全メッセージから集約した警告の一覧 |

#### メッセージごと
| フィールド | 型 | 説明 |
|---|---|---|
| `iocs` | IoC[] | 抽出・デファング済みの侵害指標 |
| `has_injection_risk` | boolean | インジェクションパターンが検出されたかどうか |
| `injection_warnings` | string[] | 検出されたインジェクションパターンの説明 |

### IoC オブジェクト

```json
{
  "original": "192.168.1.100",
  "defanged": "192[.]168[.]1[.]100",
  "type": "ip"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `original` | string | 元の IoC の値 |
| `defanged` | string | デファング済みの表現 |
| `type` | string | IoC の種別：`ip`、`url`、`domain`、`email`、`hash` |

## 分析出力フォーマット

### インシデントサマリ（JSON）

```json
{
  "title": "Database cluster outage in production",
  "severity": "critical",
  "affected_systems": ["postgres-prod-01", "api-gateway"],
  "timeline": [
    {
      "timestamp": "2026-03-19T09:55:00Z",
      "actor": "alice",
      "event": "Reported database unreachable"
    }
  ],
  "root_cause": "OOM killer terminated PostgreSQL process",
  "resolution": "Restarted PostgreSQL, increased memory limits",
  "summary": "..."
}
```

### 活動分析（JSON）

```json
{
  "incident_id": "#incident-response",
  "channel": "#incident-response",
  "participants": [
    {
      "user_name": "alice",
      "role_hint": "Database SME",
      "actions": [
        {
          "timestamp": "2026-03-19T09:55:00Z",
          "purpose": "Identify failing component",
          "method": "kubectl get pods -n production",
          "findings": "3 database pods in CrashLoopBackOff"
        }
      ]
    }
  ]
}
```

### ロール分析（JSON）

```json
{
  "incident_id": "#incident-response",
  "channel": "#incident-response",
  "participants": [
    {
      "user_name": "alice",
      "inferred_role": "Lead Responder",
      "confidence": "high",
      "evidence": ["Coordinated investigation", "Assigned tasks to others"]
    }
  ],
  "relationships": [
    {
      "from_user": "bob",
      "to_user": "alice",
      "relationship_type": "reports_to",
      "description": "Bob provided status updates to Alice"
    }
  ]
}
```
