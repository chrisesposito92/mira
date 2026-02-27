"""Scrape m3ter documentation and save as JSON files.

Usage: cd backend && python -m scripts.scrape_m3ter_docs
"""

import asyncio
import json
import logging
import re
from pathlib import Path

from app.scraper.crawler import scrape_all_pages

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/m3ter_docs")


def slugify(url: str) -> str:
    """Convert URL to a safe filename slug."""
    # Remove protocol and domain, keep path
    path = re.sub(r"https?://[^/]+", "", url)
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-")
    return slug or "index"


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pages = await scrape_all_pages()
    logger.info("Scraped %d pages", len(pages))

    for page in pages:
        slug = slugify(page.url)
        out_path = OUTPUT_DIR / f"{slug}.json"
        data = {"url": page.url, "title": page.title, "content": page.content}
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Saved %s", out_path)

    logger.info("Done. %d files saved to %s", len(pages), OUTPUT_DIR)


if __name__ == "__main__":
    asyncio.run(main())
