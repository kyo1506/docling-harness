import os
import pathlib
import tempfile
import httpx
from docling.document_converter import DocumentConverter


AUDIO_VIDEO_EXTENSIONS = {".mp3", ".wav", ".mp4", ".mov", ".webm", ".m4a", ".ogg"}
URL_PREFIXES = ("http://", "https://")

converter = DocumentConverter()


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
