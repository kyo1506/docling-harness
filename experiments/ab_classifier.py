#!/usr/bin/env python3
"""A/B do classificador do docling-harness (Fase A).

A extração (Docling) é a parte caríssima, então ela roda UMA vez e os chunks
ficam num cache. Cada arm (modelo) classifica o mesmo cache, o que torna a
comparação justa e permite repetir sem reextrair.

Uso:
  .venv/bin/python experiments/ab_classifier.py extract
  .venv/bin/python experiments/ab_classifier.py run qwen3:14b --limit 8
  .venv/bin/python experiments/ab_classifier.py run qwen3.5:9b --limit 8
  .venv/bin/python experiments/ab_classifier.py compare

`--limit N` classifica só os N primeiros chunks (custo controlado em CPU).
Sem `--limit`, classifica todos.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from docling_harness.extractor import (  # noqa: E402
    collect_sources,
    extract,
    release_accelerator,
    resolve_accelerator,
    set_accelerator,
)
from docling_harness.chunker import chunk_document, group_chunks  # noqa: E402
from docling_harness.classifier import (  # noqa: E402
    _SECTIONS,
    _KEY_FOR,
    classify_chunks,
    merge_items,
    set_llm_config,
)

CACHE_DIR = pathlib.Path(__file__).resolve().parent / "cache"
RESULTS_DIR = pathlib.Path(__file__).resolve().parent / "results"
CHUNKS_CACHE = CACHE_DIR / "chunks.json"


def _doc(result):
    return result.document if hasattr(result, "document") else None


def do_extract() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CHUNKS_CACHE.exists():
        print(f"cache já existe: {CHUNKS_CACHE} (apague para reextrair)")
        return

    sources = collect_sources(str(REPO / "sources"))
    if not sources:
        sys.exit("nenhum documento em sources/")

    set_accelerator(resolve_accelerator("cpu"))
    docs = []
    for src in sources:
        print(f"extraindo: {src}", flush=True)
        started = time.time()
        result = extract(src)
        markdown = result.document.export_to_markdown()
        doc = _doc(result)
        groups = group_chunks(chunk_document(doc)) if doc is not None else []
        docs.append({
            "src": src,
            "markdown_chars": len(markdown),
            "extract_seconds": round(time.time() - started, 1),
            "groups": groups,
        })
        print(f"  {len(groups)} grupos em {docs[-1]['extract_seconds']}s", flush=True)
        del result
    release_accelerator()

    CHUNKS_CACHE.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
    total = sum(len(d["groups"]) for d in docs)
    print(f"cache gravado: {CHUNKS_CACHE} ({len(docs)} docs, {total} grupos)")


def _slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "_", model.lower())


def _counts(sections: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for section, cats in _SECTIONS.items():
        for cat in cats:
            out[cat] = len(sections.get(section, {}).get(cat, []))
    return out


def _keys(sections: dict) -> set[str]:
    """Chaves naturais de cada item, para medir o que um arm perdeu em relação a outro."""
    out: set[str] = set()
    for section, cats in _SECTIONS.items():
        for cat in cats:
            for row in sections.get(section, {}).get(cat, []):
                if not isinstance(row, dict):
                    continue
                value = str(row.get(_KEY_FOR[cat], "")).strip().lower()
                out.add(f"{cat}:{re.sub(r'\\s+', ' ', value)}")
    return out


def do_run(model: str, limit: int | None) -> None:
    if not CHUNKS_CACHE.exists():
        sys.exit("rode `extract` antes")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    docs = json.loads(CHUNKS_CACHE.read_text(encoding="utf-8"))
    set_llm_config(model)

    all_items = []
    calls = 0
    started = time.time()
    for doc in docs:
        groups = doc["groups"]
        if limit is not None:
            groups = groups[:limit]
        if not groups:
            continue
        print(f"classificando {doc['src']}: {len(groups)} grupos com {model}", flush=True)
        items = classify_chunks(groups, [doc["src"]] * len(groups), max_workers=1)
        calls += len(groups)
        all_items.extend(items)

    sections = merge_items(all_items)
    elapsed = round(time.time() - started, 1)
    payload = {
        "model": model,
        "limit": limit,
        "calls": calls,
        "seconds": elapsed,
        "seconds_per_call": round(elapsed / calls, 1) if calls else None,
        "counts": _counts(sections),
        "keys": sorted(_keys(sections)),
        "sections": sections,
    }
    out = RESULTS_DIR / f"{_slug(model)}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{model}: {calls} chamadas em {elapsed}s → {out}")
    print("  " + json.dumps(payload["counts"], ensure_ascii=False))


def do_compare() -> None:
    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        sys.exit("nenhum resultado em experiments/results/")
    runs = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        # A pasta também guarda sondas (ex.: probe_speed.json), que são listas.
        if isinstance(data, dict) and "model" in data and "counts" in data:
            runs.append(data)
    if not runs:
        sys.exit("nenhum resultado de arm em experiments/results/")

    cats = [c for cats in _SECTIONS.values() for c in cats]
    width = max(len(r["model"]) for r in runs) + 2
    header = "categoria".ljust(20) + "".join(r["model"].ljust(width) for r in runs)
    print(header)
    print("-" * len(header))
    for cat in cats:
        row = cat.ljust(20) + "".join(str(r["counts"].get(cat, 0)).ljust(width) for r in runs)
        print(row)
    print("-" * len(header))
    print("TEMPO(s)".ljust(20) + "".join(str(r["seconds"]).ljust(width) for r in runs))
    print("CHAMADAS".ljust(20) + "".join(str(r["calls"]).ljust(width) for r in runs))

    if len(runs) >= 2:
        base, cand = runs[0], runs[-1]
        lost = sorted(set(base["keys"]) - set(cand["keys"]))
        gained = sorted(set(cand["keys"]) - set(base["keys"]))
        print(f"\nvs {base['model']}: perdidos={len(lost)} ganhos={len(gained)}")
        for k in lost[:15]:
            print(f"  - {k[:110]}")
        for k in gained[:15]:
            print(f"  + {k[:110]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B do classificador do docling-harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("extract", help="extrai sources/ e cacheia os chunks")
    run_p = sub.add_parser("run", help="classifica o cache com um modelo")
    run_p.add_argument("model")
    run_p.add_argument("--limit", type=int, default=None, help="classifica só os N primeiros chunks de cada doc")
    sub.add_parser("compare", help="compara os runs gravados")

    args = parser.parse_args()
    if args.cmd == "extract":
        do_extract()
    elif args.cmd == "run":
        do_run(args.model, args.limit)
    else:
        do_compare()


if __name__ == "__main__":
    main()
