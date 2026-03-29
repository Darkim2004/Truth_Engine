"""
Truth Engine — Filtro lingua con langdetect.
Attivo solo se la lingua è specificata nel JSON di input.
"""
from __future__ import annotations

import re

from langdetect import detect, LangDetectException
from rich.console import Console

console = Console(legacy_windows=False)


def _normalize_for_language_detection(text: str) -> str:
    """Riduce rumore (URL, spazi, simboli) per migliorare il detector."""
    if not text:
        return ""

    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"www\.\S+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"[^\w\sÀ-ÖØ-öø-ÿ]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _build_language_samples(text: str) -> list[str]:
    """Costruisce finestre di testo per voting robusto."""
    if not text:
        return []

    words = text.split()
    if len(words) < 30:
        return [text]

    samples: list[str] = []
    first = " ".join(words[:150])
    middle_start = max(0, len(words) // 2 - 75)
    middle = " ".join(words[middle_start:middle_start + 150])
    last = " ".join(words[-150:])

    for sample in (first, middle, last):
        if len(sample) >= 120:
            samples.append(sample)

    if not samples:
        samples.append(" ".join(words[:200]))

    return samples


def detect_language(text: str) -> str:
    """
    Rileva la lingua di un testo.
    
    Returns:
        Codice lingua ISO 639-1 (es: "it", "en"), o "" se non rilevabile.
    """
    normalized = _normalize_for_language_detection(text)
    if not normalized or len(normalized) < 80:
        return ""

    samples = _build_language_samples(normalized)
    if not samples:
        return ""

    votes: dict[str, int] = {}

    for sample in samples:
        try:
            lang = detect(sample)
        except LangDetectException:
            continue

        lang = (lang or "").lower().strip()[:2]
        if not lang:
            continue
        votes[lang] = votes.get(lang, 0) + 1

    if not votes:
        return ""

    return max(votes.items(), key=lambda x: x[1])[0]


def is_correct_language(text: str, expected_language: str) -> bool:
    """
    Verifica se il testo è nella lingua attesa.
    
    Args:
        text: Testo da verificare.
        expected_language: Codice lingua atteso (es: "it", "en").
                          Se vuoto, ritorna sempre True (skip filtro).
    
    Returns:
        True se la lingua matcha o se il filtro è disabilitato.
    """
    if not expected_language:
        return True  # Skip filtro se lingua non specificata

    normalized = _normalize_for_language_detection(text)
    if len(normalized) < 120:
        # Testo troppo corto/rumoroso: evita falsi blocchi.
        return True

    detected = detect_language(normalized)
    if not detected:
        return True  # Non bloccare se non riesce a rilevare

    # Normalizza per confronto
    expected = expected_language.lower().strip()[:2]
    detected = detected.lower().strip()[:2]

    if expected == detected:
        return True

    # Fallback tollerante per confusioni frequenti su testi rumorosi.
    tolerant_pairs = {
        ("it", "es"),
        ("es", "it"),
        ("it", "pt"),
        ("pt", "it"),
    }
    if (expected, detected) in tolerant_pairs:
        return True

    return False
