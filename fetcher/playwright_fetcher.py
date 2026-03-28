"""
Truth Engine — Fetch HTML con Playwright + stealth.
Fallback per pagine JS-heavy o protette da Cloudflare.
Simula comportamento umano: scroll, attese, stealth mode.
"""
from __future__ import annotations

import asyncio

from rich.console import Console
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from config import PLAYWRIGHT_TIMEOUT, PLAYWRIGHT_SCROLL_DELAY, PLAYWRIGHT_SCROLL_STEPS
from models import FetchedPage

console = Console()

# Singleton per riutilizzare il browser
_browser = None
_playwright = None


async def _get_browser():
    """Ottieni o crea un'istanza browser condivisa."""
    global _browser, _playwright

    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

    return _browser


async def close_browser():
    """Chiudi il browser e Playwright. Da chiamare a fine pipeline."""
    global _browser, _playwright

    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def fetch_with_playwright(url: str) -> FetchedPage:
    """
    Scarica una pagina con Playwright + stealth.
    
    - Applica playwright_stealth per evitare bot detection
    - Scroll lento per triggerare lazy-load
    - Aspetta networkidle o timeout
    
    Returns:
        FetchedPage con html e metadati.
    """
    try:
        from playwright_stealth import stealth_async
    except ImportError:
        console.print("  [red]✗[/red] playwright-stealth non installato")
        return FetchedPage(
            url=url,
            fetch_method="playwright",
            is_valid=False,
            error="playwright-stealth non installato",
        )

    try:
        browser = await _get_browser()

        # Nuovo contesto per ogni pagina (isolamento cookie/cache)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        page = await context.new_page()

        # Applica stealth
        await stealth_async(page)

        # Naviga
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
        except PlaywrightTimeout:
            console.print(f"    [yellow]⏱[/yellow] Playwright timeout navigazione: {url[:60]}...")
            await context.close()
            return FetchedPage(
                url=url,
                fetch_method="playwright",
                is_valid=False,
                error="Timeout navigazione",
            )

        # Aspetta un po' per JS rendering
        await asyncio.sleep(2)

        # Scroll lento per triggerare lazy-load
        for i in range(PLAYWRIGHT_SCROLL_STEPS):
            await page.evaluate(f"window.scrollBy(0, {300 + i * 200})")
            await asyncio.sleep(PLAYWRIGHT_SCROLL_DELAY / 1000)

        # Torna su
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        # Ottieni HTML completo
        html = await page.content()

        await context.close()

        if html and len(html) > 500:
            console.print(f"    [green]✓[/green] Playwright OK: {url[:60]}...")
            return FetchedPage(
                url=url,
                html=html,
                status_code=200,
                fetch_method="playwright",
                is_valid=True,
            )
        else:
            return FetchedPage(
                url=url,
                html=html,
                fetch_method="playwright",
                is_valid=False,
                error="HTML troppo corto o vuoto",
            )

    except PlaywrightTimeout:
        return FetchedPage(
            url=url,
            fetch_method="playwright",
            is_valid=False,
            error="Timeout Playwright",
        )

    except Exception as e:
        return FetchedPage(
            url=url,
            fetch_method="playwright",
            is_valid=False,
            error=f"Playwright errore: {str(e)[:150]}",
        )
