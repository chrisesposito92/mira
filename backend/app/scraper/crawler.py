"""m3ter documentation scraper using llms.txt manifest."""

import asyncio
import logging
import re
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedPage:
    url: str
    title: str
    content: str


def parse_llms_manifest(text: str) -> list[dict]:
    """Parse llms.txt format: '- [Title](url): Description' lines."""
    pattern = r"-\s+\[([^\]]+)\]\(([^)]+)\)"
    results = []
    for match in re.finditer(pattern, text):
        title, url = match.group(1), match.group(2)
        results.append({"title": title, "url": url})
    return results


async def fetch_llms_manifest(base_url: str | None = None) -> list[dict]:
    """Fetch and parse the llms.txt manifest from the docs site."""
    base = base_url or settings.m3ter_docs_url
    url = f"{base.rstrip('/')}/llms.txt"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return parse_llms_manifest(response.text)


async def scrape_page(client: httpx.AsyncClient, url: str) -> ScrapedPage | None:
    """Fetch a single page and return its content as markdown."""
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        # llms.txt links point to .md URLs that return raw markdown
        content = response.text
        # Extract title from first markdown heading if present
        title = ""
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line.removeprefix("# ").strip()
                break
        return ScrapedPage(url=url, title=title, content=content)
    except httpx.HTTPError:
        logger.warning("Failed to fetch %s", url)
        return None


async def scrape_all_pages(
    base_url: str | None = None,
    concurrency: int | None = None,
    delay: float | None = None,
) -> list[ScrapedPage]:
    """Scrape all pages from the llms.txt manifest with rate limiting."""
    concurrency = concurrency or settings.scraper_concurrency
    delay = delay or settings.scraper_delay

    manifest = await fetch_llms_manifest(base_url)
    logger.info("Found %d pages in llms.txt manifest", len(manifest))

    semaphore = asyncio.Semaphore(concurrency)
    pages: list[ScrapedPage] = []
    total = len(manifest)
    completed = 0

    async def _fetch_with_limit(client: httpx.AsyncClient, entry: dict) -> None:
        nonlocal completed
        async with semaphore:
            page = await scrape_page(client, entry["url"])
            if page:
                if not page.title:
                    page.title = entry["title"]
                pages.append(page)
            completed += 1
            if completed % 25 == 0 or completed == total:
                logger.info("Progress: %d/%d pages fetched", completed, total)
            await asyncio.sleep(delay)

    async with httpx.AsyncClient() as client:
        tasks = [_fetch_with_limit(client, entry) for entry in manifest]
        await asyncio.gather(*tasks)

    logger.info("Successfully scraped %d/%d pages", len(pages), len(manifest))
    return pages
