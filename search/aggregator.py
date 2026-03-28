"""
Truth Engine — Aggregatore risultati di ricerca.
Unisce risultati da più motori, deduplica URL.
"""
from __future__ import annotations

from rich.console import Console

from models import SearchResult
from utils.url_normalizer import normalize_url

console = Console()


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Deduplica risultati di ricerca basandosi sull'URL normalizzato.
    Se un URL appare da più motori, tiene il primo trovato.
    """
    seen_urls: dict[str, SearchResult] = {}
    duplicates = 0

    for result in results:
        normalized = normalize_url(result.url)
        if not normalized:
            continue

        if normalized not in seen_urls:
            seen_urls[normalized] = result
        else:
            duplicates += 1

    if duplicates > 0:
        console.print(f"  [dim]🔗 Rimossi {duplicates} URL duplicati[/dim]")

    return list(seen_urls.values())


async def aggregate_search(query: str) -> list[SearchResult]:
    """
    Cerca su tutti i motori disponibili, aggrega e deduplica risultati.
    Per ora solo DuckDuckGo. Brave si aggiunge dopo.
    """
    from search.duckduckgo import search_duckduckgo

    # Raccogli risultati da tutti i motori
    all_results: list[SearchResult] = []

    ddg_results = await search_duckduckgo(query)
    all_results.extend(ddg_results)

    # TODO: Aggiungere Brave qui
    # brave_results = await search_brave(query)
    # all_results.extend(brave_results)

    # Deduplica
    unique_results = deduplicate_results(all_results)

    console.print(
        f"  [blue]🔍[/blue] Totale: {len(unique_results)} URL unici "
        f"(da {len(all_results)} risultati)"
    )

    return unique_results
