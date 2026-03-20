# ai-ir: AI-powered Incident Response Analysis Toolset

`ai-ir` analyzes incident response Slack conversation history exported via
[scat](https://github.com/magifd2/scat) or [stail](https://github.com/magifd2/stail)
to generate actionable reports and reusable knowledge.

## Features

- **Incident Summary** — AI-generated timeline, root cause, and executive summary
- **Activity Analysis** — Per-participant breakdown of methods, tools, and findings
- **Role Inference** — Infer IR roles (Incident Commander, SME, etc.) and relationships
- **Knowledge Extraction** — Extract reusable investigation tactics as YAML documents
- **Security-first** — IoC defanging and prompt injection defense built-in

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/magifd2/ai-ir
cd ai-ir
uv sync
```

## Configuration

Copy `.env.example` to `.env` and configure your LLM endpoint:

```bash
cp .env.example .env
# Edit .env with your settings
```

```bash
AIIR_LLM_BASE_URL=https://api.openai.com/v1
AIIR_LLM_API_KEY=sk-...
AIIR_LLM_MODEL=gpt-4o
```

Environment variables can also be set directly without a `.env` file.

## Usage

### Export Slack channel history

```bash
# Using stail
stail export -c "#incident-response" --output incident.json

# Using scat
scat export log --channel "#incident-response" --output incident.json
```

### Step 1: Ingest and preprocess

Parse the export, defang IoCs, and detect prompt injection risks:

```bash
uv run aiir ingest incident.json -o incident.preprocessed.json
```

Output goes to stdout by default (pipe-friendly):

```bash
uv run aiir ingest incident.json | uv run aiir summarize -
```

### Step 2: Generate analysis

Each analysis command accepts either raw export files or preprocessed files:

```bash
# Generate incident summary (Markdown)
uv run aiir summarize incident.json

# Generate incident summary (JSON)
uv run aiir summarize incident.json --format json -o summary.json

# Analyze per-participant activities
uv run aiir activity incident.json -o activity.md

# Infer participant roles and relationships
uv run aiir roles incident.json -o roles.md

# Extract reusable tactics as YAML knowledge documents
uv run aiir knowledge incident.json --output-dir ./knowledge/

# Generate full report
uv run aiir report incident.json -o report.md
uv run aiir report incident.json --format json -o report.json
```

### Full pipeline example

```bash
# Preprocess once, then run multiple analyses
uv run aiir ingest incident.json -o preprocessed.json

uv run aiir summarize preprocessed.json -o summary.md
uv run aiir activity preprocessed.json -o activity.md
uv run aiir roles preprocessed.json -o roles.md
uv run aiir knowledge preprocessed.json -d ./knowledge/
uv run aiir report preprocessed.json -o full-report.md
```

## Security

- **No external transmission**: Only the configured LLM endpoint receives data
- **IoC defanging**: IPv4 addresses, URLs, domains, emails, and hashes are defanged before LLM transmission
- **Prompt injection defense**: All Slack message text is wrapped in XML tags and scanned for injection patterns
- **Local processing**: All parsing and preprocessing runs locally

See [docs/en/security.md](docs/en/security.md) for detailed security considerations.

## Documentation

- [Architecture](docs/en/architecture.md) / [アーキテクチャ](docs/ja/architecture.md)
- [Data Format](docs/en/data-format.md) / [データフォーマット](docs/ja/data-format.md)
- [Knowledge Format](docs/en/knowledge-format.md) / [ナレッジフォーマット](docs/ja/knowledge-format.md)
- [Security](docs/en/security.md) / [セキュリティ](docs/ja/security.md)
- [Maintenance](docs/en/maintenance.md) / [メンテナンス](docs/ja/maintenance.md)

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=aiir --cov-report=term-missing
```

## License

MIT License
