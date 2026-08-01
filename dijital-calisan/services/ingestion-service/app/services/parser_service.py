from __future__ import annotations

import re
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import MAX_EXTRACTED_CHARACTERS, STORAGE_PATH


class ParserError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    block_index: int
    page_number: int | None
    section_title: str | None
    char_start: int
    char_end: int


@dataclass(frozen=True)
class ParsedDocument:
    blocks: list[ParsedBlock]
    page_count: int | None
    language: str
    character_count: int


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in value.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _detect_language(text: str) -> str:
    lowered = f" {text.lower()} "
    turkish_markers = (" ve ", " bir ", " için ", " ile ", " bu ", " olarak ", " şirket ", " çalışan ")
    english_markers = (" the ", " and ", " for ", " with ", " this ", " company ", " employee ")
    tr_score = sum(lowered.count(marker) for marker in turkish_markers) + sum(text.count(char) for char in "çğıöşüÇĞİÖŞÜ")
    en_score = sum(lowered.count(marker) for marker in english_markers)
    if tr_score == en_score == 0:
        return "und"
    return "tr" if tr_score >= en_score else "en"


def resolve_storage_key(storage_key: str) -> Path:
    root = Path(STORAGE_PATH).resolve()
    target = (root / storage_key).resolve()
    if root not in target.parents:
        raise ParserError("INVALID_STORAGE_KEY", "Geçersiz doküman storage anahtarı.")
    if not target.is_file():
        raise ParserError("DOCUMENT_FILE_NOT_FOUND", "Doküman dosyası storage alanında bulunamadı.")
    return target


def _build_document(raw_blocks: list[tuple[str, int | None, str | None]], page_count: int | None) -> ParsedDocument:
    blocks: list[ParsedBlock] = []
    cursor = 0
    for text, page_number, section_title in raw_blocks:
        normalized = normalize_text(text)
        if not normalized:
            continue
        if cursor + len(normalized) > MAX_EXTRACTED_CHARACTERS:
            raise ParserError("EXTRACTED_TEXT_TOO_LARGE", "Çıkarılan doküman metni izin verilen sınırı aşıyor.")
        blocks.append(
            ParsedBlock(
                text=normalized,
                block_index=len(blocks),
                page_number=page_number,
                section_title=normalize_text(section_title)[:255] if section_title else None,
                char_start=cursor,
                char_end=cursor + len(normalized),
            )
        )
        cursor += len(normalized) + 2

    combined = "\n\n".join(block.text for block in blocks)
    if len(re.sub(r"\s+", "", combined)) < 20:
        raise ParserError("EMPTY_DOCUMENT", "Dokümanda işlenebilir metin bulunamadı.")
    return ParsedDocument(
        blocks=blocks,
        page_count=page_count,
        language=_detect_language(combined),
        character_count=len(combined),
    )


def parse_pdf(path: Path) -> ParsedDocument:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ParserError("ENCRYPTED_PDF", "Şifreli PDF dosyaları desteklenmiyor.")
        raw_blocks = [(page.extract_text() or "", index, None) for index, page in enumerate(reader.pages, start=1)]
    except ParserError:
        raise
    except (PdfReadError, OSError, ValueError) as exc:
        raise ParserError("CORRUPTED_DOCUMENT", "PDF dosyası okunamadı veya bozuk.") from exc

    extracted = "".join(text for text, _, _ in raw_blocks)
    if len(re.sub(r"\s+", "", extracted)) < 20:
        raise ParserError("SCANNED_PDF_UNSUPPORTED", "PDF'de çıkarılabilir metin bulunamadı; taranmış PDF desteği henüz yok.")
    return _build_document(raw_blocks, len(reader.pages))


def parse_docx(path: Path) -> ParsedDocument:
    try:
        document = DocxDocument(path)
        raw_blocks: list[tuple[str, int | None, str | None]] = []
        current_section: str | None = None
        for item in document.iter_inner_content():
            if isinstance(item, Paragraph):
                text = normalize_text(item.text)
                if not text:
                    continue
                if item.style and item.style.name.lower().startswith("heading"):
                    current_section = text
                    continue
                raw_blocks.append((text, None, current_section))
            elif isinstance(item, Table):
                rows = [
                    " | ".join(normalize_text(cell.text) for cell in row.cells)
                    for row in item.rows
                ]
                table_text = "\n".join(row for row in rows if row.strip(" |"))
                if table_text:
                    raw_blocks.append((table_text, None, current_section))
        return _build_document(raw_blocks, None)
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, OSError, ValueError) as exc:
        raise ParserError("CORRUPTED_DOCUMENT", "DOCX dosyası okunamadı veya bozuk.") from exc


def parse_txt(path: Path) -> ParsedDocument:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ParserError("UNSUPPORTED_TEXT_ENCODING", "TXT dosyası UTF-8 formatında olmalıdır.") from exc
    except OSError as exc:
        raise ParserError("DOCUMENT_FILE_NOT_FOUND", "TXT dosyası okunamadı.") from exc
    paragraphs = re.split(r"\n\s*\n", text)
    return _build_document([(paragraph, None, None) for paragraph in paragraphs], None)


def parse_document(storage_key: str) -> ParsedDocument:
    path = resolve_storage_key(storage_key)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix == ".docx":
        return parse_docx(path)
    if suffix == ".txt":
        return parse_txt(path)
    raise ParserError("UNSUPPORTED_FILE_TYPE", "Yalnızca PDF, DOCX ve TXT dosyaları işlenebilir.")
