import io
import wave
from unittest.mock import MagicMock, patch

import pytest

from dify_plugin.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)
from models import common
from models.speech2text.speech2text import LokutorSpeech2TextModel
from models.tts.tts import LokutorText2SpeechModel


def wav(frames: bytes = b"\x01\x00" * 100, rate: int = 44100) -> bytes:
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return b.getvalue()


def response(status=200, content=b"", text="", json=None):
    r = MagicMock()
    r.status_code = status
    r.content = content
    r.text = text
    r.json.return_value = json
    return r


def make(cls):
    # Skip the SDK constructor: the models only need credentials passed per call.
    return cls.__new__(cls)


CREDS = {"api_key": "k", "language": "es"}


def test_split_and_merge():
    assert common.split_text("One. Two. Three.", 8) == ["One.", "Two.", "Three."]
    assert all(len(p) <= 5 for p in common.split_text("abcdefghijkl", 5))
    merged = common.merge_wavs([wav(b"\x01\x00" * 10), wav(b"\x02\x00" * 5)])
    with wave.open(io.BytesIO(merged)) as r:
        assert r.getnframes() == 15 and r.getframerate() == 44100


def test_tts_request_shape():
    m = make(LokutorText2SpeechModel)
    with patch("models.common.requests.post", return_value=response(content=wav())) as p:
        out = m._synthesize(CREDS, "Hola", "M2")
    assert out[:4] == b"RIFF"
    args, kw = p.call_args
    assert args[0] == "https://api.lokutor.com/v1/tts/synthesize"
    assert kw["json"] == {"text": "Hola", "voice": "M2", "language": "es"}
    assert kw["headers"]["Authorization"] == "Bearer k"


def test_tts_auto_language_and_custom_base():
    m = make(LokutorText2SpeechModel)
    with patch("models.common.requests.post", return_value=response(content=wav())) as p:
        m._synthesize({"api_key": "k", "language": "auto", "base_url": "http://x/v1/"}, "Hi", "F1")
    args, kw = p.call_args
    assert args[0] == "http://x/v1/tts/synthesize" and "language" not in kw["json"]


def test_tts_long_text_is_one_wav():
    m = make(LokutorText2SpeechModel)
    text = ("Sentence number one. " * 400).strip()  # > 5000 chars
    with patch("models.common.requests.post", return_value=response(content=wav())) as p:
        out = m._synthesize({"api_key": "k"}, text, "F1")
    assert p.call_count >= 2
    with wave.open(io.BytesIO(out)) as r:
        assert r.getnframes() == 100 * p.call_count


@pytest.mark.parametrize(
    "status,exc",
    [(401, InvokeAuthorizationError), (429, InvokeRateLimitError), (503, InvokeServerUnavailableError), (400, InvokeBadRequestError)],
)
def test_errors(status, exc):
    m = make(LokutorText2SpeechModel)
    with patch("models.common.requests.post", return_value=response(status=status, text="no")):
        with pytest.raises(exc):
            m._synthesize(CREDS, "Hi", "F1")


def test_empty_text_rejected():
    with pytest.raises(InvokeBadRequestError):
        make(LokutorText2SpeechModel)._invoke("versa-2.0", "t", CREDS, "  ", "F1")


def test_stt_request_shape():
    m = make(LokutorSpeech2TextModel)
    with patch("models.common.requests.post", return_value=response(json={"text": "hola"})) as p:
        assert m._transcribe(CREDS, io.BytesIO(wav())) == "hola"
    args, kw = p.call_args
    assert args[0] == "https://api.lokutor.com/v1/audio/transcriptions"
    assert kw["data"] == {"model": "conv-2.0", "language": "es"}
    assert kw["files"]["file"][2] == "audio/wav"


def test_stt_rejects_non_wav():
    with pytest.raises(InvokeBadRequestError):
        make(LokutorSpeech2TextModel)._transcribe(CREDS, io.BytesIO(b"ID3\x04mp3data"))
