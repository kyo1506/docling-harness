# docling-harness

CLI tool that extracts, classifies, and consolidates documentation into structured, agent-ready context — optimized for Spec-Driven Development, Loop Engineering, and Harness Engineering workflows.

Documents go in (PDF, DOCX, HTML, meeting transcripts, etc.). A compact JSON + AGENTS.md index comes out — ready for Claude Code, Codex, opencode, or any AI coding agent.

## Why

Passing raw documentation to an LLM wastes ~90% of tokens on noise (headers, footers, boilerplate) and loses structure (tables, sections). This tool uses [Docling](https://github.com/docling-project/docling) to extract clean, structured content, then classifies it into three engineering disciplines via [OpenRouter](https://openrouter.ai) free LLMs. The output is a compact, queryable JSON with full traceability back to source documents.

## Install

```bash
pip install -e .
cp .env.example .env
# add your OPENROUTER_API_KEY to .env
```

Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Usage

```bash
# Process a directory of documents → .context/
harness sources/

# Custom output directory
harness sources/ --output .my-context/

# Token count only (skip LLM — fast, no API calls)
harness sources/ --tokens-only

# Prioritize latency over throughput (--sort latency|throughput|price)
harness sources/ --sort latency
```

## Pipeline

```
Sources (PDF/DOCX/HTML/video/audio)
    │
    ▼
Docling extract → structured markdown
    │
    ▼
TokenCount(raw) → baseline token count
    │
    ▼
HierarchicalChunker → splits by section, ~2000 tokens each
    │
    ▼
OpenRouter /free → classify each chunk:
    ├── specs (requirements, data models, business rules)
    ├── loop_engineering (triggers, verifiable outputs, feedback loops)
    └── harness_engineering (context rules, validation gates, tool requirements)
    │
    ▼
Merge & deduplicate → single JSON
    │
    ▼
TokenCount(processed) → compare savings
    │
    ▼
Write .context/harness.json + .context/AGENTS.md
```

## Output

### `.context/harness.json`

```json
{
  "_meta": {
    "sources_processed": 3,
    "cost_comparison": {
      "raw_tokens": 52341,
      "processed_tokens": 4821,
      "reduction_pct": 90.8,
      "break_even_queries": 1
    }
  },
  "specs": {
    "summary": "...",
    "requirements": [{"id": "REQ-01", "description": "...", "source": "pdf:doc.pdf:§3.2", "priority": "high"}],
    "acceptance_criteria": [...],
    "data_models": [...],
    "business_rules": [...]
  },
  "loop_engineering": {
    "summary": "...",
    "automation_triggers": [...],
    "verification_points": [...],
    "feedback_loops": [...]
  },
  "harness_engineering": {
    "summary": "...",
    "context_rules": [...],
    "validation_gates": [...],
    "tool_requirements": [...]
  }
}
```

Every item carries a `source` field tracing back to the original document and section.

### `.context/AGENTS.md`

A short index (~25 lines) with links into `harness.json` — consumed directly by Claude Code, Codex, and opencode as project context.

## Supported formats

| Format | Extraction |
|--------|-----------|
| PDF, DOCX, PPTX, XLSX | Docling standard pipeline |
| HTML, Markdown, AsciiDoc | Docling simple pipeline |
| Images (PNG, JPG, TIFF) | OCR via RapidOCR |
| Audio (MP3, WAV, M4A) | ASR via Whisper |
| Video (MP4, MOV, WebM) | ASR via Whisper |

## Requirements

- Python ≥ 3.10
- `OPENROUTER_API_KEY` environment variable (free tier works)
- Dependencies: `docling`, `docling-core`, `openai`, `token-count`, `tiktoken`, `httpx`

## Tests

```bash
python tests/test_pipeline.py
```
