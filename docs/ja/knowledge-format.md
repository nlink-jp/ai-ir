# ナレッジドキュメントフォーマット

戦術ナレッジドキュメントは、インシデントレスポンスの会話から抽出された YAML ファイルです。
各ドキュメントは、将来のインシデントで再利用できる特定の調査手法を記録します。

## ファイル命名規則

```
{id}-{title-slug}.yaml
```

例：`tac-20260319-001-check-pod-logs-for-oom.yaml`

## スキーマ

```yaml
id: "tac-20260319-001"
title: "Check Pod Logs for OOM Events"
purpose: "Identify whether a Kubernetes pod was killed by the OOM killer"
category: "container-analysis"
tools:
  - kubectl
  - grep
procedure: |
  1. List pods in the target namespace to identify crashed pods:
     kubectl get pods -n <namespace>
  2. Describe the crashed pod to check for OOM kill events:
     kubectl describe pod <pod-name> -n <namespace>
  3. Review the pod's previous container logs:
     kubectl logs <pod-name> -n <namespace> --previous
  4. Search for OOM-related messages:
     kubectl logs <pod-name> --previous | grep -i "killed\|oom\|out of memory"
observations: |
  - Exit code 137 in the pod description indicates OOM kill
  - "OOMKilled" in the pod's Last State reason confirms OOM termination
  - Memory usage trends in the logs can indicate a leak or spike
  - Check node-level OOM events with: kubectl describe node <node-name>
tags:
  - kubernetes
  - oom
  - memory
  - container
source:
  channel: "#incident-response"
  participants:
    - alice
    - bob
created_at: "2026-03-19"
```

## フィールドリファレンス

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string | yes | `tac-YYYYMMDD-NNN` 形式の一意な戦術 ID |
| `title` | string | yes | 簡潔で説明的なタイトル（命令形） |
| `purpose` | string | yes | この戦術が対処する問題や疑問 |
| `category` | string | yes | 戦術カテゴリ（下記一覧参照） |
| `tools` | string[] | yes | 使用するコマンド・ツール・スクリプト |
| `procedure` | string | yes | 番号付きのステップバイステップ手順 |
| `observations` | string | yes | 結果の解釈方法と注目すべきパターン |
| `tags` | string[] | yes | 検索・発見用のタグ |
| `source.channel` | string | yes | 元の Slack チャンネル名 |
| `source.participants` | string[] | yes | この戦術に貢献した参加者 |
| `created_at` | string | yes | ISO 日付文字列（YYYY-MM-DD） |

## カテゴリ一覧

### クロスプラットフォーム／汎用

| カテゴリ | 説明 |
|---|---|
| `log-analysis` | ログファイルの検索・フィルタリング・パース |
| `network-analysis` | トラフィックキャプチャ、接続確認、DNS、ファイアウォールルール分析 |
| `process-analysis` | 実行中プロセス、リソース使用量、親子実行ツリー |
| `memory-forensics` | メモリダンプ、ヒープ分析、OOM 調査、volatility |
| `database-analysis` | クエリ分析、ロック確認、スロークエリログ、レプリケーション確認 |
| `container-analysis` | Docker/Kubernetes のポッドおよびコンテナ調査 |
| `cloud-analysis` | クラウドプロバイダーのログ（AWS CloudTrail、GCP Audit、Azure Monitor）、IAM |
| `malware-analysis` | 不審なファイルの分析、ハッシュ確認、サンドボックス実行 |
| `authentication-analysis` | 認証ログ、ログイン失敗、ブルートフォース、クレデンシャル使用状況 |

### Linux 固有

| カテゴリ | 説明 |
|---|---|
| `linux-systemd` | systemd/journald — `journalctl`、ユニットファイル確認、サービスタイマー |
| `linux-auditd` | Linux Audit フレームワーク — `ausearch`、`aureport`、`auditctl`、`/var/log/audit/` |
| `linux-procfs` | `/proc/` ファイルシステム — プロセスメモリマップ、オープンファイル、ネットワーク状態 |
| `linux-ebpf` | eBPF/BCC 動的トレース — `execsnoop`、`opensnoop`、`bpftool`、bcc ツールキット |
| `linux-kernel` | カーネルレベル — `dmesg`、`lsmod`、`modinfo`、OOM killer イベント |

### Windows 固有

| カテゴリ | 説明 |
|---|---|
| `windows-event-log` | Windows イベントログおよび Sysmon — `wevtutil`、`Get-WinEvent`、Sysmon イベント ID |
| `windows-registry` | レジストリフォレンジック — `reg query`、Autoruns、Run/RunOnce キー |
| `windows-powershell` | PowerShell フォレンジック — Script Block Logging、トランスクリプト、PSReadLine 履歴 |
| `windows-active-directory` | AD 調査 — `Get-ADUser`、LDAP、GPO、LAPS、DCSync 検出 |
| `windows-filesystem` | NTFS アーティファクト — ADS、VSS（`vssadmin`）、MFT、プリフェッチ、LNK ファイル |
| `windows-defender` | Windows Defender/EDR — Defender ログ、検疫、除外設定確認 |

### macOS 固有

| カテゴリ | 説明 |
|---|---|
| `macos-unified-logging` | Apple 統合ログシステム — `log show` / `log stream` |
| `macos-launchd` | LaunchAgents/Daemons — `launchctl`、plist 分析 |
| `macos-gatekeeper` | `spctl`、`codesign`、検疫 xattr |
| `macos-endpoint-security` | TCC データベース、SIP 状態、ESF イベント確認 |
| `macos-filesystem` | APFS スナップショット、Time Machine、`xattr`、`fs_usage` |

### その他

| カテゴリ | 説明 |
|---|---|
| `other` | 既存のカテゴリに当てはまらないもの |

## ID の生成規則

ID は `tac-YYYYMMDD-NNN` 形式に従います：
- `YYYYMMDD`：インシデントのエクスポートタイムスタンプの日付
- `NNN`：その日付内のゼロパディングされた連番（001、002、...）

例：`tac-20260319-001`、`tac-20260319-002`、`tac-20260319-003`

## 使用例

### ネットワーク分析カテゴリの戦術をすべて検索

```bash
grep -r "category: network-analysis" knowledge/
```

### kubectl を使う戦術を一覧表示

```bash
grep -rl "kubectl" knowledge/
```

### タグでフィルタリング

```bash
grep -rl "^  - kubernetes" knowledge/
```
