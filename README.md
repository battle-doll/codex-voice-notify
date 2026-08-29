# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Hear a private, local voice when Codex needs attention or finishes work. Voice
Notify for Codex is for macOS and Windows users who miss permission prompts,
subagent changes, context compaction, or task completion while focused elsewhere.

### Use

- Open [Voice Notify for Codex in ChatGPT](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83), or use the GitHub install commands below.
- Complete guided setup, personally review `/hooks`, then choose a voice,
  language, lifecycle events, or playback interval. You can test, mute, and
  unmute the local alerts at any time.

### Try it

- `Tell me aloud when Codex needs permission or finishes, using the female English voice.`
- `Test the local Stop alert, then mute Voice Notify.`
- `Codex 작업이 끝날 때 오프라인 한국어 음성으로 알려줘.`

### Key boundaries

- Runtime playback is offline and never retains or sends conversation content.
- The plugin handles only Codex lifecycle voice setup and settings. It is not
  for general TTS or narration, speech transcription, cloud notifications,
  arbitrary OS audio automation, or screenshot action extraction.
- Setup never installs silently or bypasses hook trust. The user reviews and
  trusts the bundled hook personally; unrelated notification settings remain unchanged.

Verified on 2026-08-29: OpenAI Platform shows **Published**; the latest remote catalog snapshot shows **GLOBAL/AVAILABLE** with discoverability **UNLISTED**. `UNLISTED` does not mean listed or searchable in the public directory. Repository package 0.1.7 is an update candidate; this verified state describes the existing remote entry and does not claim that 0.1.7 has been reviewed or published.

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

Version 0.1.7 bundles 100 WAV files: ten lifecycle events for each combination
of two voice profiles and five languages. This patch clarifies discovery
metadata and equivalent first-screen guidance across all five READMEs; audio
assets and runtime behavior are unchanged from 0.1.6.

It uses `/bin/sh`, `plutil`, `afplay`, and `osascript` already included with
macOS, or Windows PowerShell and `System.Media.SoundPlayer`. It does not require
Python or Xcode Command Line Tools. It has no network code or telemetry and
never stores prompts, messages, tool input, or tool output. Playback is
non-blocking, and a local lock plus a short cooldown prevents overlapping clips.

### Interactive code ontology

[Open this repository's interactive code ontology](https://rawcdn.githack.com/battle-doll/codex-voice-notify/ce42d10e88fc490271bea2c123a611bfa3d12b13/codex-voice-notify-code-ontology.html),
generated from Voice Notify `0.1.6` with
[Code Ontology Companion](https://github.com/battle-doll/code-ontology-companion),
or [inspect the published HTML in this repository](https://github.com/battle-doll/codex-voice-notify/blob/code-ontology-showcase/codex-voice-notify-code-ontology.html).

The self-contained snapshot maps six Python files into 417 nodes and 769
relationships, with zero parse warnings and extraction evidence plus source
spans on every relationship. It supports symbol search, caller and dependency
inspection, 2D structure and 3D constellation views, and per-relationship rule,
basis, runtime-status, source-span, and limitation details.

This is static-analysis evidence, not runtime proof. The production Windows and
macOS hook entry points are PowerShell and POSIX shell and therefore fall
outside this Python snapshot's adapter coverage. Publication was explicitly
authorized. The preview uses raw.githack only as an HTML content-type bridge;
the workbench itself has no runtime CDN or network dependency.

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

Version 0.1.7 supports macOS and Windows with system-provided audio and
scripting components. macOS does not require Python or Xcode Command Line
Tools. Guided hook setup requires Codex CLI `0.145.0` or newer. Linux is not yet
supported.

## Licensing

Source code is MIT licensed. All WAV files under `assets/audio/` are excluded
from the MIT license. Under the limited grant in
[ASSET_LICENSE.md](ASSET_LICENSE.md), they may be used, copied, and redistributed
only without modification, only as part of an unmodified, free copy of Voice
Notify for Codex, and only for personal, non-commercial notification playback.

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) records generation provenance
only. Most of the male notification set was built with Fish Audio, and two
Korean subagent files were regenerated with Qwen Base to match the current
wording. These provenance details do not change the voice-asset terms.
