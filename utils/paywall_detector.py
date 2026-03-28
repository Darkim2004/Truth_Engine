"""
Truth Engine — Paywall detection euristica.
Rileva se una pagina è dietro paywall e va skippata.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

from config import PAYWALL_KEYWORDS, PAYWALL_MIN_CONTENT_LENGTH


def is_paywall(html: str) -> bool:
    """
    Rileva se una pagina HTML è dietro paywall.
    
    Euristiche:
    1. Cerca keyword paywall nel testo visibile
    2. Controlla se il corpo ha pochissimo testo (< 300 char)
    3. Controlla meta tags / classi CSS tipiche di paywall
    
    Returns:
        True se paywall rilevato.
    """
    if not html:
        return False

    html_lower = html.lower()

    # 1. Keyword check nel raw HTML
    keyword_count = sum(1 for kw in PAYWALL_KEYWORDS if kw in html_lower)
    if keyword_count >= 2:
        return True

    # 2. Parsing con BeautifulSoup per check più precisi
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return False

    # Controlla classi CSS tipiche di paywall
    paywall_selectors = [
        {"class_": lambda c: c and "paywall" in " ".join(c).lower()},
        {"class_": lambda c: c and "subscriber" in " ".join(c).lower()},
        {"class_": lambda c: c and "premium-content" in " ".join(c).lower()},
        {"id": lambda i: i and "paywall" in i.lower()},
    ]

    for selector in paywall_selectors:
        if soup.find(attrs=selector):
            return True

    # 3. Check se il body ha poco testo visibile
    body = soup.find("body")
    if body:
        # Rimuovi script e style
        for tag in body.find_all(["script", "style", "noscript"]):
            tag.decompose()

        visible_text = body.get_text(separator=" ", strip=True)
        if len(visible_text) < PAYWALL_MIN_CONTENT_LENGTH:
            return True

    return False
