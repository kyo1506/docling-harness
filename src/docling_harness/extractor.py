import gc
import os
import pathlib
import tempfile
import httpx
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


AUDIO_VIDEO_EXTENSIONS = {".mp3", ".wav", ".mp4", ".mov", ".webm", ".m4a", ".ogg"}
URL_PREFIXES = ("http://", "https://")


_ACCELERATOR_BY_NAME = {
    "auto": AcceleratorDevice.AUTO,
    "cuda": AcceleratorDevice.CUDA,
    "cpu": AcceleratorDevice.CPU,
}


def resolve_accelerator(name: str = "auto") -> AcceleratorDevice:
    """Map a CLI accelerator name to its device enum, raising on unknown values."""
    key = (name or "auto").lower()
    if key not in _ACCELERATOR_BY_NAME:
        raise ValueError(f"Unknown accelerator '{name}'. Expected one of: auto, cuda, cpu")
    return _ACCELERATOR_BY_NAME[key]


def _resolve_device(device: AcceleratorDevice) -> AcceleratorDevice:
    """Map AUTO to CUDA when a GPU is present (avoids docling's slow AUTO path on ROCm),
    else fall back to CPU."""
    if device is AcceleratorDevice.AUTO:
        try:
            import torch
            if torch.cuda.is_available():
                return AcceleratorDevice.CUDA
        except ImportError:
            pass
        return AcceleratorDevice.CPU
    return device


def _build_converter(device: AcceleratorDevice = AcceleratorDevice.AUTO) -> DocumentConverter:
    resolved = _resolve_device(device)
    # On ROCm, docling's sdpa attention needs this flag for the fast path.
    if resolved is AcceleratorDevice.CUDA:
        os.environ.setdefault("TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL", "1")
    # batch 16: safe on 16 GB for dense/high-res PDFs; 64 OOMs and loses pages.
    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=resolved),
        layout_batch_size=16,
        ocr_batch_size=16,
        ocr_options=RapidOcrOptions(backend="torch", lang=["pt"]),
    )
    return DocumentConverter(format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
    })


converter = _build_converter()


def set_accelerator(device: AcceleratorDevice) -> AcceleratorDevice:
    """Rebuild the shared converter with a different accelerator device.

    Returns the resolved device (AUTO becomes CUDA or CPU), so callers can log it.
    """
    global converter
    resolved = _resolve_device(device)
    converter = _build_converter(device)
    return resolved


def release_accelerator():
    """Drop the Docling converter (and its GPU-resident models) to free VRAM.

    The shared converter caches its loaded pipeline models on the accelerator device.
    Rebuilding it on CPU cheaply dereferences those GPU models (construction does not
    load anything), then gc + torch.cuda.empty_cache() reclaim the memory so the next
    GPU consumer (e.g. the Ollama LLM) does not contend for the same card.
    """
    global converter
    converter = _build_converter(AcceleratorDevice.CPU)
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def free_ollama_vram(base_url: str | None = None):
    """Best-effort: unload resident Ollama models to free VRAM for Docling's GPU pass.

    Docling's GPU extraction and a resident 14B LLM (~15 GB at 32K context) cannot share a
    16 GB card. Even in a two-pass run, an Ollama model left loaded by a prior chat/run keeps
    that VRAM busy, so the PDF layout stage OOMs. This pings the local Ollama server to evict
    whatever it has loaded. It only acts on a local Ollama endpoint and never raises.
    """
    host = (base_url or "http://localhost:11434/v1").replace("/v1", "").rstrip("/")
    try:
        if not host.startswith("http://localhost:11434") and not host.startswith("http://127.0.0.1:11434"):
            return
        ps = httpx.get(f"{host}/api/ps", timeout=5)
        for m in ps.json().get("models", []):
            name = m.get("model")
            if not name:
                continue
            try:
                # keep_alive=0 schedules an immediate unload once the model is idle.
                httpx.post(f"{host}/api/generate", json={"model": name, "keep_alive": 0}, timeout=10)
            except Exception:
                pass
    except Exception:
        pass


def _is_url(source: str) -> bool:
    return source.startswith(URL_PREFIXES)


def _is_audio_video(path: str) -> bool:
    return pathlib.Path(path).suffix.lower() in AUDIO_VIDEO_EXTENSIONS


def extract(source: str):
    if _is_url(source):
        resp = httpx.get(source, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        suffix = ""
        if "pdf" in content_type:
            suffix = ".pdf"
        elif "html" in content_type:
            suffix = ".html"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name
        try:
            result = converter.convert(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        result = converter.convert(source)

    return result


def collect_sources(sources_dir: str) -> list[str]:
    files = []
    p = pathlib.Path(sources_dir)
    if p.is_file():
        return [str(p)]
    for f in sorted(p.rglob("*")):
        if f.is_file() and f.suffix.lower() not in {".json", ".yaml", ".yml", ".toml", ".lock"}:
            files.append(str(f))
    return files
