#!/usr/bin/env python3
"""Sonda de latência do classificador: mesma mensagem do harness, direto no /api/chat.

Mede tempo por chunk e se a resposta é JSON válido, sem passar pelo client OpenAI
(que faz retry sem `response_format` quando o parse falha e dobra o custo).
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import httpx

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
from docling_harness.prompts import CLASSIFY_SYSTEM_PROMPT  # noqa: E402

MODELS = ["qwen3.5:9b", "qwen3:14b"]
URL = "http://localhost:11434/api/chat"


def main() -> None:
    docs = json.loads((HERE / "cache" / "chunks.json").read_text(encoding="utf-8"))
    chunk = docs[1]["groups"][0]
    user = f"Heading path: {chunk.get('heading_path', '')}\n\nContent:\n{chunk['text']}"
    print(f"chunk: {len(chunk['text'])} chars")

    out = []
    for model in MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": 1200},
        }
        t0 = time.time()
        try:
            with httpx.Client(timeout=900) as client:
                r = client.post(URL, json=payload)
                r.raise_for_status()
                data = r.json()
            elapsed = time.time() - t0
            content = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count")
            ok = False
            try:
                json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
                ok = True
            except Exception:
                ok = False
            row = {"model": model, "seconds": round(elapsed, 1), "chars": len(content),
                   "eval_tokens": eval_count, "json_valido": ok}
        except Exception as exc:  # noqa: BLE001
            row = {"model": model, "erro": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(row, ensure_ascii=False), flush=True)
        out.append(row)

    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "probe_speed.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
