# OfficeIQ / Dijital Çalışan

## Başlatma

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Gateway: http://localhost:8080
PostgreSQL: `localhost:5433` (`officeiq` veritabanı ve kullanıcısı)

Migration'lar servislerden önce otomatik olarak `alembic upgrade head` komutuyla
çalışır. Migration başarısız olursa uygulama servisleri başlatılmaz.

## Doğrulama

```bash
docker compose exec postgres psql -U officeiq -d officeiq -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'citext', 'uuid-ossp');"
docker compose exec postgres psql -U officeiq -d officeiq -c "SELECT version_num FROM alembic_version;"
docker compose exec postgres psql -U officeiq -d officeiq -c "\\d+ document_chunks"
curl --fail http://localhost:8080/health
```
