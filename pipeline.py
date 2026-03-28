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
from fetcher.manager import fetch_batch, fetch_url
from fetcher.playwright_fetcher import close_browser
from extractor.content import extract_article_text, extract_article_structured
from extractor.metadata import extract_metadata
from config import EMBEDDING_MIN_THRESHOLD
from utils.paywall_detector import is_paywall
from utils.language_filter import is_correct_language, detect_language
from utils.url_normalizer import normalize_url
from scoring.evidence_matcher import validate_evidence

console = Console()


def _classify_relevance(score: float, threshold: float) -> str:
    """Classifica la pertinenza semantica di una fonte rispetto al claim."""
    if score >= max(0.75, threshold):
        return "alta_pertinenza"
    if score >= max(0.5, threshold):
        return "media_pertinenza"
    if score >= threshold:
        return "bassa_pertinenza"
    return "non_rilevante"


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
    # Stato per-sessione (singolo JSON input): URL gia' visitati/schedulati.
    visited_urls: set[str] = set()

    # Se presente, l'URL originale in input viene marcato subito come gia' visitato
    # per evitare che venga riutilizzato come fonte durante la stessa sessione.
    input_source_url = pipeline_input.original_source.url
    if input_source_url:
        normalized_input_url = normalize_url(input_source_url)
        if normalized_input_url:
            visited_urls.add(normalized_input_url)
            console.print(
                f"[dim]🔒 URL input escluso dalle fonti: {normalized_input_url}[/dim]"
            )

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

            # Deduplica per sessione: evita di rivisitare URL gia' visti in claim precedenti.
            fresh_search_results: list[SearchResult] = []
            session_duplicates = 0

            for result in search_results:
                normalized = normalize_url(result.url)
                if not normalized:
                    continue

                if normalized in visited_urls:
                    session_duplicates += 1
                    continue

                fresh_search_results.append(result)
                visited_urls.add(normalized)

            if session_duplicates > 0:
                console.print(
                    f"  [dim]♻ Skip sessione: {session_duplicates} URL gia' visitati[/dim]"
                )

            if not fresh_search_results:
                console.print(
                    "  [yellow]⚠[/yellow] Tutti gli URL erano gia' visitati in questa sessione. "
                    "Skip claim."
                )
                all_results.append(ClaimSources(claim=claim, sources=[]))
                continue

            # --- 2. FETCH ---
            console.print(f"\n  [blue]📄 Fase 2: Fetch HTML...[/blue]")
            urls = [r.url for r in fresh_search_results]
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
                structured_data: dict = {}
                article_text = extract_article_text(page.html)
                if not article_text:
                    # Fallback: prova estrazione strutturata prima di scartare la fonte.
                    structured_data = extract_article_structured(page.html)
                    article_text = (structured_data.get("text", "") or "").strip()

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
                if not metadata.title and structured_data.get("title"):
                    metadata.title = structured_data.get("title", "")
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

            # --- 4. EVIDENCE SCORING (chunking + similarity) ---
            console.print(f"\n  [blue]🧠 Fase 4: Similarity scoring...[/blue]")
            source_scores: list[tuple[str, float]] = []

            for source in sources:
                analysis = validate_evidence(
                    url=source.url,
                    text=source.article_text,
                    claim=claim.claim_text,
                )
                source.chunks = analysis.get("chunks", [])
                source.chunk_similarity_scores = analysis.get("chunk_similarity_scores", [])
                source.top_chunk_indices = analysis.get("top_chunk_indices", [])
                source.relevant_chunks = analysis.get("matches", [])

                max_similarity = float(analysis.get("max_similarity", 0.0))
                supports_claim = bool(analysis.get("supports_claim", False))
                threshold = float(analysis.get("threshold", EMBEDDING_MIN_THRESHOLD))

                source.claim_score = max_similarity
                source.supports_claim = supports_claim
                source.claim_label = _classify_relevance(max_similarity, threshold)
                source_scores.append((source.url, max_similarity))

            # --- 5. CLAIM-LEVEL AGGREGATION ---
            if source_scores:
                best_source_url, claim_max_score = max(source_scores, key=lambda x: x[1])
            else:
                best_source_url, claim_max_score = "", 0.0

            claim_supported = any(s.supports_claim for s in sources)
            claim_label = _classify_relevance(claim_max_score, EMBEDDING_MIN_THRESHOLD)

            all_results.append(
                ClaimSources(
                    claim=claim,
                    sources=sources,
                    claim_supported=claim_supported,
                    claim_max_score=claim_max_score,
                    best_source_url=best_source_url,
                    claim_label=claim_label,
                )
            )

            console.print(
                f"\n  [blue]📊[/blue] Claim {claim.id}: "
                f"{len(sources)} fonti estratte su {len(fresh_search_results)} URL fetchati "
                f"({len(search_results)} trovati in ricerca) | "
                f"max_score={claim_max_score:.3f} | label={claim_label}"
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


async def get_article_title_from_url(url: str) -> str:
    """
    Metodo riusabile per FE/BE: dato un URL, ritorna il titolo articolo.

    Usa gli stessi strumenti della pipeline:
    - fetch manager (httpx con fallback Playwright)
    - extractor metadati (og:title, <title>, h1, ecc.)

    Returns:
        Titolo estratto, oppure stringa vuota se non disponibile.
    """
    normalized_url = normalize_url(url)
    if not normalized_url:
        return ""

    try:
        page = await fetch_url(normalized_url)
        if not page.is_valid or not page.html:
            return ""

        metadata = extract_metadata(page.html)
        return (metadata.title or "").strip()
    finally:
        # In chiamate standalone (es. endpoint frontend), rilascia risorse browser.
        await close_browser()


def get_article_title_from_url_sync(url: str) -> str:
    """
    Wrapper sincrono per ambienti non-async.

    Se il chiamante e' gia' in un event loop async, usare direttamente:
    `await get_article_title_from_url(url)`.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(get_article_title_from_url(url))

    raise RuntimeError(
        "Event loop gia' attivo: usa await get_article_title_from_url(url)."
    )
