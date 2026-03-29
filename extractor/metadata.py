"""
Truth Engine — Estrazione metadati con BeautifulSoup.
Parsing chirurgico di meta tags, OpenGraph, schema.org.
"""
from __future__ import annotations

from bs4 import BeautifulSoup
from rich.console import Console

from models import ArticleMetadata

console = Console(legacy_windows=False)


def extract_metadata(html: str) -> ArticleMetadata:
    """
    Estrae metadati da HTML con BeautifulSoup.
    
    Cerca in ordine di priorità:
    - OpenGraph meta tags (og:title, og:description, etc.)
    - Standard meta tags (author, description)
    - HTML tags (title, h1, time)
    - Schema.org / JSON-LD
    
    Returns:
        ArticleMetadata popolato con i campi trovati.
    """
    if not html:
        return ArticleMetadata()

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return ArticleMetadata()

    title = _extract_title(soup)
    author = _extract_author(soup)
    published_date = _extract_date(soup)
    description = _extract_description(soup)
    site_name = _extract_site_name(soup)
    canonical_url = _extract_canonical(soup)

    return ArticleMetadata(
        title=title,
        author=author,
        published_date=published_date,
        description=description,
        site_name=site_name,
        canonical_url=canonical_url,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    """Estrai titolo: og:title > twitter:title > <title> > <h1>"""

    # OpenGraph
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    # Twitter Card
    tw_title = soup.find("meta", attrs={"name": "twitter:title"})
    if tw_title and tw_title.get("content"):
        return tw_title["content"].strip()

    # <title> tag
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.strip()

    # <h1> fallback
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return ""


def _extract_author(soup: BeautifulSoup) -> str:
    """Estrai autore: meta author > schema.org > byline class"""

    # Meta author
    meta_author = soup.find("meta", attrs={"name": "author"})
    if meta_author and meta_author.get("content"):
        return meta_author["content"].strip()

    # article:author (OpenGraph)
    og_author = soup.find("meta", property="article:author")
    if og_author and og_author.get("content"):
        return og_author["content"].strip()

    # Cerca JSON-LD per author
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                author = data.get("author")
                if isinstance(author, dict):
                    return author.get("name", "")
                elif isinstance(author, str):
                    return author
                elif isinstance(author, list) and len(author) > 0:
                    first = author[0]
                    if isinstance(first, dict):
                        return first.get("name", "")
                    return str(first)
        except Exception:
            continue

    # Byline class fallback
    byline = soup.find(class_=lambda c: c and "byline" in " ".join(c).lower())
    if byline:
        return byline.get_text(strip=True)

    return ""


def _extract_date(soup: BeautifulSoup) -> str:
    """Estrai data pubblicazione: article:published_time > <time> > schema.org"""

    # OpenGraph article:published_time
    og_date = soup.find("meta", property="article:published_time")
    if og_date and og_date.get("content"):
        return og_date["content"].strip()

    # <time> tag con datetime
    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        return time_tag["datetime"].strip()

    # Meta date
    meta_date = soup.find("meta", attrs={"name": "date"})
    if meta_date and meta_date.get("content"):
        return meta_date["content"].strip()

    # JSON-LD datePublished
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                dp = data.get("datePublished", "")
                if dp:
                    return str(dp)
        except Exception:
            continue

    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """Estrai descrizione: og:description > meta description"""

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()

    return ""


def _extract_site_name(soup: BeautifulSoup) -> str:
    """Estrai nome sito: og:site_name > application-name"""

    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        return og_site["content"].strip()

    app_name = soup.find("meta", attrs={"name": "application-name"})
    if app_name and app_name.get("content"):
        return app_name["content"].strip()

    return ""


def _extract_canonical(soup: BeautifulSoup) -> str:
    """Estrai URL canonico: <link rel='canonical'>"""

    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        return canonical["href"].strip()

    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        return og_url["content"].strip()

    return ""
