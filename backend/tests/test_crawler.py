"""Tests for m3ter docs scraper."""

from unittest.mock import AsyncMock, MagicMock

import httpx

from app.scraper.crawler import ScrapedPage, parse_llms_manifest, scrape_page


class TestParseLlmsManifest:
    def test_parses_standard_format(self):
        text = """# m3ter Docs

- [Getting Started](https://docs.m3ter.com/getting-started.md): Intro guide
- [API Reference](https://docs.m3ter.com/api-ref.md): Full API docs
"""
        results = parse_llms_manifest(text)
        assert len(results) == 2
        assert results[0] == {
            "title": "Getting Started",
            "url": "https://docs.m3ter.com/getting-started.md",
        }
        assert results[1] == {
            "title": "API Reference",
            "url": "https://docs.m3ter.com/api-ref.md",
        }

    def test_empty_text_returns_empty(self):
        assert parse_llms_manifest("") == []

    def test_no_matching_lines(self):
        text = "Just some plain text\nwith no links"
        assert parse_llms_manifest(text) == []

    def test_handles_special_characters_in_title(self):
        text = "- [Meters & Aggregations](https://docs.m3ter.com/meters.md): Guide"
        results = parse_llms_manifest(text)
        assert len(results) == 1
        assert results[0]["title"] == "Meters & Aggregations"


class TestScrapePage:
    async def test_successful_fetch(self):
        mock_response = MagicMock()
        mock_response.text = "# Page Title\n\nSome content here."
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await scrape_page(mock_client, "https://docs.m3ter.com/test.md")
        assert result is not None
        assert result.title == "Page Title"
        assert "Some content here." in result.content
        assert result.url == "https://docs.m3ter.com/test.md"

    async def test_failed_fetch_returns_none(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))

        result = await scrape_page(mock_client, "https://docs.m3ter.com/bad.md")
        assert result is None

    async def test_no_title_heading(self):
        mock_response = MagicMock()
        mock_response.text = "No heading here, just content."
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await scrape_page(mock_client, "https://docs.m3ter.com/test.md")
        assert result is not None
        assert result.title == ""

    async def test_returns_scraped_page_type(self):
        mock_response = MagicMock()
        mock_response.text = "# Title\nContent"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await scrape_page(mock_client, "https://example.com")
        assert isinstance(result, ScrapedPage)
