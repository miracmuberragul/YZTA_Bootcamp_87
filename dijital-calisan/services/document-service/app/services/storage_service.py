from __future__ import annotations

import hashlib
import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import MAX_UPLOAD_BYTES, STORAGE_PATH

ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}
CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class StoredFile:
    original_filename: str
    storage_key: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str


def safe_filename(filename: str | None) -> str:
    name = Path((filename or "").replace("\\", "/")).name.strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=422, detail="Geçerli bir dosya adı gerekiyor.")
    return name[:255]


def _validate_content(path: Path, suffix: str) -> str:
    expected_mime = ALLOWED_MIME_TYPES.get(suffix)
    if expected_mime is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Yalnızca PDF, DOCX ve TXT dosyaları destekleniyor.",
        )

    with path.open("rb") as stream:
        header = stream.read(8)

    valid = False
    if suffix == ".pdf":
        try:
            if header.startswith(b"%PDF-"):
                reader = PdfReader(path)
                valid = not reader.is_encrypted and len(reader.pages) > 0
        except (PdfReadError, OSError, ValueError):
            valid = False
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                uncompressed_size = sum(item.file_size for item in archive.infolist())
                valid = (
                    "[Content_Types].xml" in names
                    and "word/document.xml" in names
                    and uncompressed_size <= 100 * 1024 * 1024
                )
        except (zipfile.BadZipFile, OSError):
            valid = False
    elif suffix == ".txt":
        try:
            sample = path.read_bytes()
            valid = b"\x00" not in sample and bool(sample.decode("utf-8").strip())
        except UnicodeDecodeError:
            valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Dosya içeriği uzantısıyla uyuşmuyor veya dosya bozuk.",
        )
    return expected_mime


async def store_upload(upload: UploadFile, company_id: uuid.UUID, document_id: uuid.UUID) -> StoredFile:
    original_filename = safe_filename(upload.filename)
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Yalnızca PDF, DOCX ve TXT dosyaları destekleniyor.")

    company_dir = Path(STORAGE_PATH) / str(company_id)
    company_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
    storage_key = f"{company_id}/{document_id}{suffix}"
    final_path = Path(STORAGE_PATH) / storage_key
    temp_path = company_dir / f".{document_id}.uploading"
    digest = hashlib.sha256()
    size = 0

    try:
        with temp_path.open("xb") as target:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"Dosya en fazla {MAX_UPLOAD_BYTES // (1024 * 1024)} MB olabilir.")
                digest.update(chunk)
                target.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="Boş dosya yüklenemez.")
        mime_type = _validate_content(temp_path, suffix)
        os.replace(temp_path, final_path)
        return StoredFile(original_filename, storage_key, mime_type, size, digest.hexdigest())
    finally:
        await upload.close()
        temp_path.unlink(missing_ok=True)


def resolve_storage_key(storage_key: str) -> Path:
    root = Path(STORAGE_PATH).resolve()
    target = (root / storage_key).resolve()
    if root not in target.parents:
        raise ValueError("Invalid storage key")
    return target


def delete_file(storage_key: str) -> None:
    resolve_storage_key(storage_key).unlink(missing_ok=True)
