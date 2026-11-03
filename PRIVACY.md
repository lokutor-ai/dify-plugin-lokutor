# Privacy policy: Lokutor plugin for Dify

This plugin sends the data you give it to the Lokutor API (`https://api.lokutor.com`, or the base URL you configure) and returns the result to Dify. It has no server of its own and collects nothing else.

## What is sent to Lokutor

- **Text to speech:** the text to be spoken, the chosen voice (F1-F5, M1-M5) and, if you set one, the language code.
- **Speech to text:** the audio file to transcribe (WAV) and, if you set one, the language code.
- **Every request:** your Lokutor API key, as a bearer token.
- At setup, saving the credentials makes one short test synthesis ("Hello") to check the key.

## What the plugin stores

Nothing. The API key lives in Dify's credential store. The plugin writes no files and keeps no logs of text, audio or transcripts; error messages from Lokutor are passed to Dify as they are.

## What Lokutor does with it

Processing, billing and retention are governed by Lokutor's own terms and privacy policy: https://lokutor.com/privacy-policy

## Contact

contact@lokutor.com
