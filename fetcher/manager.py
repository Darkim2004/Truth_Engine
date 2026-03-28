"""
Truth Engine — Fetch manager.
Orchestratore: prova httpx, se fallisce usa Playwright come fallback.
Supporta batch fetching parallelo con semaphore.
"""
from __future__ import annotations

import asyncio

from rich.console import Console

from config import HTTP_MAX_CONCURRENCY
from models import FetchedPage
from fetcher.httpx_fetcher import fetch_with_httpx
from fetcher.playwright_fetcher import fetch_with_playwright

console = Console(legacy_windows=False)

# Semaphore globale per limitare concorrenza
_semaphore = asyncio.Semaphore(HTTP_MAX_CONCURRENCY)


async def fetch_url(url: str) -> FetchedPage:
    """
    Scarica una pagina web.
    1. Prova con httpx (veloce, leggero)
    2. Se fallisce → fallback Playwright (JS-heavy, Cloudflare)
    
    Returns:
        FetchedPage con html e metadati.
    """
    async with _semaphore:
        # 1. Prova httpx
        result = await fetch_with_httpx(url)

        if result.is_valid:
            return result

        # 2. Fallback: Playwright
        console.print(
            f"    [dim]-> httpx fallito ({result.error}), provo Playwright...[/dim]"
        )
        pw_result = await fetch_with_playwright(url)

        if pw_result.is_valid:
            return pw_result

        # Entrambi falliti
        console.print(f"    [red][ERRORE][/red] Fetch fallito per {url[:60]}...")
        return pw_result


async def fetch_batch(urls: list[str]) -> list[FetchedPage]:
    """
    Fetch parallelo di multipli URL con semaphore per limitare concorrenza.
    
    Returns:
        Lista di FetchedPage (include anche quelli falliti).
    """
    if not urls:
        return []

    console.print(f"\n  [blue][FETCH][/blue] Fetching {len(urls)} pagine...")

    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Gestisci eccezioni non catturate
    pages: list[FetchedPage] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            pages.append(FetchedPage(
                url=urls[i],
                fetch_method="error",
                is_valid=False,
                error=str(result)[:150],
            ))
        else:
            pages.append(result)

    valid = sum(1 for p in pages if p.is_valid)
    console.print(
        f"  [blue][FETCH][/blue] Fetch completato: {valid}/{len(pages)} pagine valide"
    )

    return pages
