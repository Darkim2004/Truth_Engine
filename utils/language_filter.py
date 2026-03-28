"""
Truth Engine — Filtro lingua con langdetect.
Attivo solo se la lingua è specificata nel JSON di input.
"""
from __future__ import annotations

from langdetect import detect, LangDetectException
from rich.console import Console

console = Console()


def detect_language(text: str) -> str:
    """
    Rileva la lingua di un testo.
    
    Returns:
        Codice lingua ISO 639-1 (es: "it", "en"), o "" se non rilevabile.
    """
    if not text or len(text.strip()) < 50:
        return ""

    try:
        return detect(text)
    except LangDetectException:
        return ""


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

    detected = detect_language(text)
    if not detected:
        return True  # Non bloccare se non riesce a rilevare

    # Normalizza per confronto
    expected = expected_language.lower().strip()[:2]
    detected = detected.lower().strip()[:2]

    return expected == detected
