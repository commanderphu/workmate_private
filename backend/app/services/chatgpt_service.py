"""
ChatGPT plan usage ("Sign in with ChatGPT"): OAuth session and inference.

Docs: https://developers.openai.com/siwc/token-sharing-open-source
The flow is a preview. Sign-in needs a browser and a 127.0.0.1 callback, so it runs
locally (scripts/chatgpt_login.py) and the session is imported into the database.
From then on the server owns all refreshes.
"""

import base64
import hashlib
import json
import logging
import secrets
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from ..core.config import settings
from ..db.session import SessionLocal
from ..models.llm_credential import LLMCredential

logger = logging.getLogger(__name__)

PROVIDER = "chatgpt"
AUTH_BASE = "https://auth.openai.com"
AUTHORIZE_URL = f"{AUTH_BASE}/api/accounts/authorize"
TOKEN_URL = f"{AUTH_BASE}/api/accounts/oauth/token"
DISCOVERY_URL = f"{AUTH_BASE}/.well-known/openid-configuration"
API_BASE = "https://api.openai.com/v1"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
SCOPES = f"openid profile email offline_access resource.invoke {PLAN_SCOPE}"
REGISTRATION_CLIENT_ID = "dynamic_agent_client"
APP_NAME = "Workmate Private"
EXPIRY_MARGIN_SECONDS = 300
INFERENCE_TIMEOUT = httpx.Timeout(120, connect=10)

TERMINAL_REFRESH_ERRORS = {
    "invalid_grant",
    "invalid_refresh_token",
    "token_expired",
    "refresh_token_expired",
    "refresh_token_invalidated",
    "refresh_token_reused",
}
# Repeating the same request cannot help (429: OpenAI says to pause, without a reset time)
PERMANENT_API_ERRORS = {
    "subscription_sharing_usage_limit_exceeded",
    "subscription_sharing_user_not_eligible",
    "subscription_sharing_unsupported_capability",
}


class ChatGPTError(Exception):
    """Temporary failure: credentials stay valid, a later retry may work."""

    retryable = True


class ChatGPTPermanentError(ChatGPTError):
    """Retrying the same request will not help."""

    retryable = False


class ChatGPTLoginRequired(ChatGPTPermanentError):
    """No usable session: run scripts/chatgpt_login.py again."""


class _TokenRejected(ChatGPTPermanentError):
    """API answered 401 for this access token."""


# --- Encrypted storage ---

def _fernet() -> Fernet:
    digest = hashlib.sha256(f"llm-credentials:{settings.SECRET_KEY}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt(credential: dict) -> str:
    return _fernet().encrypt(json.dumps(credential).encode()).decode()


def _decrypt(row: Optional[LLMCredential]) -> dict:
    if row is None:
        raise ChatGPTLoginRequired("No ChatGPT session stored, run scripts/chatgpt_login.py")
    try:
        return json.loads(_fernet().decrypt(row.payload.encode()))
    except InvalidToken as exc:
        raise ChatGPTLoginRequired("Stored ChatGPT session cannot be decrypted (SECRET_KEY changed?)") from exc


def _locked_row(db) -> Optional[LLMCredential]:
    return (
        db.query(LLMCredential)
        .filter(LLMCredential.provider == PROVIDER)
        .populate_existing()
        .with_for_update()
        .first()
    )


def import_credential(credential: dict) -> dict:
    """Store a session from `chatgpt_login.py login`. The server keeps its own host ID."""
    missing = {"client_id", "access_token", "refresh_token", "expires_at"} - credential.keys()
    if missing:
        raise ValueError(f"Credential is missing fields: {sorted(missing)}")
    if PLAN_SCOPE not in credential.get("scopes", []):
        raise ValueError(f"Credential lacks the {PLAN_SCOPE} scope")

    with SessionLocal() as db:
        row = _locked_row(db)
        try:
            host_id = _decrypt(row).get("ext_agent_host_id") if row else None
        except ChatGPTLoginRequired:
            host_id = None
        stored = {**credential, "ext_agent_host_id": host_id or new_host_id()}
        if row:
            row.payload = _encrypt(stored)
        else:
            db.add(LLMCredential(provider=PROVIDER, payload=_encrypt(stored)))
        db.commit()
    return stored


def session_info() -> dict:
    """Non-secret session data, e.g. the IDs needed for the next login."""
    with SessionLocal() as db:
        credential = _decrypt(db.get(LLMCredential, PROVIDER))
    return {
        "email": credential.get("email"),
        "client_id": credential["client_id"],
        "ext_agent_host_id": credential.get("ext_agent_host_id"),
        "has_refresh_token": bool(credential.get("refresh_token")),
        "access_token_expires_at": datetime.fromtimestamp(credential["expires_at"], timezone.utc).isoformat(),
    }


# --- Tokens ---

def _usable(credential: dict, rejected: Optional[str]) -> bool:
    token = credential.get("access_token")
    return bool(token) and token != rejected and credential["expires_at"] > time.time() + EXPIRY_MARGIN_SECONDS


def _error_code(response: httpx.Response) -> Optional[str]:
    try:
        body = response.json()
    except ValueError:
        return None
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict):
        return error.get("code") or error.get("type")
    return error or (body.get("code") if isinstance(body, dict) else None)


def _refresh(credential: dict) -> dict:
    if not credential.get("refresh_token"):
        raise ChatGPTLoginRequired("ChatGPT session has no refresh token, run scripts/chatgpt_login.py")
    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": credential["client_id"],
                "refresh_token": credential["refresh_token"],
                "resource": API_BASE,
            },
            timeout=30,
        )
    except httpx.HTTPError as exc:
        raise ChatGPTError(f"ChatGPT token refresh failed: {type(exc).__name__}") from exc

    if response.status_code == 200:
        return response.json()
    code = _error_code(response)
    if code in TERMINAL_REFRESH_ERRORS:
        raise ChatGPTLoginRequired(f"ChatGPT session ended ({code}), run scripts/chatgpt_login.py")
    if code == "invalid_client":
        raise ChatGPTPermanentError("ChatGPT client_id was rejected (invalid_client)")
    raise ChatGPTError(f"ChatGPT token refresh failed: HTTP {response.status_code} code={code}")


def get_access_token(rejected: Optional[str] = None) -> str:
    """Return a valid access token. `rejected` forces a refresh unless another process already did it."""
    with SessionLocal() as db:
        credential = _decrypt(db.get(LLMCredential, PROVIDER))
        if _usable(credential, rejected):
            return credential["access_token"]

        row = _locked_row(db)
        credential = _decrypt(row)
        if _usable(credential, rejected):
            return credential["access_token"]

        try:
            tokens = _refresh(credential)
        except ChatGPTLoginRequired:
            credential.update(access_token=None, refresh_token=None, id_token=None, expires_at=0)
            row.payload = _encrypt(credential)
            db.commit()
            raise

        credential.update(
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", credential["refresh_token"]),
            id_token=tokens.get("id_token", credential.get("id_token")),
            expires_at=int(time.time()) + int(tokens.get("expires_in", 3600)),
        )
        row.payload = _encrypt(credential)
        db.commit()
        return credential["access_token"]


# --- Inference ---

def _raise_for_code(status: object, code: Optional[str], request_id: Optional[str]) -> None:
    message = f"ChatGPT request failed: status={status} code={code} request_id={request_id}"
    logger.warning(message)
    if code in PERMANENT_API_ERRORS or status in (400, 403):
        raise ChatGPTPermanentError(message)
    raise ChatGPTError(message)


def _stream_response(prompt: str, model: str, token: str) -> str:
    chunks = []
    try:
        with httpx.stream(
            "POST",
            f"{API_BASE}/responses",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": model,
                "input": [{"role": "user", "content": prompt}],
                "store": False,
                "stream": True,
            },
            timeout=INFERENCE_TIMEOUT,
        ) as response:
            request_id = response.headers.get("x-request-id")
            if response.status_code != 200:
                response.read()
                if response.status_code == 401:
                    raise _TokenRejected(f"ChatGPT rejected the token: code={_error_code(response)}")
                _raise_for_code(response.status_code, _error_code(response), request_id)

            for line in response.iter_lines():
                if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                    continue
                event = json.loads(line[5:])
                kind = event.get("type")
                if kind == "response.output_text.delta":
                    chunks.append(event["delta"])
                elif kind == "response.completed":
                    if not chunks:
                        raise ChatGPTError("ChatGPT response completed without text")
                    return "".join(chunks)
                elif kind == "response.failed":
                    error = (event.get("response") or {}).get("error") or {}
                    _raise_for_code("response.failed", error.get("code", "unknown_error"), request_id)
                elif kind == "response.incomplete":
                    raise ChatGPTError("ChatGPT response is incomplete")
    except httpx.HTTPError as exc:
        raise ChatGPTError(f"ChatGPT request failed: {type(exc).__name__}") from exc
    raise ChatGPTError("ChatGPT stream ended without response.completed")


def complete(prompt: str, model: str) -> str:
    """Send one prompt against the ChatGPT plan and return the answer text."""
    token = get_access_token()
    try:
        return _stream_response(prompt, model, token)
    except _TokenRejected:
        return _stream_response(prompt, model, get_access_token(rejected=token))


def list_models() -> list[dict]:
    """Models the signed-in account may use (they differ per account, so never hardcode one)."""
    response = httpx.get(
        f"{API_BASE}/models",
        headers={"Authorization": f"Bearer {get_access_token()}"},
        timeout=30,
    )
    response.raise_for_status()
    return [
        {"slug": model["slug"], "display_name": model.get("display_name")}
        for model in response.json().get("models", [])
        if model.get("visibility") == "list"
    ]


# --- Sign-in (runs locally, see scripts/chatgpt_login.py) ---

def new_host_id() -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def new_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def build_authorize_url(
    redirect_uri: str, state: str, nonce: str, code_challenge: str, host_id: str, client_id: Optional[str] = None
) -> str:
    params = {
        "client_id": client_id or REGISTRATION_CLIENT_ID,
        "ext_agent_host_id": host_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "resource": API_BASE,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if not client_id:
        params["agent_name_hint"] = APP_NAME
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def parse_callback(params: dict, state: str, known_client_id: Optional[str] = None) -> tuple[str, str]:
    """Validate the OAuth callback and return (code, client_id)."""
    if not secrets.compare_digest(params.get("state", ""), state):
        raise ValueError("OAuth state mismatch")
    if params.get("error"):
        raise ValueError(f"Sign-in failed: {params['error']}")
    if not params.get("code"):
        raise ValueError("Callback has no authorization code")
    issued = params.get("client_id")
    if known_client_id and issued and issued != known_client_id:
        raise ValueError("Callback client_id differs from the stored one")
    client_id = known_client_id or issued
    if not client_id:
        raise ValueError("Registration incomplete: callback has no client_id")
    return params["code"], client_id


def exchange_code(client_id: str, code: str, verifier: str, redirect_uri: str) -> dict:
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": redirect_uri,
            "resource": API_BASE,
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise ValueError(f"Token exchange failed: HTTP {response.status_code} code={_error_code(response)}")
    return response.json()


def verify_id_token(id_token: str, client_id: str, nonce: str) -> dict:
    """Check signature, issuer, audience, expiry and nonce, then return the claims."""
    discovery = httpx.get(DISCOVERY_URL, timeout=30).raise_for_status().json()
    jwks = httpx.get(discovery["jwks_uri"], timeout=30).raise_for_status().json()
    try:
        claims = jwt.decode(
            id_token,
            jwks,
            algorithms=discovery.get("id_token_signing_alg_values_supported", ["RS256"]),
            audience=client_id,
            issuer=discovery["issuer"],
            options={"verify_at_hash": False},
        )
    except JWTError as exc:
        raise ValueError(f"Invalid ID token: {exc}") from exc
    if not secrets.compare_digest(claims.get("nonce", ""), nonce):
        raise ValueError("ID token nonce mismatch")
    return claims


def build_credential(tokens: dict, claims: dict, client_id: str) -> dict:
    scopes = tokens.get("scope", "").split()
    if PLAN_SCOPE not in scopes:
        raise ValueError("ChatGPT plan use was not granted (is it enabled for this account?)")
    return {
        "email": claims.get("email"),
        "subject": claims.get("sub"),
        "client_id": client_id,
        "id_token": tokens.get("id_token"),
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_at": int(time.time()) + int(tokens.get("expires_in", 3600)),
        "scopes": scopes,
    }
