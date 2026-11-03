"""Shared helpers: credentials, HTTP errors and WAV handling for the Lokutor API."""

import io
import wave
from collections.abc import Mapping

import requests

from dify_plugin.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)

DEFAULT_BASE_URL = "https://api.lokutor.com/v1"
TIMEOUT = (10, 120)


def base_url(credentials: Mapping) -> str:
    return (credentials.get("base_url") or DEFAULT_BASE_URL).strip().rstrip("/")


def auth_headers(credentials: Mapping) -> dict:
    key = credentials.get("api_key")
    if not key:
        raise InvokeAuthorizationError("A Lokutor API key is required")
    return {"Authorization": f"Bearer {key}"}


def language_of(credentials: Mapping) -> str | None:
    """The configured language code, or None to let Lokutor detect it."""
    lang = (credentials.get("language") or "").strip()
    return None if lang in ("", "auto") else lang


def raise_for_response(resp: requests.Response) -> None:
    """Turn a non-200 Lokutor answer into the matching Dify error."""
    if resp.status_code == 200:
        return
    detail = (resp.text or "")[:500]
    code = resp.status_code
    if code in (401, 403):
        raise InvokeAuthorizationError(detail)
    if code == 429:
        raise InvokeRateLimitError(detail)
    if code == 402:
        raise InvokeBadRequestError(f"Lokutor balance or limit: {detail}")
    if code == 503 or code >= 500:
        raise InvokeServerUnavailableError(detail)
    raise InvokeBadRequestError(detail)


def post(url: str, **kwargs) -> requests.Response:
    try:
        resp = requests.post(url, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as e:
        raise InvokeConnectionError(f"Could not reach Lokutor: {type(e).__name__}") from e
    return resp


def common_invoke_error_mapping() -> dict[type[InvokeError], list[type[Exception]]]:
    return {
        InvokeConnectionError: [requests.exceptions.ConnectionError, requests.exceptions.Timeout],
        InvokeServerUnavailableError: [],
        InvokeRateLimitError: [],
        InvokeAuthorizationError: [],
        InvokeBadRequestError: [ValueError, KeyError],
    }


def split_text(text: str, limit: int) -> list[str]:
    """Split on sentence ends so no piece exceeds `limit` characters."""
    pieces: list[str] = []
    current = ""
    for sentence in _sentences(text):
        while len(sentence) > limit:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:limit])
            sentence = sentence[limit:]
        if len(current) + len(sentence) > limit and current:
            pieces.append(current)
            current = ""
        current += sentence
    if current.strip():
        pieces.append(current)
    return [p.strip() for p in pieces if p.strip()]


def _sentences(text: str) -> list[str]:
    import re

    return re.findall(r"[^.!?。！？\n]*[.!?。！？\n]+|[^.!?。！？\n]+$", text)


def merge_wavs(parts: list[bytes]) -> bytes:
    """Join WAV files with the same format into one WAV file."""
    if len(parts) == 1:
        return parts[0]
    out = io.BytesIO()
    writer: wave.Wave_write | None = None
    for part in parts:
        with wave.open(io.BytesIO(part), "rb") as r:
            if writer is None:
                writer = wave.open(out, "wb")
                writer.setparams(r.getparams())
            writer.writeframes(r.readframes(r.getnframes()))
    assert writer is not None
    writer.close()
    return out.getvalue()


def is_wav(data: bytes) -> bool:
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


