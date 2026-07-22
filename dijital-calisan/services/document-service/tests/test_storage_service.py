import io
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, UploadFile

from app.services.storage_service import resolve_storage_key, safe_filename, store_upload


def docx_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    return output.getvalue()


class StorageServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_filename_drops_path_components(self):
        self.assertEqual(safe_filename("../../secret.txt"), "secret.txt")
        self.assertEqual(safe_filename(r"..\..\secret.txt"), "secret.txt")

    async def test_stores_valid_files_under_tenant_directory(self):
        samples = [("policy.pdf", b"%PDF-1.7\ncontent"), ("guide.docx", docx_bytes()), ("note.txt", "Merhaba".encode())]
        with tempfile.TemporaryDirectory() as root, patch("app.services.storage_service.STORAGE_PATH", root):
            for filename, content in samples:
                document_id = uuid.uuid4()
                company_id = uuid.uuid4()
                result = await store_upload(UploadFile(filename=filename, file=io.BytesIO(content)), company_id, document_id)
                self.assertEqual(Path(root, result.storage_key).read_bytes(), content)
                self.assertEqual(len(result.checksum_sha256), 64)

    async def test_rejects_extension_spoofing(self):
        with tempfile.TemporaryDirectory() as root, patch("app.services.storage_service.STORAGE_PATH", root):
            with self.assertRaises(HTTPException) as error:
                await store_upload(UploadFile(filename="fake.pdf", file=io.BytesIO(b"not a pdf")), uuid.uuid4(), uuid.uuid4())
            self.assertEqual(error.exception.status_code, 415)

    async def test_rejects_oversized_file_and_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as root, patch("app.services.storage_service.STORAGE_PATH", root), patch("app.services.storage_service.MAX_UPLOAD_BYTES", 4):
            with self.assertRaises(HTTPException) as error:
                await store_upload(UploadFile(filename="note.txt", file=io.BytesIO(b"12345")), uuid.uuid4(), uuid.uuid4())
            self.assertEqual(error.exception.status_code, 413)
            self.assertEqual(list(Path(root).rglob("*.uploading")), [])

    def test_storage_key_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as root, patch("app.services.storage_service.STORAGE_PATH", root):
            with self.assertRaises(ValueError):
                resolve_storage_key("../../etc/passwd")


if __name__ == "__main__":
    unittest.main()
