# Reinstalar o ambiente local do docling-harness

A pilha do docling (PyTorch ROCm, Docling, modelos de layout e OCR) foi removida do Python do usuário em
30/09/2026 para liberar ~16,7 GB. Este passo a passo recoloca tudo como estava.

O Ollama não faz parte disto: ele tem o próprio runtime ROCm em `/usr/local/lib/ollama` e os modelos em
`/usr/share/ollama`, e continuou funcionando sem o PyTorch.

## Pré-requisitos

- Python 3.14 do sistema (`python3 --version`); a instalação vai para o site do usuário (`~/.local`).
- GPU AMD (Radeon RX 9060 XT): usar o build **ROCm** do PyTorch, nunca o CUDA.
- Ollama rodando, com o modelo do classificador: `ollama pull qwen3:14b`.
- Espaço livre: ~17 GB.

## Passos

```bash
cd ~/Documents/Projects/Personal/docling-harness

# 1. PyTorch e torchvision ROCm (antes do docling, senão o pip puxa o build CUDA)
python3 -m pip install --user torch torchvision --index-url https://download.pytorch.org/whl/rocm7.2

# 2. O projeto e as dependências (docling, docling-core, openai, tiktoken, httpx)
python3 -m pip install --user -e .

# 3. Leitura de formatos OpenDocument, se precisar
python3 -m pip install --user "docling-slim[format-opendocument]"
```

Se o pip recusar com `externally-managed-environment`, repita o comando com `--break-system-packages`: ele
só afeta o `~/.local`, não o Python do sistema.

## Conferir

```bash
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # deve terminar em +rocm7.2 True
python3 -c "import docling; print('docling ok')"
ollama list                                                                     # qwen3:14b presente
```

No ROCm o PyTorch expõe a GPU como `cuda`; `torch.cuda.is_available()` igual a `True` é o esperado.

## Versões que estavam instaladas (30/09/2026)

Para reproduzir exatamente, fixe estas versões no passo 2:

```
torch==2.13.0+rocm7.2
torchvision==0.28.0+rocm7.2
triton==3.7.1
triton-rocm==3.7.1
docling==2.121.0
docling-slim==2.121.0
docling-core==2.92.0
docling-ibm-models==3.13.3
docling-parse==7.15.0
doclang==0.7.3
accelerate==1.14.0
transformers==5.14.1
tokenizers==0.22.2
safetensors==0.8.0
huggingface_hub==1.26.0
hf-xet==1.5.2
rapidocr==3.9.2
opencv-python==5.0.0.93
pyclipper==1.4.0
shapely==2.1.2
rtree==1.4.1
semchunk==3.2.5
tree-sitter==0.26.0
tree-sitter-c==0.24.2
tree-sitter-javascript==0.25.0
tree-sitter-python==0.25.0
tree-sitter-typescript==0.23.2
latex2mathml==3.81.0
token-count==0.2.1
```

Os pacotes `cuda-bindings`, `cuda-pathfinder` e `cuda-toolkit` também estavam instalados e foram removidos:
são da NVIDIA e não servem nesta máquina. Não reinstalar.
