import argparse
import logging
import sys

from .extractor import extract, collect_sources, resolve_accelerator, set_accelerator, release_accelerator, free_ollama_vram
from .chunker import chunk_document, group_chunks
from .classifier import classify_chunks, set_llm_config, resolve_llm_config
from .rules_extractor import structured_extract, merge_deterministic, apply_requirements
from .merger import merge
from .token_counter import compute_comparison, count_tokens
from .output import write_output

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog="harness", description="Docling Harness — extract and classify docs for AI agents")
    parser.add_argument("sources", help="Directory or file path containing source documents")
    parser.add_argument("--output", default=".context", help="Output directory (default: .context/)")
    parser.add_argument("--tokens-only", action="store_true", help="Only count tokens, skip LLM classification")
    parser.add_argument("--model", help="Override the LLM model (overrides HARNESS_LLM_MODEL)")
    parser.add_argument("--accelerator", default="auto", choices=["auto", "cuda", "cpu"],
                        help="Docling accelerator device (default: auto)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Concurrent LLM classification calls (default: 4)")
    args = parser.parse_args()

    sources = collect_sources(args.sources)
    if not sources:
        logger.error("No source files found in %s", args.sources)
        sys.exit(1)

    logger.info("Found %d source(s)", len(sources))

    device = resolve_accelerator(args.accelerator)
    resolved = set_accelerator(device)
    logger.info("Accelerator: %s (requested: %s)", resolved.value, device.value)

    if not args.tokens_only:
        base_url, _, model = set_llm_config(args.model)
        logger.info("LLM backend: %s (model: %s, workers: %d)", base_url, model, args.workers)
    else:
        base_url = resolve_llm_config(args.model)[0]

    # On GPU extraction, evict any resident Ollama model first: a 14B model left loaded
    # by a previous chat/run (~15 GB at 32K context) otherwise OOMs Docling's layout pass.
    if getattr(resolved, "value", None) == "cuda":
        free_ollama_vram(base_url)

    all_raw_texts = []
    pending = []  # (src, src_ref, groups) to classify in the second pass

    # Pass 1 — extract & chunk every source. Docling runs on the GPU here while the
    # LLM model is NOT loaded yet, so GPU extraction gets the full VRAM (no OOM from
    # contending with the resident qwen3).
    for src in sources:
        logger.info("Extracting: %s", src)
        result = extract(src)
        raw_text = result.document.export_to_markdown()
        all_raw_texts.append(raw_text)

        if args.tokens_only:
            del result
            continue

        doc = _get_doc(result)
        if doc is not None:
            groups = group_chunks(chunk_document(doc))
            src_ref = f"file:{src}"
            pending.append((src, src_ref, groups))
        del result

    if args.tokens_only:
        combined_raw = "\n".join(all_raw_texts)
        raw_count = count_tokens(combined_raw)
        logger.info("=== Token Count ===")
        logger.info("Raw markdown tokens: %d (no processing applied)", raw_count)
        return

    if not pending:
        logger.error("No documents could be extracted. Check your sources.")
        sys.exit(1)

    # Free Docling's GPU models before the LLM loads, so qwen3 and Docling never share
    # the same VRAM. Keep_alive won't save us because a GPU doc's extraction starts the
    # instant the previous doc's last LLM call finishes.
    release_accelerator()

    # Pass 2 — classify every chunk across all docs. The Ollama model loads once here
    # (full GPU available) and stays warm for the whole classification pass.
    all_chunk_items = []
    for src, src_ref, groups in pending:
        items = classify_chunks(groups, [src] * len(groups), max_workers=args.workers)
        for i, (ch, item) in enumerate(zip(groups, items)):
            heading = ch.get("heading_path", "")
            det = structured_extract(ch["text"], heading, src_ref)
            item.items = merge_deterministic(item.items, det)
            item.items = apply_requirements(item.items, heading, src_ref, ch["text"])
            item.source = f"{src_ref}§{heading}" if heading else src_ref
            all_chunk_items.append(item)
            logger.info("  section %d classified (model: %s)", i, item.model_used)

    if not all_chunk_items:
        logger.error("No content was classified. Check your sources and ensure Ollama is running.")
        sys.exit(1)

    logger.info("Merging %d chunk results...", len(all_chunk_items))
    output_data = merge(all_chunk_items)

    combined_raw = "\n".join(all_raw_texts)
    comparison = compute_comparison(combined_raw, {
        "specs": output_data.specs,
        "loop_engineering": output_data.loop_engineering,
        "harness_engineering": output_data.harness_engineering,
    })

    if comparison.reduction_pct >= 0:
        logger.info("Raw tokens: %d → Processed tokens: %d (%.1f%% reduction)",
                    comparison.raw_tokens, comparison.processed_tokens, comparison.reduction_pct)
    else:
        logger.info("Raw tokens: %d → Processed tokens: %d (%.1f%% growth)",
                    comparison.raw_tokens, comparison.processed_tokens, -comparison.reduction_pct)

    write_output(output_data, comparison, args.output, len(sources))
    logger.info("Output written to %s/", args.output)


def _get_doc(result):
    if hasattr(result, "document"):
        return result.document
    return None
