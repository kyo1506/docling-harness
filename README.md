# docling-harness

CLI tool that extracts, classifies, and consolidates documentation into structured, agent-ready context — optimized for Spec-Driven Development, Loop Engineering, and Harness Engineering workflows.

Documents go in (PDF, DOCX, HTML, meeting transcripts, etc.). A compact JSON + AGENTS.md index comes out — ready for Claude Code, Codex, opencode, or any AI coding agent.

## Why

Passing raw documentation to an LLM wastes ~90% of tokens on noise (headers, footers, boilerplate) and loses structure (tables, sections). This tool uses [Docling](https://github.com/docling-project/docling) to extract clean, structured content, then classifies it into three engineering disciplines via local LLMs through [Ollama](https://ollama.ai). The output is a compact, queryable JSON with full traceability back to source documents.

## Install

```bash
pip install -e .
```

**Prerequisites:**
- [Ollama](https://ollama.ai) installed and running
- Pull the model: `ollama pull mistral:7b`

The classifier connects to Ollama at `http://localhost:11434` — no API keys or accounts needed.

## Usage

```bash
# Process a directory of documents → .context/
harness sources/

# Custom output directory
harness sources/ --output .my-context/

# Token count only (skip LLM — fast, no API calls)
harness sources/ --tokens-only
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
HierarchicalChunker → splits by section
    │
    ▼
Ollama (mistral:7b) → classify each chunk:
    ├── specs (requirements, data models, business rules)
    ├── loop_engineering (triggers, verifiable outputs, feedback loops)
    └── harness_engineering (context rules, validation gates, tool requirements)
    │
    ▼
Merge & deduplicate → single JSON (LLM-based merge with programmatic fallback)
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

The merge step is lossless and programmatic: every classified item is kept, deduplicated only on identical text, and assigned stable ids (`REQ-01`, `AC-01`, `BR-01`, `DM-01`). Structured business rules (`RQxx-RNxx`) and acceptance criteria (`RQxx-CAxx`) are additionally captured deterministically from the raw text so no rule is lost to LLM summarization. `_meta.merge_mode` is set to `"lossless_programmatic"`.

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

## Considerations

### Model choice

The default backend is a local Ollama instance (`http://localhost:11434/v1`, model `qwen2.5:14b`) — no API key, content stays on the machine. For better quality, larger local models work:

```bash
ollama pull qwen2.5:14b   # current default
ollama pull llama3.1:8b   # faster, lower quality
```

### Switching providers

The LLM backend is configurable via environment variables (or a `--model` flag), so a remote OpenAI-compatible provider needs no code change:

```bash
# DeepSeek (or any OpenAI-compatible endpoint)
export HARNESS_LLM_BASE_URL=https://api.deepseek.com
export HARNESS_LLM_API_KEY=sk-...
export HARNESS_LLM_MODEL=deepseek-chat

# one-off model override
harness sources/ --model deepseek-chat
```

Precedence: `--model` flag > `HARNESS_LLM_MODEL` > default. Note: a remote provider sends document content off-machine — keep restricted documents on the local default.

### Large documents

Classification runs per document section group (each RQ/section classified as a unit), and the merge is a deterministic programmatic pass — there is no LLM merge and no payload size limit. The processed output grows roughly with the number of extracted rules; for dense specification documents the token "reduction" is modest because the document itself is rules.

### Classification quality

`qwen2.5:14b` works well for Portuguese and English content. Small chunks (< 100 chars) may produce hallucinated classifications — the model fills in plausible but invented content. This is an inherent limitation of small local models. For production use with large documents, a 14B+ local model or a remote provider is recommended.

## Requirements

- Python ≥ 3.10
- [Ollama](https://ollama.ai) with `mistral:7b` (or compatible model)
- Dependencies: `docling`, `docling-core`, `openai`, `token-count`, `tiktoken`, `httpx`

## Tests

```bash
python tests/test_pipeline.py
```
