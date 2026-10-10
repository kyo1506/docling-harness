# Fase A: achados do A/B (2026-10-10)

Medição feita sobre os 2 documentos de `sources/`, extraídos uma vez em CPU
(233,5 s → 8 + 21 = 29 grupos, cache em `experiments/cache/chunks.json`).

Venv CPU em `.venv/` (torch 2.14.1+cpu, docling 2.137.0); não toca no
`~/.local` ROCm. O Ollama roda com GPU; o venv só extrai.

## 1. Laya (modelo de decisão): não se paga aqui

Instalado via `pip install laya` (0.4.2), `Router` roteou o português para o
checkpoint `multilingual` corretamente.

| Medida | Resultado |
|---|---|
| `noul` (tem conteúdo?) mediana | 0.911 |
| chunks com `noul > 0.5` | **29 / 29** |
| confiança (margem) da disciplina, mediana | **0.015** |
| distribuição da disciplina | 13 harness / 11 loop / 5 specs |
| latência | 5,44 s/chunk em CPU |

Sonda de sanidade confere a direção do `noul`: texto técnico → 0.80; ruído
(índice/sumário) → 0.083. O problema não é a direção, é o corpus: depois do
chunking do Docling **todo chunk é seção substantiva**, então o gate filtra
zero e a disciplina fica empatada.

**Conclusão:** não integrar o gate no `classifier.py`. Só passa a valer com
fine-tuning no domínio (o upstream documenta o loop RLCD), ou não vale.

## 2. qwen3.5:9b vs qwen3:14b: não trocar

Os dois arms rodaram os 29 chunks com `HARNESS_MAX_TOKENS=1600`.

| categoria | qwen3.5:9b | qwen3:14b |
|---|---|---|
| requirements | 37 | 72 |
| acceptance_criteria | 16 | 36 |
| data_models | 17 | 27 |
| business_rules | 17 | 45 |
| automation_triggers | 1 | 20 |
| verification_points | 11 | 21 |
| feedback_loops | 1 | 13 |
| context_rules | 25 | 38 |
| validation_gates | 18 | 36 |
| tool_requirements | 11 | 34 |
| **total** | **155** | **342** |
| tempo (29 chamadas) | 922,8 s | 1261,3 s |

O qwen3:14b trouxe 332 itens que o qwen3.5 não trouxe (o inverso foram 142).

A diferença **não é artefato do teto de tokens**: com `num_predict=4096` em 3
chunks, o qwen3.5:9b devolveu JSON válido em **1 de 3** (13 itens) contra
**3 de 3** do qwen3:14b (62 itens). O endpoint OpenAI-compatible do Ollama não
faz o qwen3.5 (thinking) respeitar `response_format=json_object`.

**Conclusão:** manter `qwen3:14b`. Não atualizar para `qwen3.5:9b` neste harness.

## 3. Mudança no código

`classifier.py` ganhou `HARNESS_MAX_TOKENS` (opcional, sem default): sem a env o
comportamento é o de antes. Foi o que tornou os arms viáveis; sem teto, cada
chunk passava de 5 min.

## Reproduzir

```bash
.venv/bin/python experiments/ab_classifier.py extract
HARNESS_MAX_TOKENS=1600 .venv/bin/python experiments/ab_classifier.py run qwen3.5:9b
HARNESS_MAX_TOKENS=1600 .venv/bin/python experiments/ab_classifier.py run qwen3:14b
.venv/bin/python experiments/ab_classifier.py compare
.venv/bin/python experiments/laya_gate.py
.venv/bin/python experiments/probe_speed.py
```

O GGUF `hf.co/ggml-org/Laya-GGUF:BF16` (844 MB) foi baixado mas **não é usado**:
tem TEMPLATE `{{ .Prompt }}` cru e serve só pelo llama.cpp com o formato interno;
o caminho suportado é o pacote Python `laya`.
