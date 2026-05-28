"""
Chunker service — splits raw text into ~300-word chunks with 50-word overlap.

Strategy rationale (from CONTEXT.md):
  Company About Us pages are typically 200–800 words. 500-word chunks would
  produce only 1–2 segments with no meaningful retrieval differentiation.
  300-word chunks with 50-word overlap yields 3–5 retrievable segments,
  making the RAG pipeline genuinely useful.
"""

from typing import List


CHUNK_SIZE = 300    # words per chunk
OVERLAP = 50        # words shared between consecutive chunks


def chunk_text(text: str) -> List[str]:
    """
    Split *text* into overlapping word-window chunks.

    Returns a list of chunk strings. Each chunk is approximately
    CHUNK_SIZE words. Adjacent chunks share OVERLAP words at their
    boundary so that context is not lost at the seam.

    If the text is shorter than CHUNK_SIZE words the whole text is
    returned as a single chunk.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += CHUNK_SIZE - OVERLAP  # slide forward by (chunk_size - overlap)

    return chunks
