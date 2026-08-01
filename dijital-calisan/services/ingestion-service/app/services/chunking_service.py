from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import tiktoken

from app.config import CHUNK_OVERLAP_TOKENS, CHUNK_SIZE_TOKENS, TOKENIZER_MODEL
from app.services.parser_service import ParsedBlock, ParsedDocument


@dataclass(frozen=True)
class ChunkData:
    chunk_index: int
    content: str
    content_hash: str
    token_count: int
    page_start: int | None
    page_end: int | None
    section_title: str | None
    char_start: int | None
    char_end: int | None


@dataclass(frozen=True)
class _Unit:
    text: str
    tokens: tuple[int, ...]
    page_number: int | None
    section_title: str | None
    char_start: int
    char_end: int


class Tokenizer:
    def __init__(self, model: str = TOKENIZER_MODEL):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        return self.encoding.encode(text, disallowed_special=())

    def decode(self, tokens: list[int] | tuple[int, ...]) -> str:
        return self.encoding.decode(list(tokens))

    def count(self, text: str) -> int:
        return len(self.encode(text))


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    paragraph_pattern = re.compile(r"[^\n]+")
    sentence_pattern = re.compile(r".+?(?:[.!?…]+(?=\s|$)|$)", re.DOTALL)
    for paragraph in paragraph_pattern.finditer(text):
        paragraph_text = paragraph.group()
        matches = list(sentence_pattern.finditer(paragraph_text))
        if not matches:
            spans.append((paragraph.start(), paragraph.end()))
            continue
        for match in matches:
            start = paragraph.start() + match.start()
            end = paragraph.start() + match.end()
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if start < end:
                spans.append((start, end))
    return spans


def _units_for_block(block: ParsedBlock, tokenizer: Tokenizer, max_tokens: int) -> list[_Unit]:
    units: list[_Unit] = []
    for start, end in _sentence_spans(block.text):
        sentence = block.text[start:end]
        tokens = tokenizer.encode(sentence)
        if len(tokens) <= max_tokens:
            units.append(_Unit(sentence, tuple(tokens), block.page_number, block.section_title, block.char_start + start, block.char_start + end))
            continue
        # Pathological single sentences are split at the largest character
        # boundary that still fits the exact model token budget.
        segment_start = 0
        while segment_start < len(sentence):
            low, high = segment_start + 1, len(sentence)
            best_end = low
            while low <= high:
                middle = (low + high) // 2
                if tokenizer.count(sentence[segment_start:middle]) <= max_tokens:
                    best_end = middle
                    low = middle + 1
                else:
                    high = middle - 1
            if best_end < len(sentence):
                whitespace = sentence.rfind(" ", segment_start, best_end)
                if whitespace > segment_start + max(1, (best_end - segment_start) // 2):
                    best_end = whitespace
            text_slice = sentence[segment_start:best_end].strip()
            if text_slice:
                slice_tokens = tokenizer.encode(text_slice)
                units.append(
                    _Unit(
                        text_slice,
                        tuple(slice_tokens),
                        block.page_number,
                        block.section_title,
                        block.char_start + start + segment_start,
                        block.char_start + start + best_end,
                    )
                )
            segment_start = best_end
            while segment_start < len(sentence) and sentence[segment_start].isspace():
                segment_start += 1
    return units


def _render(units: list[_Unit]) -> str:
    return "\n\n".join(unit.text.strip() for unit in units if unit.text.strip()).strip()


def _suffix_overlap(units: list[_Unit], tokenizer: Tokenizer, overlap_tokens: int) -> list[_Unit]:
    if overlap_tokens <= 0:
        return []
    selected: list[_Unit] = []
    for unit in reversed(units):
        candidate = [unit, *selected]
        if tokenizer.count(_render(candidate)) > overlap_tokens:
            break
        selected = candidate
    if selected:
        return selected

    # Keep the largest valid character suffix when the final semantic unit alone
    # exceeds overlap. Character boundaries avoid replacement characters that
    # can appear when a BPE token byte sequence is decoded in isolation.
    last = units[-1]
    low, high = 0, len(last.text) - 1
    best_start = len(last.text)
    while low <= high:
        middle = (low + high) // 2
        if tokenizer.count(last.text[middle:]) <= overlap_tokens:
            best_start = middle
            high = middle - 1
        else:
            low = middle + 1
    whitespace = last.text.find(" ", best_start)
    if whitespace != -1 and whitespace < best_start + max(1, (len(last.text) - best_start) // 3):
        best_start = whitespace + 1
    tail_text = last.text[best_start:].strip()
    tail = tokenizer.encode(tail_text)
    return [
        _Unit(
            text=tail_text,
            tokens=tuple(tail),
            page_number=last.page_number,
            section_title=last.section_title,
            char_start=max(last.char_start, last.char_end - len(last.text) + best_start),
            char_end=last.char_end,
        )
    ] if tail_text else []


def _to_chunk(index: int, units: list[_Unit], tokenizer: Tokenizer) -> ChunkData:
    content = _render(units)
    pages = [unit.page_number for unit in units if unit.page_number is not None]
    sections = {unit.section_title for unit in units if unit.section_title}
    return ChunkData(
        chunk_index=index,
        content=content,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        token_count=tokenizer.count(content),
        page_start=min(pages) if pages else None,
        page_end=max(pages) if pages else None,
        section_title=next(iter(sections)) if len(sections) == 1 else None,
        char_start=min((unit.char_start for unit in units), default=None),
        char_end=max((unit.char_end for unit in units), default=None),
    )


def chunk_document(
    document: ParsedDocument,
    *,
    tokenizer: Tokenizer | None = None,
    chunk_size_tokens: int = CHUNK_SIZE_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[ChunkData]:
    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= chunk_size_tokens:
        raise ValueError("overlap_tokens must be between 0 and chunk_size_tokens")

    tokenizer = tokenizer or Tokenizer()
    units = [
        unit
        for block in document.blocks
        for unit in _units_for_block(block, tokenizer, chunk_size_tokens)
    ]
    if not units:
        return []

    chunks: list[ChunkData] = []
    current: list[_Unit] = []
    for unit in units:
        candidate = [*current, unit]
        if current and tokenizer.count(_render(candidate)) > chunk_size_tokens:
            chunks.append(_to_chunk(len(chunks), current, tokenizer))
            current = _suffix_overlap(current, tokenizer, overlap_tokens)
            candidate = [*current, unit]
            while current and tokenizer.count(_render(candidate)) > chunk_size_tokens:
                current = current[1:]
                candidate = [*current, unit]
        current = candidate

    if current:
        final = _to_chunk(len(chunks), current, tokenizer)
        if not chunks or final.content_hash != chunks[-1].content_hash:
            chunks.append(final)

    if any(chunk.token_count > chunk_size_tokens for chunk in chunks):
        raise RuntimeError("chunk token budget exceeded")
    return chunks
