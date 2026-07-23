from __future__ import annotations

from app.services.chunking_service import Tokenizer, chunk_document
from app.services.parser_service import ParsedBlock, ParsedDocument


def _document(text: str, page: int | None = 1, section: str | None = "Politika") -> ParsedDocument:
    block = ParsedBlock(
        text=text,
        block_index=0,
        page_number=page,
        section_title=section,
        char_start=0,
        char_end=len(text),
    )
    return ParsedDocument(blocks=[block], page_count=page, language="tr", character_count=len(text))


def test_turkish_text_uses_model_tokenizer_exactly():
    tokenizer = Tokenizer()
    text = "Çalışanların yıllık izin talepleri yönetici onayına gönderilir."
    chunks = chunk_document(_document(text), tokenizer=tokenizer, chunk_size_tokens=50, overlap_tokens=10)
    assert chunks[0].token_count == len(tokenizer.encode(chunks[0].content))


def test_chunks_never_exceed_token_budget_and_are_deterministic():
    tokenizer = Tokenizer()
    text = " ".join(
        f"Çalışan {index} için yıllık izin prosedürü yönetici tarafından onaylanır."
        for index in range(80)
    )
    first = chunk_document(_document(text), tokenizer=tokenizer, chunk_size_tokens=100, overlap_tokens=20)
    second = chunk_document(_document(text), tokenizer=tokenizer, chunk_size_tokens=100, overlap_tokens=20)
    assert len(first) > 2
    assert all(chunk.token_count <= 100 for chunk in first)
    assert [(chunk.content, chunk.content_hash) for chunk in first] == [
        (chunk.content, chunk.content_hash) for chunk in second
    ]


def test_overlap_repeats_semantic_tail():
    tokenizer = Tokenizer()
    sentences = [f"Bu işlem adımı {index} çalışan tarafından uygulanır." for index in range(30)]
    chunks = chunk_document(_document(" ".join(sentences)), tokenizer=tokenizer, chunk_size_tokens=70, overlap_tokens=20)
    assert len(chunks) > 1
    first_sentences = set(chunks[0].content.split("\n\n"))
    second_sentences = set(chunks[1].content.split("\n\n"))
    assert first_sentences & second_sentences


def test_page_and_section_metadata_are_preserved():
    tokenizer = Tokenizer()
    first = ParsedBlock("Birinci sayfa prosedür açıklaması yeterince uzundur.", 0, 1, "İzin", 0, 52)
    second = ParsedBlock("İkinci sayfa onay açıklaması yeterince uzundur.", 1, 2, "İzin", 54, 103)
    document = ParsedDocument([first, second], 2, "tr", 101)
    chunks = chunk_document(document, tokenizer=tokenizer, chunk_size_tokens=100, overlap_tokens=10)
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].section_title == "İzin"
    assert chunks[0].char_start == 0


def test_pathological_long_sentence_falls_back_to_token_windows():
    tokenizer = Tokenizer()
    text = "çokuzunifade " * 500
    chunks = chunk_document(_document(text), tokenizer=tokenizer, chunk_size_tokens=64, overlap_tokens=8)
    assert len(chunks) > 2
    assert all(chunk.token_count <= 64 for chunk in chunks)
