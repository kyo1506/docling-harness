#!/usr/bin/env python3
"""Gate de decisão com Laya sobre os chunks cacheados (Fase A).

Laya é um modelo de decisão (não gera texto). Aqui ele só decide:
  1. `tem_conteudo` (noul): o chunk merece uma chamada de LLM?
  2. `disciplina` (choice): disciplina dominante, para priorizar/rotular.

Uso:
  .venv/bin/python experiments/laya_gate.py
Saída: experiments/results/laya_gate.json + resumo no terminal.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import time

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "cache" / "chunks.json"
OUT = HERE / "results" / "laya_gate.json"

QUESTIONS = {
    "disciplina": {
        "type": "choice",
        "instructions": "Em qual disciplina de engenharia este trecho se encaixa melhor?",
        "criteria": {
            "specs": "requisitos, regras de negocio, criterios de aceite, modelos de dados, contratos",
            "loop_engineering": "gatilhos de automacao, saidas verificaveis automaticamente, loops de feedback, gates humanos",
            "harness_engineering": "regras de contexto, convencoes de codigo, gates de validacao, ferramentas exigidas",
        },
    },
    "tem_conteudo": {
        "type": "noul",
        "instructions": "Este trecho traz conteudo tecnico util para o contexto de um agente de codigo?",
    },
}

# Sonda de sanidade: a direcao do `noul` precisa ser conferida, não presumida.
SANITY = [
    ("conteudo", "O sistema deve registrar toda alteracao de perfil em log de auditoria imutavel."),
    ("ruido", "Sumario. Agradecimentos. Referencias bibliograficas. Indice remissivo."),
]


def main() -> None:
    from laya import Router

    docs = json.loads(CACHE.read_text(encoding="utf-8"))
    router = Router()

    rows = []
    started = time.time()
    for doc in docs:
        for i, chunk in enumerate(doc["groups"]):
            heading = chunk.get("heading_path", "")
            text = chunk["text"]
            state = f"{heading}\n\n{text}" if heading else text
            t0 = time.time()
            res = router.predict(state, QUESTIONS, max_len=8192)
            elapsed = time.time() - t0
            answers = res["answers"]
            rows.append({
                "src": doc["src"],
                "index": i,
                "heading": heading,
                "chars": len(text),
                "model": res.get("routing", {}).get("model"),
                "disciplina": answers["disciplina"]["choice"],
                "disciplina_conf": answers["disciplina"]["confidence"],
                "disciplina_probs": answers["disciplina"]["probabilities"],
                "tem_conteudo": answers["tem_conteudo"]["noul"],
                "segundos": round(elapsed, 3),
            })
            print(f"  [{i:02d}] {answers['disciplina']['choice']:20s} "
                  f"conf={answers['disciplina']['confidence']:.3f} "
                  f"noul={answers['tem_conteudo']['noul']:.3f} {elapsed:.2f}s "
                  f"{heading[:50]}", flush=True)

    total = time.time() - started
    sanity = []
    for label, text in SANITY:
        res = router.predict(text, {"tem_conteudo": QUESTIONS["tem_conteudo"]}, max_len=8192)
        sanity.append({"label": label, "noul": res["answers"]["tem_conteudo"]["noul"]})
        print(f"sanity {label}: noul={sanity[-1]['noul']:.3f}")

    dist = {}
    for r in rows:
        dist[r["disciplina"]] = dist.get(r["disciplina"], 0) + 1
    payload = {
        "chunks": len(rows),
        "seconds": round(total, 1),
        "seconds_per_chunk": round(total / len(rows), 3) if rows else None,
        "disciplina_dist": dist,
        "disciplina_conf_mediana": round(statistics.median(r["disciplina_conf"] for r in rows), 3),
        "noul_mediana": round(statistics.median(r["tem_conteudo"] for r in rows), 3),
        "noul_acima_0_5": sum(1 for r in rows if r["tem_conteudo"] > 0.5),
        "sanity": sanity,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== resumo ===")
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
