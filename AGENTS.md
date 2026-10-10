# docling-harness: guia para agentes

CLI Python que extrai documentos (Docling) e classifica os trechos com um LLM, gerando contexto para agentes. Detalhes de uso no `README.md` (leia por seção: `grep -n '^#' README.md`).

## Comandos

- Instalar: `pip install -e .` (venv CPU em `.venv/`; reinstalação em `REINSTALAR-AMBIENTE.md`)
- Rodar: `harness sources/` (saída em `.context/`); só contagem de tokens: `harness sources/ --tokens-only`
- Testes: `python tests/test_pipeline.py`

## Onde mexer

- Classificador: `src/docling_harness/classifier.py`. Limite de saída do LLM pela env `HARNESS_MAX_TOKENS` (opcional, sem default, lido em `_max_tokens()`).
- Modelo padrão: `qwen3:14b` via Ollama, escolhido no A/B de 10/10/2026.

## Não leia

- `experiments/results/*.json` e `experiments/cache/*.json`: saída gerada, centenas de KB. O resumo está em `experiments/FINDINGS.md`.
- `sources/` (PDFs reais, restritos), `.context*/` (saída da ferramenta), `.venv/`.
