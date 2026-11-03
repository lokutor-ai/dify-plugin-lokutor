from typing import IO

from dify_plugin import Speech2TextModel
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeBadRequestError,
    InvokeError,
)

from ..common import (
    auth_headers,
    base_url,
    common_invoke_error_mapping,
    is_wav,
    language_of,
    post,
    raise_for_response,
)


class LokutorSpeech2TextModel(Speech2TextModel):
    def _invoke(
        self,
        model: str,
        credentials: dict,
        file: IO[bytes],
        user: str | None = None,
    ) -> str:
        return self._transcribe(credentials, file)

    def _transcribe(self, credentials: dict, file: IO[bytes]) -> str:
        data = file.read()
        if not is_wav(data):
            raise InvokeBadRequestError(
                "Lokutor transcribes WAV audio only (PCM, 8 to 48 kHz). Convert the file to WAV first."
            )
        form = {"model": "conv-2.0"}
        language = language_of(credentials)
        if language:
            form["language"] = language
        resp = post(
            f"{base_url(credentials)}/audio/transcriptions",
            headers=auth_headers(credentials),
            data=form,
            files={"file": ("audio.wav", data, "audio/wav")},
        )
        raise_for_response(resp)
        try:
            return resp.json()["text"]
        except (ValueError, KeyError) as e:
            raise InvokeBadRequestError("Unexpected answer from the Lokutor transcription API") from e

    def validate_credentials(self, model: str, credentials: dict) -> None:
        # One second of silence: proves the key and the endpoint without a real recording.
        import io
        import wave

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 16000)
        buf.seek(0)
        try:
            self._transcribe(credentials, buf)
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex)) from ex

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return common_invoke_error_mapping()
