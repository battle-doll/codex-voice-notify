# Support

Report reproducible bugs and feature requests through
[GitHub Issues](https://github.com/battle-doll/codex-voice-notify/issues).

Run the bundled settings script's read-only `doctor` first. Include only the
plugin version, Codex CLI/app versions, operating-system family/version, chosen
voice/language, event, selected audio backend, and whether approval succeeded.
Diagnostics do not alter settings, approve hooks, or play sound. Redact local
paths, user/host names, account identifiers, and unrelated hook metadata. Never
upload raw logs, settings, review receipts, prompts, transcripts, credentials,
or tool payloads.

If the settings test works but a real lifecycle event is silent, run
`review-hooks`, review the exact Voice Notify commands, approve only after
informed consent, and fully close/relaunch the relevant Codex process. When the
local approval API is unavailable, use the visible `/hooks` fallback to review
and trust the commands manually. A settings test or approval receipt alone is
not proof that lifecycle playback works.

macOS playback/settings/approval use bundled system tools; Windows uses native
PowerShell; Linux needs Python 3 and an installed `pw-play`, `paplay`, `aplay`,
or `ffplay` with an accessible audio device/server. Headless, SSH, containers,
and WSL may have no audible output. The plugin never installs audio packages
or updates Codex silently.
