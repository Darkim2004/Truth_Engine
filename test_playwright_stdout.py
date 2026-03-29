import sys
import io
import asyncio
from fetcher.playwright_fetcher import fetch_with_playwright



async def main():
    res = await fetch_with_playwright("https://example.com")
    print(res.is_valid)

asyncio.run(main())
