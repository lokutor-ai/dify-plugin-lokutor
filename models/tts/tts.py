from collections.abc import Generator

from dify_plugin import TTSModel
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeBadRequestError,
    InvokeError,
)

from ..common import (
    auth_headers,
    base_url,
    common_invoke_error_mapping,
    language_of,
    merge_wavs,
    post,
    raise_for_response,
    split_text,
)

VOICES = {f"{g}{n}" for g in "FM" for n in range(1, 6)}
CHAR_LIMIT = 5000  # Lokutor's per-request limit on /tts/synthesize


class LokutorText2SpeechModel(TTSModel):
    def _invoke(
        self,
        model: str,
        tenant_id: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: str | None = None,
    ) -> bytes | Generator[bytes, None, None]:
        if not content_text or not content_text.strip():
            raise InvokeBadRequestError("Text-to-speech input must not be empty")
        if voice not in VOICES:
            voice = self._get_model_default_voice(model, credentials) or "F1"
        return self._synthesize(credentials, content_text, voice)

    def _synthesize(self, credentials: dict, text: str, voice: str) -> bytes:
        """Return one WAV file (16-bit PCM, 44.1 kHz, mono)."""
        parts = []
        for piece in split_text(text, CHAR_LIMIT):
            body = {"text": piece, "voice": voice}
            language = language_of(credentials)
            if language:
                body["language"] = language
            resp = post(
                f"{base_url(credentials)}/tts/synthesize",
                headers={**auth_headers(credentials), "Content-Type": "application/json"},
                json=body,
            )
            raise_for_response(resp)
            parts.append(resp.content)
        if not parts:
            raise InvokeBadRequestError("No audio was produced")
        return merge_wavs(parts)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        try:
            self._synthesize(credentials, "Hello", "F1")
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return common_invoke_error_mapping()
