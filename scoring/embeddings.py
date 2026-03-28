"""
Sentence Transformers + cosine similarity per claim/chunk matching.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config import EMBEDDING_MODEL_NAME

_model: Optional[SentenceTransformer] = None


def get_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    """Lazy-load singleton del modello embeddings."""
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def embed_texts(texts: list[str], model_name: str = EMBEDDING_MODEL_NAME) -> np.ndarray:
    """Ritorna embeddings [n_texts, dim] per la lista fornita."""
    if not texts:
        return np.array([], dtype=float)

    model = get_embedding_model(model_name)
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(embeddings, dtype=float)


def compute_similarity(claim_embedding: np.ndarray, chunk_embeddings: np.ndarray) -> np.ndarray:
    """Calcola cosine similarity claim vs ogni chunk."""
    if claim_embedding.size == 0 or chunk_embeddings.size == 0:
        return np.array([], dtype=float)

    similarities = cosine_similarity(claim_embedding.reshape(1, -1), chunk_embeddings)
    return similarities[0]


def get_top_k_indices(similarities: np.ndarray, top_k: int, min_threshold: float) -> list[int]:
    """Indici top-k ordinati per score decrescente e filtrati per soglia minima."""
    if similarities.size == 0 or top_k <= 0:
        return []

    candidate_indices = [
        index for index, score in enumerate(similarities.tolist())
        if score >= min_threshold
    ]
    candidate_indices.sort(key=lambda idx: similarities[idx], reverse=True)
    return candidate_indices[:top_k]
