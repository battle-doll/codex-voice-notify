# Voice Notify for Codex

Offline multilingual voice notifications for ten Codex lifecycle events on macOS
and Windows. Choose a warm husky voice or a deep bright voice in Korean,
Japanese, English, Russian, or Simplified Chinese.

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

Version 0.1.5 bundles 100 WAV files: ten lifecycle events for each combination
of two voice profiles and five languages.

It uses `/bin/sh`, `plutil`, `afplay`, and `osascript` already included with
macOS, or Windows PowerShell and `System.Media.SoundPlayer`. It does not require
Python or Xcode Command Line Tools. It has no network code or telemetry and
never stores prompts, messages, tool input, or tool output. Playback is
non-blocking, and a local lock plus a short cooldown prevents overlapping clips.

## Install from GitHub

Give Codex the repository URL and ask it to install the plugin, or run:

macOS:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Windows PowerShell:

```powershell
codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main
codex.cmd plugin add codex-voice-notify@codex-voice-notify
```

## First-time setup

After installation, select the plugin's **Finish first-time setup** prompt or
ask Codex naturally:

> Finish first-time setup for Voice Notify using the female Korean voice.
> Check and update the Codex CLI if required.

This is a safe, repeatable starter prompt. Current Codex plugin UI does not
conditionally hide a prompt after first use, so it remains available for
recovery or re-running setup.

The guided setup:

1. Checks for a Codex CLI version that supports `/hooks` and, when explicitly
   authorized by the setup prompt, updates an npm or Homebrew installation if
   required.
2. Saves the selected voice and language.
3. Plays the local `Stop` notification as a test.
4. Opens a new terminal window and starts the verified Codex CLI in it; it does
   not merely print a `/hooks` instruction.

The bundled setup script only reports compatibility; it does not modify the
host installation by itself. Codex performs an authorized update after
inspecting whether the CLI came from npm, the Homebrew cask, or another source.

In the newly opened Codex CLI terminal, enter `/hooks`, inspect the bundled
command, and explicitly trust it. Then fully restart Codex before testing
lifecycle events. Hook trust is persisted, but an already-running Codex process
may not activate newly trusted plugin hooks until the next launch. Codex
deliberately does not trust third-party hooks at install time, and the plugin
never bypasses that review.

If an update cannot replace a currently running CLI executable, exit that CLI,
run the displayed update command in a separate terminal, and start setup again.

## Configure

Use natural language at any time. For example:

- "Use the female English voice."
- "Change Voice Notify to male Japanese."
- "Use the female Russian voice."
- "Change Voice Notify to male Simplified Chinese."
- "여성 한국어 음성으로 바꿔줘."
- "Mute Voice Notify."
- "Test the Stop notification."

Codex maps `female` or `male` and Korean/Hangul (`ko`), Japanese (`ja`),
English (`en`), Russian (`ru`), or Simplified Chinese (`zh-CN`) to the bundled
settings command. Because `zh-CN` is the only bundled Chinese variant, a
generic "Chinese" or "中文" request defaults to `zh-CN` (Simplified Chinese,
Mainland Mandarin). You can also run it manually from a clone:

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko --open-hooks
/bin/sh scripts/voice_notify_config.sh show
/bin/sh scripts/voice_notify_config.sh set --voice female --language ko
/bin/sh scripts/voice_notify_config.sh set --voice male --language en
/bin/sh scripts/voice_notify_config.sh set --voice female --language ru
/bin/sh scripts/voice_notify_config.sh set --voice male --language zh-CN
/bin/sh scripts/voice_notify_config.sh test --event Stop
/bin/sh scripts/voice_notify_config.sh mute
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko -OpenHooks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

Defaults are `female`, `ko`, a 450 ms minimum interval, and eight events
enabled. `PreToolUse` and `PostToolUse` remain available but default to off to
avoid noisy per-tool notifications. `PermissionRequest` only plays when Codex
actually asks for permission.

## Troubleshooting

- If `/hooks` is unrecognized, update Codex CLI to `0.145.0` or newer and start
  setup again.
- If PowerShell blocks `codex.ps1` or `npm.ps1`, use `codex.cmd` or `npm.cmd`.
  The bundled Windows settings commands use process-local
  `-ExecutionPolicy Bypass` and do not change the system execution policy.
- If the test sound works but lifecycle notifications do not, review the hook
  in `/hooks`, trust it, and fully restart Codex.

## Compatibility

Version 0.1.5 supports macOS and Windows with system-provided audio and
scripting components. macOS does not require Python or Xcode Command Line
Tools. Guided hook setup requires Codex CLI `0.145.0` or newer. Linux is not yet
supported.

## Licensing

Source code is MIT licensed. WAV files under `assets/audio/` are excluded from
the MIT license and use the separate terms in [ASSET_LICENSE.md](ASSET_LICENSE.md).
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for generation provenance.
Most of the male notification set was built with Fish Audio and is subject to
the non-commercial asset boundary described there. Two Korean subagent files
were regenerated with Qwen Base to match the current wording.
