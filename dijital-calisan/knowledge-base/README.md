# OfficeIQ bilgi tabanı

Bu dizin, yerel RAG kaynak dokümanları için ayrılmıştır. Ham kurumsal belgeler
gizlilik, KVKK ve depo boyutu nedenleriyle Git tarafından izlenmez.

Beklenen yapı:

```text
knowledge-base/
  Finans/
    FIN-PR-001 Masraf Yönetimi.docx
  İnsan Kaynakları/
    Personel El Kitabı.docx
```

Üst seviye klasör adı OfficeIQ kategorisine dönüştürülür. Belgeleri çalışan
sisteme aktarmak için:

```bash
python tools/import_knowledge_base.py knowledge-base \
  --base-url http://localhost:8080 \
  --company-slug sirket-kodu \
  --email admin@example.com
```

Parola komut satırında tutulmaz; araç güvenli biçimde terminalden ister.
Drive, S3 veya başka bir kurumsal depolama kaynağı kalıcı kaynak olmalı; bu
dizin yalnızca yerel ve geçici çalışma kopyasıdır.

Araç bağımlılıklarını kurmak için:

```bash
python -m pip install -r tools/requirements.txt
```
