# Ingestion Service — Faz 5

Yüklenmiş PDF, DOCX ve UTF-8 TXT belgelerini metin bloklarına dönüştürür, gerçek model tokenizerı ile deterministik chunk'lar üretir ve PostgreSQL'e kaydeder.

## İş akışı

`queued → processing → succeeded | failed`

- Kalıcı `ingestion_jobs` tablosu kuyruk kaydıdır.
- Background worker servis yeniden başladığında `queued` işleri yeniden bulur.
- Dosya işlenmeden önce SHA-256 checksum tekrar doğrulanır.
- Başarılı chunk yazımı tek transaction içinde yapılır.
- Retrieval yalnız `documents.status = processed` kayıtlarını kullanmalıdır.

## Parser

- PDF: metin ve 1 tabanlı sayfa numarası; şifreli, bozuk ve taranmış PDF hata kodları.
- DOCX: paragraf, heading bağlamı ve tablo satırları.
- TXT: yalnız UTF-8, boş metin kontrolü.
- Metin NFKC Unicode normalizasyonundan geçirilir; küçük harfe çevrilmez.

## Tokenization ve chunking

- Tokenizer: `tiktoken`, `text-embedding-3-small` için `cl100k_base`.
- Varsayılan chunk bütçesi: 500 token.
- Varsayılan overlap: 75 token.
- Öncelik: paragraf/cümle sınırı; bütçeyi aşan tek cümlede token-aware karakter sınırı.
- Her chunk: token sayısı, SHA-256 content hash, sayfa aralığı, bölüm başlığı ve karakter aralığı taşır.
- Tokenizer sözlüğü Docker build sırasında image içine cache'lenir; runtime ağ erişimine ihtiyaç duymaz.

## Internal API

- `POST /internal/v1/ingestion/jobs`
- `GET /internal/v1/ingestion/jobs/{job_id}`
- `POST /internal/v1/ingestion/jobs/{job_id}/process`
- `DELETE /internal/v1/ingestion/documents/{document_id}?company_id=...`

Tüm endpoint'ler `X-Internal-API-Key` ister ve gateway üzerinden dışarı açılmaz.

## Test

```bash
pip install -r requirements-dev.txt
TIKTOKEN_CACHE_DIR=/tmp/officeiq-tiktoken-cache \
  PYTHONPATH=. pytest -q
```
