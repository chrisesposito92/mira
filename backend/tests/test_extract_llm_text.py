"""Tests for extract_llm_text utility function."""

from app.agents.utils import extract_llm_text


class TestExtractLlmText:
    """Tests for extracting plain text from various LLM response formats."""

    def test_string_passthrough(self):
        assert extract_llm_text("hello world") == "hello world"

    def test_content_block_list(self):
        """Anthropic Claude returns content as list of content blocks."""
        content = [{"type": "text", "text": '[\n  {"title": "Use Case 1"}\n]'}]
        result = extract_llm_text(content)
        assert result == '[\n  {"title": "Use Case 1"}\n]'

    def test_multiple_content_blocks(self):
        content = [
            {"type": "text", "text": "first part"},
            {"type": "text", "text": " second part"},
        ]
        assert extract_llm_text(content) == "first part second part"

    def test_mixed_list_with_strings(self):
        content = ["some text", {"type": "text", "text": " more text"}]
        assert extract_llm_text(content) == "some text more text"

    def test_strips_json_code_fence(self):
        content = '```json\n[{"title": "Test"}]\n```'
        assert extract_llm_text(content) == '[{"title": "Test"}]'

    def test_strips_plain_code_fence(self):
        content = '```\n[{"title": "Test"}]\n```'
        assert extract_llm_text(content) == '[{"title": "Test"}]'

    def test_code_fence_in_content_blocks(self):
        """Combined: content blocks + code fence wrapping."""
        content = [{"type": "text", "text": '```json\n{"key": "val"}\n```'}]
        assert extract_llm_text(content) == '{"key": "val"}'

    def test_non_text_blocks_ignored(self):
        content = [
            {"type": "tool_use", "id": "123"},
            {"type": "text", "text": "actual content"},
        ]
        assert extract_llm_text(content) == "actual content"

    def test_fallback_for_unknown_type(self):
        assert extract_llm_text(42) == "42"

    def test_empty_list(self):
        assert extract_llm_text([]) == ""

    def test_empty_string(self):
        assert extract_llm_text("") == ""
