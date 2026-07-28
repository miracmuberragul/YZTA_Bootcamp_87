#!/usr/bin/env python3
"""Import a folder tree into OfficeIQ, mapping top-level folders to categories."""

from __future__ import annotations

import argparse
import getpass
import mimetypes
import sys
import time
from pathlib import Path

import requests


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
DEFAULT_COLORS = [
    "#2563EB", "#7C3AED", "#DB2777", "#DC2626", "#EA580C",
    "#CA8A04", "#16A34A", "#0D9488", "#0891B2", "#4F46E5",
]


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=90, **kwargs)
    if not response.ok:
        raise RuntimeError(f"{method} {url}: {response.status_code} {response.text[:300]}")
    return response.json() if response.content else None


def login(session: requests.Session, base_url: str, slug: str, email: str, password: str) -> None:
    payload = request_json(
        session,
        "POST",
        f"{base_url}/api/auth/login",
        json={"company_slug": slug, "email": email, "password": password},
    )
    session.headers["Authorization"] = f"Bearer {payload['access_token']}"


def ensure_categories(session: requests.Session, base_url: str, names: list[str]) -> dict[str, str]:
    existing = request_json(session, "GET", f"{base_url}/api/v1/categories")
    category_ids = {item["name"]: item["id"] for item in existing}
    for index, name in enumerate(names):
        if name in category_ids:
            continue
        created = request_json(
            session,
            "POST",
            f"{base_url}/api/v1/categories",
            json={"name": name, "color": DEFAULT_COLORS[index % len(DEFAULT_COLORS)]},
        )
        category_ids[name] = created["id"]
    return category_ids


def wait_for_documents(
    session: requests.Session,
    base_url: str,
    document_ids: list[str],
    timeout_seconds: int,
) -> dict[str, str]:
    deadline = time.monotonic() + timeout_seconds
    remaining = set(document_ids)
    statuses: dict[str, str] = {}
    while remaining and time.monotonic() < deadline:
        for document_id in list(remaining):
            item = request_json(session, "GET", f"{base_url}/api/v1/documents/{document_id}")
            statuses[document_id] = item["status"]
            if item["status"] in {"processed", "failed"}:
                remaining.remove(document_id)
        if remaining:
            time.sleep(3)
    for document_id in remaining:
        statuses[document_id] = "timeout"
    return statuses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--company-slug", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password")
    parser.add_argument("--wait", type=int, default=900, metavar="SECONDS")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir():
        parser.error(f"Kaynak klasör bulunamadı: {source}")

    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        parser.error("Desteklenen dosya bulunamadı (PDF, DOCX, TXT).")

    category_names = sorted({path.relative_to(source).parts[0] for path in files})
    password = args.password or getpass.getpass("OfficeIQ parolası: ")
    base_url = args.base_url.rstrip("/")
    session = requests.Session()
    login(session, base_url, args.company_slug, args.email, password)
    category_ids = ensure_categories(session, base_url, category_names)

    uploaded: list[str] = []
    duplicates = 0
    for index, path in enumerate(files, start=1):
        relative = path.relative_to(source)
        category_name = relative.parts[0]
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as handle:
            result = request_json(
                session,
                "POST",
                f"{base_url}/api/v1/documents",
                files={"file": (path.name, handle, mime_type)},
                data={"category": "other", "display_name": path.stem},
            )
        document_id = result["document_id"]
        if result.get("duplicate"):
            duplicates += 1
        else:
            uploaded.append(document_id)
        request_json(
            session,
            "PATCH",
            f"{base_url}/api/v1/documents/{document_id}/category",
            json={"category_id": category_ids[category_name]},
        )
        print(f"[{index}/{len(files)}] {relative}")

    statuses = wait_for_documents(session, base_url, uploaded, args.wait) if uploaded else {}
    processed = sum(status == "processed" for status in statuses.values())
    failed = sum(status == "failed" for status in statuses.values())
    timed_out = sum(status == "timeout" for status in statuses.values())
    print(
        f"Sonuç: {len(files)} dosya, {len(category_names)} kategori, "
        f"{len(uploaded)} yeni, {duplicates} tekrar, "
        f"{processed} işlendi, {failed} hata, {timed_out} zaman aşımı."
    )
    return 1 if failed or timed_out else 0


if __name__ == "__main__":
    sys.exit(main())
