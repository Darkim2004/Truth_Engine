"""
Truth Engine — Normalizzazione URL per deduplicazione.
Rimuove tracking params, normalizza schema/host, ordina query params.
Zero dipendenze extra (usa solo urllib.parse).
"""
from __future__ import annotations

from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

from config import TRACKING_PARAMS


def normalize_url(url: str) -> str:
    """
    Normalizza un URL per deduplicazione.
    
    Operazioni:
    1. Lowercase schema e host
    2. Rimuovi www. prefix
    3. Rimuovi fragment (#section)
    4. Rimuovi trailing slash
    5. Rimuovi tracking params (utm_*, fbclid, etc.)
    6. Ordina query params rimanenti
    
    Returns:
        URL normalizzato, o stringa vuota se URL invalido.
    """
    if not url or not url.strip():
        return ""

    url = url.strip()

    # Aggiungi schema se mancante
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return ""

    # 1. Lowercase schema e host
    scheme = parsed.scheme.lower()
    host = parsed.hostname or ""
    host = host.lower()

    # 2. Rimuovi www. prefix
    if host.startswith("www."):
        host = host[4:]

    if not host:
        return ""

    # 3. Rimuovi fragment
    # (non usiamo parsed.fragment)

    # 4. Path: rimuovi trailing slash (ma mantieni "/" root)
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if not path:
        path = "/"

    # 5. Filtra tracking params
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    filtered_params = {
        k: v for k, v in query_params.items()
        if k.lower() not in TRACKING_PARAMS
    }

    # 6. Ordina params rimanenti
    sorted_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

    # Ricostruisci URL
    # Gestisci porta (ometti se default)
    port = parsed.port
    if port and port not in (80, 443):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    normalized = urlunparse((scheme, netloc, path, "", sorted_query, ""))

    return normalized


def urls_are_same(url1: str, url2: str) -> bool:
    """Controlla se due URL puntano alla stessa risorsa dopo normalizzazione."""
    return normalize_url(url1) == normalize_url(url2)
