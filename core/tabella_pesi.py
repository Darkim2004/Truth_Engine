from __future__ import annotations

from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Transform 'https://www.ansa.it/news/123' into 'ansa.it'."""
    try:
        value = (url or "").strip()
        if not value:
            return ""

        if "://" not in value:
            value = "https://" + value

        domain = urlparse(value).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def get_credibility_score(domain: str) -> float:
    """
    Estimate baseline source credibility from the domain.

    Scores are deliberately simple and explainable: institutions and primary
    science sources rank highest, major news organizations rank high, low-trust
    markers rank low, and unknown sources remain neutral.
    """
    clean_domain = extract_domain(domain) if "/" in (domain or "") else (domain or "")
    clean_domain = clean_domain.lower()

    if not clean_domain:
        return 0.0

    institutional_domains = [
        ".gov",
        ".gov.it",
        "who.int",
        "cdc.gov",
        "nih.gov",
        "europa.eu",
        "istat.it",
        "iss.it",
        "salute.gov.it",
        "wikipedia.",
    ]
    if clean_domain.endswith(".gov") or any(d in clean_domain for d in institutional_domains):
        return 1.0

    high_trust_domains = [
        "ansa.it",
        "reuters.com",
        "apnews.com",
        "bbc.co.uk",
        "nature.com",
        "science.org",
        "nejm.org",
        "thelancet.com",
        "jamanetwork.com",
    ]
    if any(d in clean_domain for d in high_trust_domains):
        return 0.9

    major_news_domains = [
        "corriere.it",
        "repubblica.it",
        "ilsole24ore.com",
        "lastampa.it",
        "ilgiornale.it",
        "liberoquotidiano.it",
        "nytimes.com",
        "theguardian.com",
    ]
    if any(d in clean_domain for d in major_news_domains):
        return 0.8

    low_trust_markers = [
        "bufale",
        "verita-nascoste",
        "complotti",
        "fake-news",
        "blogspot",
    ]
    if any(marker in clean_domain for marker in low_trust_markers):
        return 0.2

    if "blog" in clean_domain:
        return 0.3

    return 0.5
