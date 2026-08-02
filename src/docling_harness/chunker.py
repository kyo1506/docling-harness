from docling_core.transforms.chunker import HierarchicalChunker

chunker = HierarchicalChunker()


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
