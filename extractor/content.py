"""
Truth Engine — Estrazione contenuto articolo con trafilatura.
Rimuove nav, ads, footer. Estrae solo il corpo principale.
"""
from __future__ import annotations

import re

from rich.console import Console

console = Console(legacy_windows=False)


def extract_article_text(html: str) -> str:
    """
    Estrae il corpo principale di un articolo da HTML.
    Usa trafilatura per rimuovere nav, ads, footer e ottenere solo il testo utile.
    
    Args:
        html: HTML della pagina.
        
    Returns:
        Testo dell'articolo, o stringa vuota se estrazione fallisce.
    """
    if not html:
        return ""

    # 1) Tentativo alta precisione
    try:
        from trafilatura import extract

        text_precise = extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
        )
        text_precise = _clean_text(text_precise or "")
        if _is_valid_text(text_precise):
            return text_precise

        # 2) Tentativo alta recall (meno severo)
        text_recall = extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
        )
        text_recall = _clean_text(text_recall or "")
        if _is_valid_text(text_recall):
            return text_recall

    except Exception as e:
        console.print(f"    [red][ERRORE][/red] trafilatura errore: {str(e)[:100]}")
        return ""


def extract_article_structured(html: str) -> dict:
    """
    Estrazione strutturata con bare_extraction().
    Ritorna dict con text, title, author, date, etc.
    
    Returns:
        Dict con campi estratti, o dict vuoto se fallisce.
    """
    if not html:
        return {}

    try:
        from trafilatura import bare_extraction

        result = bare_extraction(
            html,
            include_comments=False,
            include_tables=True,
            favor_precision=False,
        )

        if result is None:
            return {}

        return {
            "text": _clean_text(_get_structured_field(result, "text")),
            "title": _get_structured_field(result, "title"),
            "author": _get_structured_field(result, "author"),
            "date": _get_structured_field(result, "date"),
            "sitename": _get_structured_field(result, "sitename"),
            "description": _get_structured_field(result, "description"),
        }

    except Exception as e:
        console.print(f"    [red][ERRORE][/red] bare_extraction errore: {str(e)[:100]}")
        return {}
