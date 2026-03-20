# Knowledge Document Format

Tactic knowledge documents are YAML files extracted from incident response conversations.
Each document captures a specific investigation method that can be reused in future incidents.

## File Naming

```
{id}-{title-slug}.yaml
```

Example: `tac-20260319-001-check-pod-logs-for-oom.yaml`

## Schema

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
confidence: confirmed
evidence: "Alice shared kubectl output showing OOMKilled status in the channel"
source:
  channel: "#incident-response"
  participants:
    - alice
    - bob
created_at: "2026-03-19"
```

## Field Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique tactic ID in format `tac-YYYYMMDD-NNN` |
| `title` | string | yes | Concise, descriptive title (imperative form) |
| `purpose` | string | yes | The question or problem this tactic addresses |
| `category` | string | yes | Tactic category (see list below) |
| `tools` | string[] | yes | Commands, tools, or scripts used |
| `procedure` | string | yes | Step-by-step numbered instructions |
| `observations` | string | yes | How to interpret results and what patterns indicate |
| `tags` | string[] | yes | Searchable tags for discovery |
| `confidence` | `"confirmed"` \| `"inferred"` \| `"suggested"` | yes | Evidence confidence level (see below) |
| `evidence` | string | yes | One-sentence rationale for the confidence classification |
| `source.channel` | string | yes | Originating Slack channel |
| `source.participants` | string[] | yes | Participants who contributed this tactic |
| `created_at` | string | yes | ISO date string (YYYY-MM-DD) |

### Confidence Levels

| Value | Meaning |
|---|---|
| `confirmed` | Command output or explicit result was shared in the Slack channel |
| `inferred` | Participant mentioned running or checking something but no output was shared |
| `suggested` | Proposed as a recommendation; no indication it was actually executed |

When using tactics from the knowledge base, treat `confirmed` tactics as verified procedures and `inferred`/`suggested` tactics as candidates that warrant validation before adoption.

## Categories

### Cross-platform / General

| Category | Description |
|---|---|
| `log-analysis` | Searching, filtering, and parsing log files |
| `network-analysis` | Traffic capture, connection inspection, DNS, firewall rule analysis |
| `process-analysis` | Running processes, resource usage, parent-child execution trees |
| `memory-forensics` | Memory dumps, heap analysis, OOM investigation, volatility |
| `database-analysis` | Query analysis, lock inspection, slow query logs, replication checks |
| `container-analysis` | Docker/Kubernetes pod and container investigation |
| `cloud-analysis` | Cloud provider logs (AWS CloudTrail, GCP Audit, Azure Monitor), IAM |
| `malware-analysis` | Suspicious file analysis, hash checking, sandbox detonation |
| `authentication-analysis` | Auth logs, failed logins, brute force, credential usage |

### Linux-specific

| Category | Description |
|---|---|
| `linux-systemd` | systemd/journald — `journalctl`, unit file inspection, service timers |
| `linux-auditd` | Linux Audit framework — `ausearch`, `aureport`, `auditctl`, `/var/log/audit/` |
| `linux-procfs` | `/proc/` filesystem — process memory maps, open files, network state |
| `linux-ebpf` | eBPF/BCC dynamic tracing — `execsnoop`, `opensnoop`, `bpftool`, bcc toolkit |
| `linux-kernel` | Kernel-level — `dmesg`, `lsmod`, `modinfo`, OOM killer events |

### Windows-specific

| Category | Description |
|---|---|
| `windows-event-log` | Windows Event Log and Sysmon — `wevtutil`, `Get-WinEvent`, Sysmon event IDs |
| `windows-registry` | Registry forensics — `reg query`, Autoruns, Run/RunOnce keys |
| `windows-powershell` | PowerShell forensics — Script Block Logging, transcripts, PSReadLine history |
| `windows-active-directory` | AD investigation — `Get-ADUser`, LDAP, GPO, LAPS, DCSync detection |
| `windows-filesystem` | NTFS artifacts — ADS, VSS (`vssadmin`), MFT, prefetch, LNK files |
| `windows-defender` | Windows Defender/EDR — Defender logs, quarantine, exclusion inspection |

### macOS-specific

| Category | Description |
|---|---|
| `macos-unified-logging` | Apple Unified Logging System — `log show` / `log stream` |
| `macos-launchd` | LaunchAgents/Daemons — `launchctl`, plist analysis |
| `macos-gatekeeper` | `spctl`, `codesign`, quarantine xattrs |
| `macos-endpoint-security` | TCC database, SIP status, ESF event inspection |
| `macos-filesystem` | APFS snapshots, Time Machine, `xattr`, `fs_usage` |

### Other

| Category | Description |
|---|---|
| `other` | Does not fit any existing category |

## ID Generation

IDs follow the format `tac-YYYYMMDD-NNN`:
- `YYYYMMDD`: Date from the incident's export timestamp
- `NNN`: Zero-padded sequential number within that date (001, 002, ...)

Example sequence: `tac-20260319-001`, `tac-20260319-002`, `tac-20260319-003`

## Usage Examples

### Find all network analysis tactics

```bash
grep -r "category: network-analysis" knowledge/
```

### List tactics using kubectl

```bash
grep -rl "kubectl" knowledge/
```

### Filter by tag

```bash
grep -rl "^  - kubernetes" knowledge/
```
