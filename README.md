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

When the LLM merge step fails (large documents exceeding the safe payload limit), the output falls back to a programmatic merge with deduplication on requirement description and business rule text. The `_meta.merge_fallback` flag is set to `true` in this case.

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

`mistral:7b` is the default model. It's fast on consumer hardware and handles JSON output reliably. For better classification quality, consider larger models:

```bash
ollama pull llama3.1:8b   # better reasoning, still fits 16GB RAM
ollama pull qwen2.5:14b   # much better, needs 16GB+ RAM
```

To switch models, edit the `model` parameter in `src/docling_harness/classifier.py`.

### Large documents

The merge step has a 100K character safe payload limit. For documents producing enough chunks to exceed this limit, the tool performs clean truncation at JSON object boundaries. If the merge LLM still produces no output, a programmatic fallback merge runs — all classified items are included, with deduplication on requirement descriptions and business rules. The `_meta.merge_fallback` flag in the output indicates when this occurred.

### Classification quality

`mistral:7b` works well for Portuguese and English content. Small chunks (< 100 chars) may produce hallucinated classifications — the model fills in plausible but invented content. This is an inherent limitation of small local models. For production use with large documents, a 14B+ model is recommended.

## Requirements

- Python ≥ 3.10
- [Ollama](https://ollama.ai) with `mistral:7b` (or compatible model)
- Dependencies: `docling`, `docling-core`, `openai`, `token-count`, `tiktoken`, `httpx`

## Tests

```bash
python tests/test_pipeline.py
```
