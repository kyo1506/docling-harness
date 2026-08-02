## Why

Developers and AI coding agents consume large volumes of documentation (PDFs, DOCX, web pages, meeting transcripts) to understand requirements, architecture, and business rules. Passing raw documents directly to an LLM wastes tokens on noise (headers, footers, boilerplate) and loses structure (tables, sections, cross-references). This tool pre-processes documentation through Docling for structured extraction, then classifies and summarizes content into a compact, agent-ready JSON — reducing token consumption by ~90% across repeated queries while preserving traceability back to source documents.

## What Changes

- New CLI tool `docling-harness` that accepts a directory of source documents and outputs structured agent context
- Docling-based extraction pipeline supporting PDF, DOCX, PPTX, XLSX, HTML, Markdown, images (OCR), and video/audio (ASR via Whisper)
- Hierarchical chunking with intelligent LLM classification into three engineering disciplines: Spec-Driven Development, Loop Engineering, and Harness Engineering
- Token cost comparison reporting raw vs. processed token counts using TokenCount
- Output: `harness.json` (structured context) + `AGENTS.md` (short index for agent discovery)

## Capabilities

### New Capabilities

- `document-extraction`: Extract structured content from PDF, DOCX, PPTX, XLSX, HTML, Markdown, images, audio, and video files using Docling. Output clean markdown with tables, section hierarchy, and image captions preserved.
- `context-generation`: Chunk extracted content, classify each chunk into specs/loop/harness categories via OpenRouter free LLM, summarize per chunk, and merge into a single structured JSON with source traceability on every item.
- `token-comparison`: Count tokens of raw Docling markdown output vs. the final processed JSON. Generate a cost comparison report showing reduction percentage, absolute savings, and break-even query count.
- `agent-context-output`: Generate `harness.json` with categorized context plus an `AGENTS.md` index file pointing to JSON sections for direct agent consumption (Claude Code, Codex, opencode).

## Impact

- New Python package: `docling-harness` with CLI entry point
- Dependencies: `docling`, `docling-core`, `openai` (OpenRouter base_url), `token-count`, `tiktoken`, `httpx`
- Uses `OPENROUTER_API_KEY` environment variable for LLM calls
- Output directory: `.context/` (JSON + AGENTS.md)
- No changes to existing code or infrastructure
