"""
Validazione evidenze tramite chunking + similarita' semantica.
"""
from __future__ import annotations

from config import (
    CHUNK_MIN_SIZE,
    CHUNK_MAX_SIZE,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MIN_THRESHOLD,
    EMBEDDING_TOP_K,
)
from scoring.paragraph_chunker import chunk_by_paragraphs
from scoring.embeddings import embed_texts, compute_similarity, get_top_k_indices


def validate_evidence(
    url: str,
    text: str,
    claim: str,
    min_threshold: float = EMBEDDING_MIN_THRESHOLD,
    top_k: int = EMBEDDING_TOP_K,
    model_name: str = EMBEDDING_MODEL_NAME,
    min_chunk_size: int = CHUNK_MIN_SIZE,
    max_chunk_size: int = CHUNK_MAX_SIZE,
) -> dict:
    """
    Analizza una fonte rispetto al claim.

    Output pensato per il frontend e per i test:
    - include input originali (url, text, claim)
    - include chunk + score + top chunks filtrati per soglia
    """
    source_text = (text or "").strip()
    claim_text = (claim or "").strip()

    if not source_text or not claim_text:
        return {
            "url": url,
            "original_text": source_text,
            "claim": claim_text,
            "chunks": [],
            "chunk_similarity_scores": [],
            "top_chunk_indices": [],
            "matches": [],
            "max_similarity": 0.0,
            "supports_claim": False,
            "threshold": float(min_threshold),
        }

    chunks = chunk_by_paragraphs(
        source_text,
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
    )

    if not chunks:
        return {
            "url": url,
            "original_text": source_text,
            "claim": claim_text,
            "chunks": [],
            "chunk_similarity_scores": [],
            "top_chunk_indices": [],
            "matches": [],
            "max_similarity": 0.0,
            "supports_claim": False,
            "threshold": float(min_threshold),
        }

    claim_embedding = embed_texts([claim_text], model_name=model_name)
    chunk_embeddings = embed_texts(chunks, model_name=model_name)
    similarities = compute_similarity(claim_embedding[0], chunk_embeddings)

    top_indices = get_top_k_indices(
        similarities,
        top_k=top_k,
        min_threshold=min_threshold,
    )

    scores = [float(s) for s in similarities.tolist()]
    matches = [
        {
            "url": url,
            "chunk_index": index,
            "chunk_text": chunks[index],
            "similarity_score": scores[index],
        }
        for index in top_indices
    ]

    max_similarity = max(scores) if scores else 0.0

    return {
        "url": url,
        "original_text": source_text,
        "claim": claim_text,
        "chunks": chunks,
        "chunk_similarity_scores": scores,
        "top_chunk_indices": top_indices,
        "matches": matches,
        "max_similarity": float(max_similarity),
        "supports_claim": float(max_similarity) >= float(min_threshold),
        "threshold": float(min_threshold),
    }


def processa_tutte_le_fonti(
    claim: str,
    lista_risultati_ricerca: list[dict],
    min_threshold: float = EMBEDDING_MIN_THRESHOLD,
    top_k: int = EMBEDDING_TOP_K,
) -> list[dict]:
    """
    API esterna: analizza tutte le fonti ricevute dal frontend.

    Ogni elemento in lista_risultati_ricerca deve avere almeno:
    - url
    - text (oppure article_text)
    """
    report_finale: list[dict] = []

    for fonte in lista_risultati_ricerca:
        url = fonte.get("url", "")
        text = fonte.get("text", fonte.get("article_text", ""))

        risultato = validate_evidence(
            url=url,
            text=text,
            claim=claim,
            min_threshold=min_threshold,
            top_k=top_k,
        )
        report_finale.append(
            {
                "url": url,
                "text": text,
                "analisi": risultato,
            }
        )

    return report_finale
