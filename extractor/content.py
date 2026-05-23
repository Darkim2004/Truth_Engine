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
