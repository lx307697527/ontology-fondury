import io
import re
import zipfile

from pypdf import PdfReader

from app.config import get_settings


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith((".txt", ".md", ".markdown")):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        return _docx_text(data)
    raise ValueError(f"不支持的文件类型：{filename}（支持 txt/md/pdf/docx）")


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"<w:p[ >]", "\n<w:p ", xml)
    return re.sub(r"<[^>]+>", "", xml)


def chunk_text(text: str) -> list[str]:
    size, overlap = get_settings().chunk_size, get_settings().chunk_overlap
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            for sep in ("\n\n", "。", ". ", "；", "; ", "\n", " "):
                cut = text.rfind(sep, start + size // 2, end)
                if cut != -1:
                    end = cut + len(sep)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
