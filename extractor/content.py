"""
Truth Engine — Estrazione contenuto articolo con trafilatura.
Rimuove nav, ads, footer. Estrae solo il corpo principale.
"""
from __future__ import annotations

import re

from rich.console import Console

console = Console()


def _clean_text(text: str) -> str:
    """Normalizza il testo estratto rimuovendo whitespace rumoroso."""
    if not text:
        return ""

    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def _is_valid_text(text: str, min_length: int = 80) -> bool:
    """Heuristica minima per considerare valido il testo estratto."""
    if not text:
        return False
    return len(text.strip()) >= min_length


def _extract_with_bs4_fallback(html: str) -> str:
    """Fallback leggero: prova article/main e paragrafi visibili."""
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return ""

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return ""

    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return ""

    for tag in root.find_all(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "aside"]):
        tag.decompose()

    paragraphs = [p.get_text(" ", strip=True) for p in root.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) >= 40]

    if paragraphs:
        return _clean_text("\n\n".join(paragraphs))

    return _clean_text(root.get_text(" ", strip=True))


def _get_structured_field(result: object, key: str) -> str:
    """Legge un campo da bare_extraction sia dict che oggetto."""
    if result is None:
        return ""

    if isinstance(result, dict):
        value = result.get(key, "")
        return str(value or "")

    value = getattr(result, key, "")
    return str(value or "")


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
        console.print(f"    [yellow]⚠[/yellow] trafilatura errore: {str(e)[:100]}")

    # 3) Tentativo structured extraction
    structured = extract_article_structured(html)
    structured_text = _clean_text(structured.get("text", ""))
    if _is_valid_text(structured_text):
        return structured_text

    # 4) Ultimo fallback manuale
    bs4_text = _extract_with_bs4_fallback(html)
    if _is_valid_text(bs4_text):
        return bs4_text

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
        console.print(f"    [red]✗[/red] bare_extraction errore: {str(e)[:100]}")
        return {}
