# ai-ir System Architecture

## Overview

`ai-ir` is a command-line toolset for AI-powered analysis of incident response Slack
conversation histories. It processes exports from scat/stail, applies security
preprocessing, and uses an OpenAI-compatible LLM API to generate structured analysis.

## Component Diagram

```
Input (scat/stail JSON export)
         │
         ▼
┌─────────────────────┐
│   aiir ingest       │  ← parser/loader.py
│                     │    parser/defang.py
│  - Load & validate  │    parser/sanitizer.py
│  - Defang IoCs      │
│  - Detect injection │
└─────────┬───────────┘
          │ ProcessedExport (JSON)
          ▼
┌─────────────────────────────────────────────────────┐
│                    LLM Client                       │
│                  llm/client.py                      │
│                                                     │
│  OpenAI-compatible API (configurable endpoint)      │
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
│ formatter.py     │  → YAML files
└──────────────────┘
          │
          ▼
┌──────────────────┐
│ report/          │
│ generator.py     │  → Markdown / JSON report
└──────────────────┘
```

## Module Responsibilities

### `aiir.config`
Loads configuration from environment variables using `pydantic-settings`.
Supports `.env` files via `python-dotenv`. All LLM settings use the `AIIR_LLM_` prefix.

### `aiir.models`
Defines all Pydantic data models:
- **Input models**: `SlackMessage`, `SlackExport`
- **Preprocessed models**: `IoC`, `ProcessedMessage`, `ProcessedExport`
- **Analysis models**: `IncidentSummary`, `ActivityAnalysis`, `RoleAnalysis`
- **Knowledge models**: `Tactic`, `TacticSource`

### `aiir.parser`
Three-stage pipeline:
1. **loader**: Deserialize and validate JSON against `SlackExport` schema
2. **defang**: Extract and defang IoCs (IPs, URLs, hashes, emails)
3. **sanitizer**: Detect prompt injection patterns, wrap text in safety tags

### `aiir.llm`
Thin wrapper around the OpenAI Python SDK. Supports:
- Standard chat completion (`complete`)
- JSON-mode completion (`complete_json`)
- Configurable base URL for any OpenAI-compatible endpoint

### `aiir.analyze`
Three analyzers, each with a focused system prompt and structured JSON output:
- **summarizer**: Timeline, severity, root cause, resolution
- **activity**: Per-user actions with purpose, method, findings
- **roles**: Inferred IR roles with confidence levels and evidence

### `aiir.knowledge`
- **extractor**: Prompts LLM to identify reusable investigation tactics
- **formatter**: Serializes tactics to YAML with generated IDs

### `aiir.report`
Aggregates all analysis results into cohesive Markdown or JSON reports.

### `aiir.cli`
Click-based CLI with six subcommands. Each analysis command auto-detects whether
the input is a raw export or preprocessed file (by checking for the `security_warnings`
field) and runs ingestion if needed.

## Data Flow

```
Raw JSON → SlackExport → ProcessedExport → LLM API → Analysis Models → Reports/YAML
```

## Security Architecture

All user-sourced data passes through a two-stage security pipeline before reaching
the LLM:

1. **Defanging** (in `parser/defang.py`): IoCs are replaced with defanged variants
   so malicious URLs and IPs cannot be accidentally activated.
2. **Sanitization** (in `parser/sanitizer.py`): Text is scanned for 14+ prompt
   injection patterns and wrapped in `<user_message>` XML tags to signal to the LLM
   that the content is data, not instructions.

The LLM client is the only component that makes network requests, and only to the
configured endpoint.
