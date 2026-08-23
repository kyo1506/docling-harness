import re
from docling_core.transforms.chunker import HierarchicalChunker

chunker = HierarchicalChunker()

_SECTION_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s*\S")
_RULE_PATTERN_RE = re.compile(r"RQ\d+-R[NC]\d+|RN\d+", re.I)

# Long-form docs (books, manuals) without numbered headings collapse into a single
# oversized group otherwise, which OOMs the LLM context. Split groups past this size.
_MAX_GROUP_CHARS = 4000


def chunk_document(docling_document):
    chunks = list(chunker.chunk(docling_document))
    results = []
    for i, c in enumerate(chunks):
        text = c.text.strip()
        if not text:
            continue
        heading_path = ""
        if hasattr(c, "meta") and hasattr(c.meta, "headings"):
            heading_path = " > ".join(c.meta.headings) if c.meta.headings else ""
        results.append({
            "index": i,
            "text": text,
            "heading_path": heading_path,
        })
    return results


def group_chunks(chunks: list[dict]) -> list[dict]:
    """Reassemble hierarchical fragments into section groups.

    Fragments under running-header headings are absorbed into the current section;
    groups shorter than 40 chars with no rule/criterion pattern are dropped.
    Long-form docs (no numbered headings) are split by size so no group overflows
    the LLM context.
    """
    groups = []
    current = None
    current_heading = None
    for c in chunks:
        text = c.get("text", "").strip()
        heading = c.get("heading_path", "").strip()
        is_section = bool(_SECTION_RE.match(heading))
        oversized = current is not None and len(current["text"]) >= _MAX_GROUP_CHARS
        if current is None or (is_section and heading != current_heading) or oversized:
            if current is not None:
                groups.append(current)
            current = {"index": len(groups), "text": text, "heading_path": heading}
            current_heading = heading
        elif current is not None:
            current["text"] += "\n" + text
    if current is not None:
        groups.append(current)

    return [g for g in groups if _keep(g)]


def _keep(group: dict) -> bool:
    text = group["text"].strip()
    if len(text) >= 40:
        return True
    return bool(_RULE_PATTERN_RE.search(text))

