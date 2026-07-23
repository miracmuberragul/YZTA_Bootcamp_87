# Document Service

Faz 4 doküman yaşam döngüsünü yönetir. PDF, DOCX ve UTF-8 TXT dosyalarını kabul eder; içerik türünü doğrular, tenant dizinine güvenli bir storage key ile kaydeder ve Ingestion Service üzerinde kalıcı bir job oluşturur.

## API

- `POST /api/v1/documents` — admin; multipart `file`, `category`, opsiyonel `display_name`
- `GET /api/v1/documents` — tenant bazlı liste; `page`, `page_size`, `status`, `category`
- `GET /api/v1/documents/{id}` — tenant bazlı detay/durum
- `GET /api/v1/documents/{id}/content` — yetkili indirme
- `POST /api/v1/documents/{id}/retry-ingestion` — admin
- `DELETE /api/v1/documents/{id}` — admin ve idempotent silme

Yükleme `202 Accepted` döner. Aynı şirket aynı içeriği tekrar gönderirse yeni fiziksel kopya oluşturulmaz ve mevcut doküman `duplicate: true` ile döner. Ingestion geçici olarak erişilemezse doküman `uploaded` durumunda ve kullanıcıya gösterilebilir hata mesajıyla kalır; retry endpoint'i ile yeniden kuyruğa alınır.

## Güvenlik ve sınırlar

- En fazla 15 MB (`MAX_UPLOAD_BYTES`).
- Dosya türü uzantı ve gerçek içerikle doğrulanır.
- Storage yolu kullanıcı dosya adından üretilmez.
- Bütün sorgular JWT `company_id` claim'i ile filtrelenir; doğrulama için Auth Service ile aynı `SECRET_KEY` kullanılır.
- Upload/retry/delete yalnız `admin` rolüne açıktır.
- Ingestion çağrıları `X-Internal-API-Key` ile korunur.

## Test

```bash
pip install -r requirements-dev.txt
PYTHONPATH=. python -m unittest discover -s tests -v
```
