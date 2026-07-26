# Voice Notify for Codex

Offline multilingual voice notifications for ten Codex lifecycle events on macOS
and Windows. Choose a warm husky voice or a deep bright voice in Korean,
Japanese, or English.

This is an independent plugin with MIT-licensed source code and separately
licensed voice assets. It is not affiliated with or endorsed by OpenAI.

## What it does

The plugin plays a local WAV for:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PermissionRequest`
- `PreCompact`
- `PostCompact`
- `SubagentStart`
- `SubagentStop`
- `Stop`

It uses the macOS system `afplay` player or Windows `System.Media.SoundPlayer`.
It has no network code or telemetry and never stores prompts, messages, tool
input, or tool output. Playback is non-blocking, and a local lock plus a short
cooldown prevents overlapping clips.

## Install from GitHub

Give Codex the repository URL and ask it to install the plugin, or run:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Restart Codex, open `/hooks`, inspect the bundled command, and explicitly trust it.
Then fully restart Codex again before testing lifecycle events. Hook trust is
persisted, but an already-running Codex process may not activate newly trusted
plugin hooks until the next launch. Codex deliberately does not trust
third-party hooks at install time, and the plugin must not bypass that review.

## Configure

Ask Codex to configure Voice Notify, or run the bundled command from a clone:

macOS:

```bash
/usr/bin/python3 scripts/voice_notify_config.py show
/usr/bin/python3 scripts/voice_notify_config.py set --voice female --language ko
/usr/bin/python3 scripts/voice_notify_config.py set --voice male --language en
/usr/bin/python3 scripts/voice_notify_config.py test --event Stop
/usr/bin/python3 scripts/voice_notify_config.py mute
```

Windows:

```powershell
powershell.exe -NoProfile -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -File scripts\voice_notify_config.ps1 mute
```

Defaults are `female`, `ko`, a 450 ms minimum interval, and eight events
enabled. `PreToolUse` and `PostToolUse` remain available but default to off to
avoid noisy per-tool notifications. `PermissionRequest` only plays when Codex
actually asks for permission.

## Compatibility

Version 0.1.2 supports macOS and Windows with only system-provided audio and
scripting components. Linux is not yet supported.

## Licensing

Source code is MIT licensed. WAV files under `assets/audio/` are excluded from
the MIT license and use the separate terms in [ASSET_LICENSE.md](ASSET_LICENSE.md).
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for generation provenance.
Most of the male notification set was built with Fish Audio and is subject to
the non-commercial asset boundary described there. Two Korean subagent files
were regenerated with Qwen Base to match the current wording.
