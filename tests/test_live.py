"""One live round trip; runs only when LOKUTOR_API_KEY is set."""
import io
import os

import pytest

from models.speech2text.speech2text import LokutorSpeech2TextModel
from models.tts.tts import LokutorText2SpeechModel

pytestmark = pytest.mark.skipif(not os.environ.get("LOKUTOR_API_KEY"), reason="no key")


def test_round_trip():
    creds = {"api_key": os.environ["LOKUTOR_API_KEY"], "language": "en"}
    audio = LokutorText2SpeechModel.__new__(LokutorText2SpeechModel)._synthesize(creds, "Hello", "F1")
    assert audio[:4] == b"RIFF"
    text = LokutorSpeech2TextModel.__new__(LokutorSpeech2TextModel)._transcribe(creds, io.BytesIO(audio))
    print("transcript:", text)
    assert text.lower().startswith("hel")  # one-word clip: "Hella." was observed
