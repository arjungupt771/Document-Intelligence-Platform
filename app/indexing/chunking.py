from __future__ import annotations

from dataclasses import dataclass

from app.indexing.config import ChunkingSettings
from app.parsing.models import ParsedDocument


@dataclass(frozen=True)
class Chunk:
    chunk_index: int
    text: str
    page_number: int | None


def chunk_document(
    document: ParsedDocument,
    settings: ChunkingSettings = ChunkingSettings(),
) -> list[Chunk]:
    """
    Splits a parsed document into overlapping, page-aware chunks.

    Chunking happens per page first, so a chunk never silently mixes text
    from two different pages (page_number stays a reliable citation). A
    sliding window over words is then applied within each page's text so
    long pages still split into multiple, reasonably-sized chunks with
    `chunk_overlap` words of context carried into the next chunk.
    """
    chunks: list[Chunk] = []
    chunk_index = 0

    for page in document.pages:
        words = page.text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + settings.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            chunks.append(Chunk(chunk_index=chunk_index, text=chunk_text, page_number=page.page_number))
            chunk_index += 1

            if end == len(words):
                break
            start = end - settings.chunk_overlap

    return chunks
