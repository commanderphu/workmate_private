"""
Tests for the LLM provider switch in ClaudeService (Anthropic vs. OpenAI-compatible APIs)
"""

from pathlib import Path

import httpx
import pytest

from app.services import claude_service
from app.services.claude_service import ClaudeService

ANSWER = '```json\n{"type": "Rechnung", "summary": "Telekom-Rechnung", "amount": 49.99}\n```'


@pytest.fixture()
def openai_settings(monkeypatch):
    s = claude_service.settings
    monkeypatch.setattr(s, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(s, "LLM_BASE_URL", "https://api.groq.com/openai/v1/")
    monkeypatch.setattr(s, "LLM_API_KEY", "gsk_test")
    monkeypatch.setattr(s, "LLM_MODEL", "llama-3.3-70b-versatile")
    return s


@pytest.fixture()
def fake_post(monkeypatch):
    calls = []

    def _post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json})
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"choices": [{"message": {"content": ANSWER}}]}, request=request)

    monkeypatch.setattr(claude_service.httpx, "post", _post)
    return calls


class TestOpenAICompatible:
    def test_paperless_analysis_uses_chat_completions(self, openai_settings, fake_post):
        result = ClaudeService().analyze_for_paperless("Rechnung der Telekom über 49,99 EUR")

        assert result == {"type": "Rechnung", "summary": "Telekom-Rechnung", "amount": 49.99}
        call = fake_post[0]
        assert call["url"] == "https://api.groq.com/openai/v1/chat/completions"
        assert call["headers"] == {"Authorization": "Bearer gsk_test"}
        assert call["json"]["model"] == "llama-3.3-70b-versatile"
        assert "Telekom" in call["json"]["messages"][0]["content"]

    def test_without_api_key_no_auth_header(self, openai_settings, fake_post, monkeypatch):
        # e.g. a local Ollama
        monkeypatch.setattr(openai_settings, "LLM_API_KEY", None)
        ClaudeService().analyze_document("Text")
        assert fake_post[0]["headers"] == {}

    def test_http_error_is_raised(self, openai_settings, monkeypatch):
        # Rate limit on a free tier must surface, so the task retries and stores ai_error
        def _post(url, **kwargs):
            return httpx.Response(429, json={"error": "rate limit"}, request=httpx.Request("POST", url))

        monkeypatch.setattr(claude_service.httpx, "post", _post)
        with pytest.raises(httpx.HTTPStatusError):
            ClaudeService().analyze_for_paperless("Text")

    def test_missing_base_url_is_rejected(self, openai_settings, monkeypatch):
        monkeypatch.setattr(openai_settings, "LLM_BASE_URL", None)
        with pytest.raises(ValueError, match="LLM_BASE_URL"):
            ClaudeService()

    def test_image_analysis_not_supported(self, openai_settings):
        with pytest.raises(NotImplementedError):
            ClaudeService().analyze_document_image(Path("scan.png"))


class TestProviderSelection:
    def test_claude_requires_api_key(self, monkeypatch):
        monkeypatch.setattr(claude_service.settings, "LLM_PROVIDER", "claude")
        monkeypatch.setattr(claude_service.settings, "CLAUDE_API_KEY", None)
        with pytest.raises(ValueError, match="CLAUDE_API_KEY"):
            ClaudeService()

    def test_unknown_provider_is_rejected(self, monkeypatch):
        monkeypatch.setattr(claude_service.settings, "LLM_PROVIDER", "irgendwas")
        with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
            ClaudeService()
