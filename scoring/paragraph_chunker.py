"""
Chunking per paragrafi con merge/split su dimensioni anomale.
"""
from __future__ import annotations

import re


def _split_large_paragraph(paragraph: str, max_chunk_size: int) -> list[str]:
    """Splitta un paragrafo molto lungo in blocchi a dimensione controllata."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if not current:
            current = sentence
            continue

        candidate = f"{current} {sentence}"
        if len(candidate) <= max_chunk_size:
            current = candidate
        else:
            chunks.append(current)
            # Se anche la singola frase supera il limite, spezza per caratteri.
            if len(sentence) > max_chunk_size:
                for i in range(0, len(sentence), max_chunk_size):
                    part = sentence[i:i + max_chunk_size].strip()
                    if part:
                        chunks.append(part)
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_by_paragraphs(
    text: str,
    min_chunk_size: int = 150,
    max_chunk_size: int = 800,
) -> list[str]:
    """
    Divide il testo per paragrafi e riequilibra chunk troppo piccoli/grandi.

    Regole:
    - split iniziale su paragrafi vuoti;
    - paragrafi piccoli: merge nel chunk corrente;
    - paragrafi grandi: split su frasi mantenendo max_chunk_size;
    - filtro finale su chunk vuoti.
    """
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_large_paragraph(paragraph, max_chunk_size))
            continue

        if not current:
            current = paragraph
            continue

        # Mantieni blocchi con una dimensione minima unendo paragrafi adiacenti.
        if len(current) < min_chunk_size:
            current = f"{current}\n\n{paragraph}"
            continue

        candidate = f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    # Post-pass: unisci eventuale ultimo chunk troppo corto al precedente.
    if len(chunks) > 1 and len(chunks[-1]) < min_chunk_size:
        chunks[-2] = f"{chunks[-2]}\n\n{chunks[-1]}".strip()
        chunks.pop()

    return [c for c in chunks if c]
