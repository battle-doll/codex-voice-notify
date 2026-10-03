# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Hear a private, local voice when Codex needs attention or finishes work.
Voice Notify for Codex supports macOS, Windows, and Linux.

### Use

- Install from GitHub, then ask: `Set up Voice Notify with the female Korean voice. Explain the hooks and ask me before approving them.`
- Codex checks compatibility and audio, saves your preferences, and presents the exact Voice Notify hook commands. After your informed approval, it can apply that approval through Codex's supported local interface.
- Choose a voice, language, lifecycle events, or playback interval. Test, mute, and unmute at any time.

### Try it

- `Tell me aloud when Codex needs permission or finishes, using the female English voice.`
- `Check why Voice Notify stopped after my Codex update.`
- `Test the local Stop alert, then mute Voice Notify.`

### Key boundaries

- Playback is offline and never retains or sends conversation content.
- This plugin handles Codex lifecycle voice setup and settings, not general TTS, narration, transcription, cloud notifications, arbitrary OS audio automation, or screenshot action extraction.
- Hook approval requires your review and consent. Only the reviewed Voice Notify hooks are approved; unrelated hooks and notification settings remain unchanged.

Checked on 2026-10-03: OpenAI Platform shows the existing 0.1.7 entry as **Published**. Version 0.2.0 has not been submitted. Current directory discoverability is unverified. Historical record — Verified on 2026-08-29: the catalog reported **GLOBAL/AVAILABLE** and **UNLISTED**; this old snapshot does not establish current listing or searchability. [Existing entry](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83).

As checked on 2026-10-03, [OpenAI's submission documentation](https://developers.openai.com/plugins/deploy/submission) excludes lifecycle-hook ZIPs from submission. Version 0.2.0 is a prepared update candidate; public submission is on hold. See [SUBMISSION.md](SUBMISSION.md).

This is an independent plugin with MIT-licensed source code and separately licensed voice assets. It is not affiliated with or endorsed by OpenAI.

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

Version 0.2.0 bundles 100 WAV files: two voice profiles, five languages, and ten lifecycle events. Audio assets and defaults are unchanged. This update accepts current Codex prerelease version strings, adds read-only diagnostics and consent-based hook setup, and adds Linux playback.

macOS uses its bundled `/bin/sh`, `plutil`, `afplay`, and `osascript` for regular playback and settings; Python and Xcode Command Line Tools are unnecessary for those actions. Windows uses PowerShell and `System.Media.SoundPlayer`. Linux uses Python 3's standard library and the first installed player from `pw-play`, `paplay`, `aplay`, or `ffplay`. The plugin installs no audio packages. Runtime playback has no network code or telemetry and never stores prompts, messages, tool input, or tool output. A local lock and cooldown prevent overlapping clips.

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

This is a historical 0.1.6 snapshot; it has not been regenerated for 0.2.0 or the Linux and hook-approval changes.

## Install from GitHub

macOS / Linux:

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

Codex guides setup in your conversation language and shows five audio languages — Korean, English, Japanese, Russian, and Simplified Chinese — plus female and male voices. Spoken language is a separate choice from the guide language. Existing or explicit choices are kept; only missing preferences are asked. For a new setup, the suggested voice is female in your supported language (or Korean if your language has no bundled audio). Raw script defaults remain `female/ko`. Hook review, consent, and hearing confirmation are explained in your language.

After installation, select **Finish first-time setup** or ask:

> Set up Voice Notify with the female Korean voice. Explain the hooks and ask me before approving them.

The guided workflow is repeatable:

1. Run read-only `doctor` to check the selected Codex CLI, version, audio player, and settings. Codex CLI `0.145.0` or newer is required; current prerelease suffixes are recognized.
2. Save your chosen voice and language, and play the local `Stop` test. Confirm that you heard it.
3. Run `review-hooks` and show the exact Voice Notify commands, scope, and `approvalDigest`. Ask for approval of those reviewed commands.
4. After your explicit approval, run `approve-hooks` with that `approvalDigest`. Codex's supported local app-server interface applies only the exact reviewed Voice Notify approval. Changed commands require a new review; no trust store is edited directly and no trust bypass is used.
5. Fully close and relaunch Codex, then hear one enabled lifecycle event. A successful settings test or approval receipt alone does not prove lifecycle playback.

If the approval interface is unavailable, use `setup --open-hooks` on macOS/Linux or `setup -OpenHooks` on Windows to open a visible Codex CLI terminal. In it, enter `/hooks`, inspect the bundled commands, and explicitly trust them. Then fully restart Codex before testing lifecycle events. On a headless system or without a terminal launcher, start the selected CLI yourself and enter `/hooks`.

The scripts never update Codex or install dependencies silently. If the CLI is too old, Codex may update a recognized npm or Homebrew installation only when you explicitly authorize that separate update. Desktop-bundled and unknown installations use their own supported update path. If an executable is in use, close that CLI before updating.

## Configure

Use natural language: “Use the female English voice,” “Change Voice Notify to male Japanese,” “Use the female Russian voice,” “Use male Simplified Chinese,” or “Mute Voice Notify.”

Codex maps `female` or `male` and Korean/Hangul (`ko`), Japanese (`ja`), English (`en`), Russian (`ru`), or Simplified Chinese (`zh-CN`) to the bundled settings. Generic “Chinese” or “中文” defaults to the only bundled Chinese variant, `zh-CN` (Simplified Chinese, Mainland Mandarin). Manual commands from a clone:

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh doctor
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko
/bin/sh scripts/voice_notify_config.sh review-hooks
# After explicit consent, replace <approvalDigest> with the returned current digest:
/bin/sh scripts/voice_notify_config.sh approve-hooks --approve "<approvalDigest>"
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 doctor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 review-hooks
# After explicit consent, replace <approvalDigest> with the returned current digest:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 approve-hooks -Approve "<approvalDigest>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

Linux:

```bash
python3 scripts/voice_notify_config.py doctor
python3 scripts/voice_notify_config.py setup --voice female --language ko
python3 scripts/voice_notify_config.py review-hooks
# After explicit consent, replace <approvalDigest> with the returned current digest:
python3 scripts/voice_notify_config.py approve-hooks --approve "<approvalDigest>"
python3 scripts/voice_notify_config.py show
python3 scripts/voice_notify_config.py set --voice male --language en
python3 scripts/voice_notify_config.py test --event Stop
python3 scripts/voice_notify_config.py mute
```

Defaults are `female`, `ko`, a 450 ms minimum interval, and eight events enabled. `PreToolUse` and `PostToolUse` are available but default to off. `PermissionRequest` plays only when Codex actually requests permission.

## Troubleshooting

- Run `doctor` first. Diagnostics do not change preferences, approve hooks, or play audio; local output can contain paths, so redact it before sharing.
- If `/hooks` is unavailable, check the selected CLI and update it with your authorization. A desktop app update and a separately installed CLI update can differ.
- If test audio works but lifecycle alerts do not, review hook approval, fully close and relaunch the relevant Codex process, and test a real enabled event.
- If PowerShell blocks `codex.ps1` or `npm.ps1`, use `codex.cmd` or `npm.cmd`. `-ExecutionPolicy Bypass` applies only to the launched settings process, not the system policy.
- Linux requires Python 3 and an installed supported audio player with access to an audio device/server. SSH, containers, WSL, and headless sessions may have no audible output even when a player exists. No packages are installed automatically.

## Compatibility

Version 0.2.0 supports macOS, Windows, and Linux. macOS regular playback/settings stay Python-free; Windows uses native PowerShell; Linux requires Python 3 and one supported local player. Hook approval automation uses native macOS `osascript` JXA, native Windows PowerShell, or Linux Python 3, and needs the selected Codex CLI's supported local app-server interface; use manual `/hooks` review if unavailable. Codex CLI `0.145.0` or newer is required. Platform support does not imply that every desktop release, audio backend, or headless session has been audibly verified.

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
