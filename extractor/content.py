"""
Truth Engine — Estrazione contenuto articolo con trafilatura.
Rimuove nav, ads, footer. Estrae solo il corpo principale.
"""
from __future__ import annotations

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

    try:
        from trafilatura import extract

        text = extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,  # Usa fallback se estrazione primaria fallisce
            favor_precision=True,  # Preferisci precisione a recall
        )

        if text and len(text.strip()) > 50:
            return text.strip()

        return ""

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

        result = bare_extraction(html, include_comments=False, include_tables=True)

        if result is None:
            return {}

        return {
            "text": getattr(result, "text", "") or "",
            "title": getattr(result, "title", "") or "",
            "author": getattr(result, "author", "") or "",
            "date": getattr(result, "date", "") or "",
            "sitename": getattr(result, "sitename", "") or "",
            "description": getattr(result, "description", "") or "",
        }

    except Exception as e:
        console.print(f"    [red][ERRORE][/red] bare_extraction errore: {str(e)[:100]}")
        return {}
