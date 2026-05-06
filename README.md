# Speech To Text Bot

[![CI](https://github.com/ovsds/speech-to-text-bot/workflows/Check%20PR/badge.svg)](https://github.com/ovsds/speech-to-text-bot/actions?query=workflow%3A%22%22Check+PR%22%22)

Telegram bot that transcribes voice messages and audio/video attachments to text.

## Architecture

Telegram delivers voice and media messages (via webhook or long-polling) to an aiohttp server, where an aiogram dispatcher routes them to a media handler. In the default mode, the handler uploads the audio to S3-compatible storage and starts a [Temporal](https://temporal.io/) workflow that splits the audio on silence, recognizes each chunk in parallel as separate activities, calls back into the bot with the transcript, and cleans up the stored audio. Recognition uses the [`SpeechRecognition`](https://github.com/Uberi/speech_recognition) Python library's Google backend, configured for Russian. A simpler synchronous handler that skips Temporal and S3 is also available for single-process deployments. The two processes — the web/bot server (`backend/bin/main`) and the Temporal worker (`backend/bin/temporalio_worker`) — share the same `backend/lib` codebase.

See [`backend/README.md`](backend/README.md) for the full settings reference.

## Status

Working but maintained for personal use only, not as a service for others.

## Development

### Global dependencies

- [Taskfile](https://taskfile.dev/installation/)
- [nvm](https://github.com/nvm-sh/nvm?tab=readme-ov-file#install--update-script)
- [zizmor](https://woodruffw.github.io/zizmor/installation/) - used for GHA security scanning

### Taskfile commands

For all commands see [Taskfile](Taskfile.yaml) or `task --list-all`.

## License

[MIT](LICENSE)
