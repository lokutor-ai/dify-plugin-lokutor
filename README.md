# Lokutor for Dify

Model provider plugin for [Dify](https://dify.ai): Lokutor's own speech models.

| Model type | Model | What it does |
| --- | --- | --- |
| Text to speech | `versa-2.0` | Ten voices (F1-F5, M1-M5), WAV output (16-bit PCM, 44.1 kHz, mono) |
| Speech to text | `conv-2.0` | One model for all nine languages, text with punctuation and casing |

Languages: English, Spanish, Catalan, Galician, Basque, Portuguese, French, Italian, German.

## Setup

1. Get an API key at https://lokutor.com.
2. In Dify, open **Settings > Model Provider**, install **Lokutor** and paste the key.
3. Optional fields: **API Base URL** (default `https://api.lokutor.com/v1`) and **Language** (a language code, or *Detect* to let Lokutor decide from the text or audio).
4. In **System Model Settings**, choose `versa-2.0` as the text-to-speech model and `conv-2.0` as the speech-to-text model.

Saving the key makes one short test synthesis ("Hello") to check it.

## Things to know

- **Speech to text takes WAV only** (PCM, 8 to 48 kHz). Other formats, such as MP3 or M4A, are refused with a clear error; convert them first.
- **Text to speech returns WAV.** Dify's players handle it; a client that insists on MP3 does not.
- Text over 5,000 characters is split on sentence ends and joined into one WAV.
- Without a language, Lokutor has no hint for synthesis and the voice speaks English-like by default; set the language for predictable results in the other eight.
- Billing and limits are those of your Lokutor account ([rate card](https://api.lokutor.com/v1/pricing)).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest          # unit tests with mocked HTTP
LOKUTOR_API_KEY=... .venv/bin/python -m pytest tests/test_live.py -s   # one live round trip
dify plugin package .               # builds the .difypkg
```

Source: https://github.com/lokutor-ai/dify-plugin-lokutor. Contact: contact@lokutor.com. Privacy: [PRIVACY.md](PRIVACY.md). License: MIT.
