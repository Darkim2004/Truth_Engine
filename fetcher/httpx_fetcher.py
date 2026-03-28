"""
Truth Engine — Fetch HTML con httpx (asincrono).
Prima scelta per scaricare pagine. Veloce e leggero.
Retry su errori transitori con backoff esponenziale.
"""
from __future__ import annotations

import asyncio
import random

import httpx
from rich.console import Console

from config import HTTP_TIMEOUT, HTTP_MAX_RETRIES, HTTP_BACKOFF_FACTOR, DEFAULT_HEADERS
from models import FetchedPage

console = Console()

# Status code da ritentare
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Status code da skippare subito
SKIP_STATUS = {401, 403, 404, 410, 451}


async def fetch_with_httpx(url: str) -> FetchedPage:
    """
    Scarica una pagina con httpx.
    
    - Retry su 429/5xx con backoff esponenziale
    - Skip immediato su 403/404 
    - Timeout 15s
    
    Returns:
        FetchedPage con html e metadati.
    """
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                response = await client.get(url)

                # Skip immediato su errori permanenti
                if response.status_code in SKIP_STATUS:
                    return FetchedPage(
                        url=url,
                        status_code=response.status_code,
                        fetch_method="httpx",
                        is_valid=False,
                        error=f"HTTP {response.status_code}",
                    )

                # Retry su errori transitori
                if response.status_code in RETRYABLE_STATUS:
                    if attempt < HTTP_MAX_RETRIES:
                        sleep_time = HTTP_BACKOFF_FACTOR ** attempt + random.uniform(0, 1)
                        console.print(
                            f"    [yellow]↻[/yellow] httpx {response.status_code} per {url[:60]}... "
                            f"retry in {sleep_time:.1f}s"
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                    else:
                        return FetchedPage(
                            url=url,
                            status_code=response.status_code,
                            fetch_method="httpx",
                            is_valid=False,
                            error=f"HTTP {response.status_code} dopo {HTTP_MAX_RETRIES} tentativi",
                        )

                # Successo
                if response.status_code == 200:
                    html = response.text
                    # Check che sia effettivamente HTML
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "application/xhtml" not in content_type:
                        return FetchedPage(
                            url=url,
                            status_code=response.status_code,
                            fetch_method="httpx",
                            is_valid=False,
                            error=f"Content-Type non HTML: {content_type[:50]}",
                        )

                    return FetchedPage(
                        url=url,
                        html=html,
                        status_code=response.status_code,
                        fetch_method="httpx",
                        is_valid=True,
                    )

                # Altro status code non gestito
                return FetchedPage(
                    url=url,
                    status_code=response.status_code,
                    fetch_method="httpx",
                    is_valid=False,
                    error=f"HTTP {response.status_code} non gestito",
                )

        except httpx.TimeoutException:
            if attempt < HTTP_MAX_RETRIES:
                sleep_time = HTTP_BACKOFF_FACTOR ** attempt
                await asyncio.sleep(sleep_time)
                continue
            return FetchedPage(
                url=url,
                fetch_method="httpx",
                is_valid=False,
                error="Timeout",
            )

        except httpx.ConnectError as e:
            return FetchedPage(
                url=url,
                fetch_method="httpx",
                is_valid=False,
                error=f"Connessione fallita: {str(e)[:100]}",
            )

        except Exception as e:
            return FetchedPage(
                url=url,
                fetch_method="httpx",
                is_valid=False,
                error=f"Errore: {str(e)[:100]}",
            )

    # Fallback (non dovrebbe arrivarci)
    return FetchedPage(
        url=url,
        fetch_method="httpx",
        is_valid=False,
        error="Max retry raggiunto",
    )
