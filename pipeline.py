"""
Truth Engine — Pipeline orchestratore.
Coordina search → fetch → filter → extract per ogni claim.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel

from models import (
    PipelineInput,
    PipelineOutput,
    ClaimSources,
    ExtractedSource,
    SearchResult,
    FetchedPage,
)
from search.aggregator import aggregate_search
from fetcher.manager import fetch_batch
from fetcher.playwright_fetcher import close_browser
from extractor.content import extract_article_text
from extractor.metadata import extract_metadata
from utils.paywall_detector import is_paywall
from utils.language_filter import is_correct_language, detect_language

console = Console()


async def run_pipeline(input_data: dict) -> PipelineOutput:
    """
    Esegue l'intero pipeline di crawling e scraping.
    
    Flow:
    1. Parse input JSON
    2. Per ogni claim:
       a. Cerca URL con DuckDuckGo (+ Brave in futuro)
       b. Deduplica URL
       c. Fetch HTML (httpx → Playwright fallback)
       d. Filtra paywall
       e. Filtra lingua (se specificata)
       f. Estrai contenuto + metadati
    3. Ritorna output strutturato
    """
    # Parse input
    pipeline_input = PipelineInput(**input_data)
    claims = pipeline_input.analysis.claims_to_verify
    expected_lang = pipeline_input.metadata.language

    console.print(Panel(
        f"[bold]Truth Engine — Crawling Pipeline[/bold]\n"
        f"Claims da verificare: {len(claims)}\n"
        f"Lingua attesa: {expected_lang or 'non specificata (filtro disabilitato)'}",
        border_style="blue",
    ))

    all_results: list[ClaimSources] = []

    try:
        for i, claim in enumerate(claims):
            console.print(f"\n{'─' * 60}")
            console.print(
                f"[bold cyan]Claim {claim.id}[/bold cyan] ({i + 1}/{len(claims)}): "
                f"{claim.claim_text[:80]}..."
            )
            console.print(f"  Query: [italic]{claim.search_query}[/italic]")

            # --- 1. SEARCH ---
            console.print(f"\n  [blue]🔍 Fase 1: Ricerca...[/blue]")
            search_results: list[SearchResult] = await aggregate_search(claim.search_query)

            if not search_results:
                console.print(f"  [yellow]⚠[/yellow] Nessun risultato trovato. Skip claim.")
                all_results.append(ClaimSources(claim=claim, sources=[]))
                continue

            # --- 2. FETCH ---
            console.print(f"\n  [blue]📄 Fase 2: Fetch HTML...[/blue]")
            urls = [r.url for r in search_results]
            pages: list[FetchedPage] = await fetch_batch(urls)

            # --- 3. FILTER + EXTRACT ---
            console.print(f"\n  [blue]📰 Fase 3: Filtraggio + Estrazione...[/blue]")
            sources: list[ExtractedSource] = []

            for page in pages:
                if not page.is_valid:
                    console.print(f"    [dim]⊘ Skip (fetch fallito): {page.url[:50]}...[/dim]")
                    continue

                # Paywall check
                if is_paywall(page.html):
                    console.print(f"    [yellow]🔒 Paywall rilevato: {page.url[:50]}...[/yellow]")
                    continue

                # Estrai contenuto
                article_text = extract_article_text(page.html)
                if not article_text:
                    console.print(f"    [dim]⊘ Nessun contenuto estratto: {page.url[:50]}...[/dim]")
                    continue

                # Filtro lingua (opzionale)
                if expected_lang and not is_correct_language(article_text, expected_lang):
                    detected = detect_language(article_text)
                    console.print(
                        f"    [yellow]🌐 Lingua sbagliata ({detected} ≠ {expected_lang}): "
                        f"{page.url[:50]}...[/yellow]"
                    )
                    continue

                # Estrai metadati
                metadata = extract_metadata(page.html)
                lang_detected = detect_language(article_text)

                source = ExtractedSource(
                    url=page.url,
                    article_text=article_text,
                    metadata=metadata,
                    fetch_method=page.fetch_method,
                    language_detected=lang_detected,
                )
                sources.append(source)

                console.print(
                    f"    [green]✓[/green] Estratto: {metadata.title[:50] or page.url[:50]}... "
                    f"({len(article_text)} char)"
                )

            all_results.append(ClaimSources(claim=claim, sources=sources))

            console.print(
                f"\n  [blue]📊[/blue] Claim {claim.id}: "
                f"{len(sources)} fonti estratte su {len(search_results)} URL trovati"
            )

    finally:
        # Chiudi il browser Playwright se è stato usato
        await close_browser()

    # Costruisci output
    total_sources = sum(len(r.sources) for r in all_results)
    output = PipelineOutput(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_claims=len(claims),
        total_sources_found=total_sources,
        results=all_results,
    )

    console.print(f"\n{'═' * 60}")
    console.print(Panel(
        f"[bold green]Pipeline completato![/bold green]\n"
        f"Claims processati: {len(claims)}\n"
        f"Fonti totali estratte: {total_sources}",
        border_style="green",
    ))

    return output
