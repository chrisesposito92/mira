"""Tests for LLM model factory and registry."""

import pytest

from app.agents.llm_factory import MODEL_REGISTRY, get_llm, list_models


class TestModelRegistry:
    def test_registry_has_five_models(self):
        assert len(MODEL_REGISTRY) == 5

    def test_all_expected_models_present(self):
        expected = {
            "gpt-5.2",
            "gemini-3-flash-preview",
            "gemini-3.1-pro-preview",
            "claude-opus-4-6",
            "claude-sonnet-4-6",
        }
        assert set(MODEL_REGISTRY.keys()) == expected

    def test_each_model_has_provider_and_name(self):
        for model_id, (provider, model_name) in MODEL_REGISTRY.items():
            assert isinstance(provider, str), f"{model_id} provider should be str"
            assert isinstance(model_name, str), f"{model_id} model_name should be str"
            assert len(provider) > 0
            assert len(model_name) > 0


class TestGetLlm:
    def test_invalid_model_id_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown model_id"):
            get_llm("nonexistent-model")

    def test_invalid_model_id_shows_available(self):
        with pytest.raises(ValueError, match="Available models"):
            get_llm("bad-id")


class TestListModels:
    def test_returns_all_five_models(self):
        models = list_models()
        assert len(models) == 5

    def test_each_model_has_required_fields(self):
        models = list_models()
        for model in models:
            assert "id" in model
            assert "provider" in model
            assert "display_name" in model

    def test_model_ids_match_registry(self):
        models = list_models()
        model_ids = {m["id"] for m in models}
        assert model_ids == set(MODEL_REGISTRY.keys())

    def test_providers_are_valid(self):
        valid_providers = {"openai", "anthropic", "google_genai"}
        models = list_models()
        for model in models:
            assert model["provider"] in valid_providers
