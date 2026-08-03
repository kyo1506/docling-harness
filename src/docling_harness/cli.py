import argparse
import logging
import sys

from .extractor import extract, collect_sources
from .chunker import chunk_document
from .classifier import classify_chunk
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
    args = parser.parse_args()

    sources = collect_sources(args.sources)
    if not sources:
        logger.error("No source files found in %s", args.sources)
        sys.exit(1)

    logger.info("Found %d source(s)", len(sources))

    all_raw_texts = []
    all_chunk_items = []

    for src in sources:
        logger.info("Processing: %s", src)
        result = extract(src)
        raw_text = result.document.export_to_markdown()
        all_raw_texts.append(raw_text)

        if args.tokens_only:
            continue

        doc = _get_doc(result)
        if doc is None:
            continue

        chunks = chunk_document(doc)
        for ch in chunks:
            item = classify_chunk(ch, src)
            all_chunk_items.append(item)
            logger.info("  chunk %d classified (model: %s)", ch["index"], item.model_used)

    if args.tokens_only:
        combined_raw = "\n".join(all_raw_texts)
        raw_count = count_tokens(combined_raw)
        logger.info("=== Token Count ===")
        logger.info("Raw markdown tokens: %d (no processing applied)", raw_count)
        return

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

    logger.info("Raw tokens: %d → Processed tokens: %d (%.1f%% reduction)",
                comparison.raw_tokens, comparison.processed_tokens, comparison.reduction_pct)

    write_output(output_data, comparison, args.output, len(sources))
    logger.info("Output written to %s/", args.output)


def _get_doc(result):
    if hasattr(result, "document"):
        return result.document
    return None
