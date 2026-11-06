"""
Tests for LLM_PROVIDER=chatgpt: encrypted session storage, refresh, streaming, sign-in checks
"""

import json
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from app.models.llm_credential import LLMCredential
from app.services import chatgpt_service as chatgpt
from app.services import claude_service
from app.services.claude_service import ClaudeService
from app.tests.conftest import TestingSessionLocal


def credential(**overrides):
    return {
        "email": "user@example.com",
        "client_id": "oaiapp_test",
        "access_token": "access-old",
        "refresh_token": "refresh-old",
        "expires_at": int(time.time()) + 3600,
        "scopes": [chatgpt.PLAN_SCOPE],
        **overrides,
    }


def stored():
    with TestingSessionLocal() as session:
        return chatgpt._decrypt(session.get(LLMCredential, chatgpt.PROVIDER))


@pytest.fixture()
def store(db, monkeypatch):
    monkeypatch.setattr(chatgpt, "SessionLocal", TestingSessionLocal)
    return chatgpt.import_credential


@pytest.fixture()
def token_endpoint(monkeypatch):
    """Answers refresh calls with the given response and records them."""
    calls = []

    def install(status=200, body=None):
        body = body if body is not None else {
            "access_token": "access-new", "refresh_token": "refresh-new", "expires_in": 3600,
        }

        def _post(url, data=None, timeout=None):
            calls.append({"url": url, "data": data})
            return httpx.Response(status, json=body, request=httpx.Request("POST", url))

        monkeypatch.setattr(chatgpt.httpx, "post", _post)
        return calls

    return install


@pytest.fixture()
def api(monkeypatch):
    """Replaces the transport of httpx.stream with scripted responses, one per request."""
    requests = []

    def install(*responses):
        queue = list(responses)

        def handler(request):
            requests.append(request)
            return queue.pop(0)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        monkeypatch.setattr(chatgpt.httpx, "stream", client.stream)
        return requests

    return install


def sse(*events):
    lines = [f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events]
    return httpx.Response(200, text="".join(lines))


DELTAS = [
    {"type": "response.created"},
    {"type": "response.output_text.delta", "delta": "Hal"},
    {"type": "response.output_text.delta", "delta": "lo"},
]
COMPLETED = {"type": "response.completed", "response": {}}


class TestStorage:
    def test_tokens_are_encrypted_at_rest(self, store):
        store(credential())
        with TestingSessionLocal() as session:
            payload = session.get(LLMCredential, chatgpt.PROVIDER).payload
        assert "refresh-old" not in payload
        assert stored()["refresh_token"] == "refresh-old"

    def test_reimport_keeps_server_host_id(self, store):
        first = store(credential())["ext_agent_host_id"]
        second = store(credential(ext_agent_host_id="urn:uuid:laptop"))["ext_agent_host_id"]
        assert first.startswith("urn:uuid:")
        assert second == first

    def test_import_requires_plan_scope(self, store):
        with pytest.raises(ValueError, match=chatgpt.PLAN_SCOPE):
            store(credential(scopes=["openid"]))

    def test_missing_session_asks_for_login(self, store):
        with pytest.raises(chatgpt.ChatGPTLoginRequired):
            chatgpt.get_access_token()


class TestRefresh:
    def test_valid_token_is_not_refreshed(self, store, token_endpoint):
        calls = token_endpoint()
        store(credential())
        assert chatgpt.get_access_token() == "access-old"
        assert calls == []

    def test_expiring_token_rotates_refresh_token(self, store, token_endpoint):
        calls = token_endpoint()
        store(credential(expires_at=int(time.time()) + 60))
        assert chatgpt.get_access_token() == "access-new"
        assert calls[0]["url"] == chatgpt.TOKEN_URL
        assert calls[0]["data"] == {
            "grant_type": "refresh_token",
            "client_id": "oaiapp_test",
            "refresh_token": "refresh-old",
            "resource": "https://api.openai.com/v1",
        }
        assert stored()["refresh_token"] == "refresh-new"

    def test_terminal_error_clears_tokens_but_keeps_client(self, store, token_endpoint):
        token_endpoint(400, {"error": "refresh_token_reused"})
        store(credential(expires_at=0))
        with pytest.raises(chatgpt.ChatGPTLoginRequired):
            chatgpt.get_access_token()
        assert stored()["refresh_token"] is None
        assert stored()["client_id"] == "oaiapp_test"

    def test_temporary_error_keeps_credentials(self, store, token_endpoint):
        token_endpoint(503, {"error": "unavailable"})
        store(credential(expires_at=0))
        with pytest.raises(chatgpt.ChatGPTError) as exc:
            chatgpt.get_access_token()
        assert exc.value.retryable
        assert stored()["refresh_token"] == "refresh-old"


class TestInference:
    def test_joins_deltas_and_sends_required_fields(self, store, api):
        requests = api(sse(*DELTAS, COMPLETED))
        store(credential())
        assert chatgpt.complete("Prompt", "some-model") == "Hallo"
        body = json.loads(requests[0].content)
        assert str(requests[0].url) == "https://api.openai.com/v1/responses"
        assert requests[0].headers["authorization"] == "Bearer access-old"
        assert body == {
            "model": "some-model",
            "input": [{"role": "user", "content": "Prompt"}],
            "store": False,
            "stream": True,
        }

    def test_stream_without_completed_is_an_error(self, store, api):
        api(sse(*DELTAS))
        store(credential())
        with pytest.raises(chatgpt.ChatGPTError, match="without response.completed"):
            chatgpt.complete("Prompt", "some-model")

    def test_failure_after_stream_start_is_not_retried(self, store, api):
        failed = {
            "type": "response.failed",
            "response": {"error": {"code": "subscription_sharing_usage_limit_exceeded"}},
        }
        api(sse(*DELTAS, failed))
        store(credential())
        with pytest.raises(chatgpt.ChatGPTPermanentError, match="usage_limit_exceeded"):
            chatgpt.complete("Prompt", "some-model")

    @pytest.mark.parametrize("status,code,retryable", [
        (429, "subscription_sharing_usage_limit_exceeded", False),
        (403, "subscription_sharing_user_not_eligible", False),
        (400, "subscription_sharing_unsupported_capability", False),
        (503, "subscription_sharing_usage_unavailable", True),
    ])
    def test_http_errors(self, store, api, status, code, retryable):
        api(httpx.Response(status, json={"error": {"code": code}}, headers={"x-request-id": "req_1"}))
        store(credential())
        with pytest.raises(chatgpt.ChatGPTError, match="req_1") as exc:
            chatgpt.complete("Prompt", "some-model")
        assert exc.value.retryable is retryable

    def test_401_refreshes_once_and_retries(self, store, api, token_endpoint):
        token_endpoint()
        requests = api(
            httpx.Response(401, json={"error": {"code": "subscription_sharing_invalid_user"}}),
            sse(*DELTAS, COMPLETED),
        )
        store(credential())
        assert chatgpt.complete("Prompt", "some-model") == "Hallo"
        assert requests[1].headers["authorization"] == "Bearer access-new"

    def test_claude_service_routes_to_chatgpt(self, monkeypatch):
        monkeypatch.setattr(claude_service.settings, "LLM_PROVIDER", "chatgpt")
        monkeypatch.setattr(claude_service.settings, "LLM_MODEL", "some-model")
        monkeypatch.setattr(chatgpt, "complete", lambda prompt, model: f"{model}:{prompt}")
        assert ClaudeService()._complete("Prompt", max_tokens=10) == "some-model:Prompt"

    def test_model_is_required(self, monkeypatch):
        monkeypatch.setattr(claude_service.settings, "LLM_PROVIDER", "chatgpt")
        monkeypatch.setattr(claude_service.settings, "LLM_MODEL", None)
        with pytest.raises(ValueError, match="LLM_MODEL"):
            ClaudeService()


class TestSignIn:
    def test_first_registration_url(self):
        url = chatgpt.build_authorize_url("http://127.0.0.1:1455/auth/callback", "s", "n", "c", "urn:uuid:1")
        query = parse_qs(urlparse(url).query)
        assert query["client_id"] == ["dynamic_agent_client"]
        assert query["agent_name_hint"] == ["Workmate Private"]
        assert query["code_challenge_method"] == ["S256"]
        assert chatgpt.PLAN_SCOPE in query["scope"][0]

    def test_relogin_url_uses_issued_client(self):
        url = chatgpt.build_authorize_url("http://127.0.0.1:1455/auth/callback", "s", "n", "c", "h", "oaiapp_1")
        query = parse_qs(urlparse(url).query)
        assert query["client_id"] == ["oaiapp_1"]
        assert "agent_name_hint" not in query

    def test_callback_returns_issued_client(self):
        params = {"state": "s", "code": "abc", "client_id": "oaiapp_1"}
        assert chatgpt.parse_callback(params, "s") == ("abc", "oaiapp_1")

    @pytest.mark.parametrize("params,known,message", [
        ({"state": "x", "code": "abc", "client_id": "a"}, None, "state"),
        ({"state": "s", "error": "access_denied"}, None, "access_denied"),
        ({"state": "s", "code": "abc"}, None, "Registration incomplete"),
        ({"state": "s", "code": "abc", "client_id": "b"}, "a", "differs"),
    ])
    def test_callback_rejections(self, params, known, message):
        with pytest.raises(ValueError, match=message):
            chatgpt.parse_callback(params, "s", known)

    def test_credential_requires_granted_plan_scope(self):
        tokens = {"access_token": "a", "refresh_token": "r", "scope": "openid email"}
        with pytest.raises(ValueError, match="not granted"):
            chatgpt.build_credential(tokens, {}, "oaiapp_1")


class TestIdToken:
    @pytest.fixture()
    def sign(self, monkeypatch):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ).decode()
        public = jwk.construct(pem, "RS256").public_key().to_dict()
        documents = {
            chatgpt.DISCOVERY_URL: {"issuer": "https://auth.openai.com", "jwks_uri": "https://auth.openai.com/jwks"},
            "https://auth.openai.com/jwks": {"keys": [{**public, "kid": "k1"}]},
        }

        def _get(url, timeout=None):
            return httpx.Response(200, json=documents[url], request=httpx.Request("GET", url))

        monkeypatch.setattr(chatgpt.httpx, "get", _get)

        def _sign(**overrides):
            claims = {
                "iss": "https://auth.openai.com", "aud": "oaiapp_1", "sub": "user-1",
                "nonce": "n", "exp": int(time.time()) + 600, **overrides,
            }
            return jwt.encode(claims, pem, algorithm="RS256", headers={"kid": "k1"})

        return _sign

    def test_valid_token(self, sign):
        assert chatgpt.verify_id_token(sign(), "oaiapp_1", "n")["sub"] == "user-1"

    @pytest.mark.parametrize("overrides", [
        {"aud": "oaiapp_other"},
        {"iss": "https://evil.example"},
        {"exp": 1},
        {"nonce": "other"},
    ])
    def test_rejected_claims(self, sign, overrides):
        with pytest.raises(ValueError):
            chatgpt.verify_id_token(sign(**overrides), "oaiapp_1", "n")
