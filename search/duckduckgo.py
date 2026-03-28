"""
Truth Engine — Ricerca DuckDuckGo.
Usa DDGS (sincrono, wrappato in executor per async).
Gestisce RatelimitException con backoff esponenziale.
"""
from __future__ import annotations

import asyncio
import random
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from ddgs import DDGS

from config import SEARCH_MAX_RESULTS, SEARCH_RETRY_MAX, SEARCH_BACKOFF_FACTOR, SEARCH_DELAY_BETWEEN
from models import SearchResult

console = Console()

# Thread pool per wrappare le chiamate sincrone
_executor = ThreadPoolExecutor(max_workers=2)


def _search_sync(query: str, max_results: int) -> list[dict]:
    """Esegue la ricerca DuckDuckGo in modo sincrono."""
    ddgs = DDGS()
    return ddgs.text(query, max_results=max_results)


async def search_duckduckgo(query: str, max_results: int = SEARCH_MAX_RESULTS) -> list[SearchResult]:
    """
    Cerca su DuckDuckGo e ritorna una lista di SearchResult.
    Gestisce rate limiting con retry + backoff esponenziale.
    
    La libreria ddgs v9 è sincrona, quindi usiamo un ThreadPoolExecutor
    per non bloccare l'event loop.
    """
    results: list[SearchResult] = []
    loop = asyncio.get_event_loop()

    for attempt in range(1, SEARCH_RETRY_MAX + 1):
        try:
            raw_results = await loop.run_in_executor(
                _executor, _search_sync, query, max_results
            )

            for r in raw_results:
                url = r.get("href", "")
                if url:
                    results.append(SearchResult(
                        url=url,
                        title=r.get("title", ""),
                        snippet=r.get("body", ""),
                        source_engine="duckduckgo",
                    ))

            console.print(
                f"  [green]✓[/green] DuckDuckGo: {len(results)} risultati per "
                f"'{query[:50]}{'...' if len(query) > 50 else ''}'"
            )
            return results

        except Exception as e:
            error_name = type(e).__name__

            # Check se è un rate limit (il nome della classe può variare)
            if "ratelimit" in error_name.lower() or "429" in str(e):
                sleep_time = SEARCH_BACKOFF_FACTOR ** attempt + random.uniform(0, 1)
                console.print(
                    f"  [yellow]⚠[/yellow] DuckDuckGo rate limit "
                    f"(tentativo {attempt}/{SEARCH_RETRY_MAX}). "
                    f"Attendo {sleep_time:.1f}s..."
                )
                await asyncio.sleep(sleep_time)
            else:
                console.print(f"  [red]✗[/red] DuckDuckGo errore: {error_name}: {e}")
                break

    console.print(
        f"  [red]✗[/red] DuckDuckGo: nessun risultato per "
        f"'{query[:50]}{'...' if len(query) > 50 else ''}'"
    )
    return results


async def search_duckduckgo_batch(queries: list[str]) -> dict[str, list[SearchResult]]:
    """
    Esegue ricerche multiple con delay tra una e l'altra per evitare rate limit.
    Ritorna un dict query -> risultati.
    """
    all_results: dict[str, list[SearchResult]] = {}

    for i, query in enumerate(queries):
        if i > 0:
            delay = SEARCH_DELAY_BETWEEN + random.uniform(0, 1)
            await asyncio.sleep(delay)

        all_results[query] = await search_duckduckgo(query)

    return all_results
