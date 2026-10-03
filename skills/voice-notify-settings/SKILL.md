---
name: voice-notify-settings
description: Set up, configure, diagnose, test, mute, or unmute private offline Voice Notify alerts for Codex lifecycle events on macOS, Windows, or Linux. Use for first-time setup, alerts when Codex needs attention or finishes, compatibility checks, review and consent-based approval of this plugin's exact hooks, voice and language selection, event toggles, and timing. Do not use for general TTS or narration, transcription, cloud notifications, arbitrary OS audio automation, screenshot action extraction, silent installation, or hook-trust bypass.
---

# Voice Notify settings

Use only the bundled settings scripts and review helpers. Never read prompts,
transcripts, or account credentials, and leave unrelated hooks and notification
settings unchanged.

Resolve the plugin root from this installed `SKILL.md` path: the skill directory
is `skills/voice-notify-settings`, so the root is two directories above it. Use
that verified absolute path. Do not assume `PLUGIN_ROOT` exists outside a hook
process, and do not use a root from an unrelated environment variable or an
unverified user prompt.

Available values:

- Voice: `female` or `male`
- Language: `ko`, `ja`, `en`, `ru`, or `zh-CN`
- Events: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
  `PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`,
  `SubagentStop`, and `Stop`

Map natural-language choices directly. 한국어, 한글, Korean map to `ko`;
일본어, 日本語, Japanese to `ja`; 영어, English to `en`; 러시아어, русский,
Russian to `ru`; 중국어, 중국어 간체, 간체중국어, 中文, 简体中文, Simplified
Chinese to `zh-CN`. A generic Chinese request selects the only bundled Chinese
variant, `zh-CN` (Simplified Chinese, Mainland Mandarin). Preserve confirmed
existing preferences and explicit choices. Raw script defaults remain
`female/ko`; they are not a requirement for the assistant's initial suggestion.

## First-time setup

Read [references/setup-guides.json](references/setup-guides.json) from this
installed skill directory before guiding initial setup. Use the guide matching
the user's current conversation language, not the operating-system locale. It
provides localized greetings, five spoken-language choices, female/male labels,
consent wording, and a hearing-confirmation question. Reply in the user's actual
language. For a language outside the five guides, translate the guidance into
that language while clearly keeping the bundled audio choices limited to
`ko`, `en`, `ja`, `ru`, and `zh-CN`; do not claim new audio-language support.

Briefly show all five audio-language options and both voices in the user's
language. The guide language and chosen audio language are independent. Keep
explicit choices or previously confirmed saved preferences. Only if a necessary
choice is unspecified, ask one concise combined preference question; do not
re-ask a known choice. For a new setup without saved preferences, suggest
`female` and the user's supported spoken language; if their language is not
bundled, suggest `ko` and let them choose from the five. This assistant
suggestion does not change the raw `female/ko` defaults. An explicit request for
one option must not silently reset another saved option.

Native diagnostic JSON, command names, and `approvalDigest` are internal
technical output. Explain relevant findings, the exact permission scope, and
next steps in the user's language; do not paste raw diagnostics as the setup
experience. Display the exact hook commands when reviewing approval, and keep
private paths and receipts out of public documents or support uploads.

The primary user flow is one natural-language setup request, followed by one
informed approval for the exact reviewed hooks. Do useful preparation before
requesting approval; do not ask again if the user already approved these exact
commands and their current review fingerprint.

1. Resolve the exact Codex CLI to use. On macOS/Linux, inspect `which -a codex`;
   on Windows, inspect `Get-Command codex.cmd, codex.exe, codex -All`. Verify the
   canonical selected path with `--version`. If multiple installations are
   ambiguous, ask which to use before updating or approving anything.
2. Run bundled `doctor` with that verified CLI path. This is read-only: it
   checks compatibility, audio availability, and preferences without playing
   sound or changing hook approval. CLI `0.145.0` or newer is required; a current
   prerelease suffix is accepted. An app update and a separately installed CLI
   update can differ.
3. Run `setup` with the requested voice/language and selected CLI. It saves
   preferences and tests the local `Stop` WAV. Confirm the sound was audible.
   Do not infer audible playback merely from a zero exit code.
4. Run `review-hooks`. Show the user's exact Voice Notify commands, events,
   permission scope, and returned `approvalDigest`. Explain that approval lets
   those local commands run for selected Codex lifecycle events. Local app-server
   inspection may see hook metadata; only this installed plugin's validated
   commands may be selected for approval. Do not expose unrelated metadata.
5. Obtain explicit consent for those reviewed commands. A general install/setup
   request does not itself authorize hook trust. Do not fabricate an
   `approvalDigest`, reuse one after a package/command change, or request approval
   for unseen commands.
6. Only after that consent, run `approve-hooks --approve <approvalDigest>`
   (`-Approve` on Windows) with the same verified CLI. The helper re-lists the
   hooks and rejects a changed digest. A mismatch requires a fresh review and
   consent for changed commands. Keep the receipt local.
7. Fully close and relaunch the relevant Codex process, show the effective
   settings, and confirm one enabled real lifecycle event was heard. Report
   separately whether settings, hook approval, test audio, and lifecycle audio
   have been verified. Setup is complete only when all four are verified.

macOS (replace the synthetic example paths with resolved installed paths):

```bash
SKILL_DIR="/path/to/plugin/skills/voice-notify-settings"
PLUGIN_ROOT="$(cd "${SKILL_DIR}/../.." && pwd)"
CODEX_BIN="/path/to/verified/codex"
SETTINGS_SCRIPT="${PLUGIN_ROOT}/scripts/voice_notify_config.sh"
/bin/sh "${SETTINGS_SCRIPT}" doctor --codex-command "${CODEX_BIN}"
/bin/sh "${SETTINGS_SCRIPT}" setup --voice female --language ko --codex-command "${CODEX_BIN}"
/bin/sh "${SETTINGS_SCRIPT}" review-hooks --codex-command "${CODEX_BIN}"
# Only after consent for the returned current approvalDigest:
/bin/sh "${SETTINGS_SCRIPT}" approve-hooks --approve "<approvalDigest>" --codex-command "${CODEX_BIN}"
/bin/sh "${SETTINGS_SCRIPT}" show
```

Windows:

```powershell
$SkillDir = "C:\path\to\plugin\skills\voice-notify-settings"
$PluginRoot = [IO.Path]::GetFullPath((Join-Path $SkillDir "..\.."))
$CodexPath = "C:\path\to\verified\codex.cmd"
$SettingsScript = Join-Path $PluginRoot "scripts\voice_notify_config.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript doctor -CodexCommand $CodexPath
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript setup -Voice female -Language ko -CodexCommand $CodexPath
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript review-hooks -CodexCommand $CodexPath
# Only after consent for the returned current approvalDigest:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript approve-hooks -Approve "<approvalDigest>" -CodexCommand $CodexPath
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript show
```

Linux:

```bash
SKILL_DIR="/path/to/plugin/skills/voice-notify-settings"
PLUGIN_ROOT="$(cd "${SKILL_DIR}/../.." && pwd)"
CODEX_BIN="/path/to/verified/codex"
SETTINGS_SCRIPT="${PLUGIN_ROOT}/scripts/voice_notify_config.py"
python3 "${SETTINGS_SCRIPT}" doctor --codex-command "${CODEX_BIN}"
python3 "${SETTINGS_SCRIPT}" setup --voice female --language ko --codex-command "${CODEX_BIN}"
python3 "${SETTINGS_SCRIPT}" review-hooks --codex-command "${CODEX_BIN}"
# Only after consent for the returned current approvalDigest:
python3 "${SETTINGS_SCRIPT}" approve-hooks --approve "<approvalDigest>" --codex-command "${CODEX_BIN}"
python3 "${SETTINGS_SCRIPT}" show
```

Check each command's exit status and stop dependent steps on failure. Use the
requested voice and language rather than overwriting them with example defaults.
macOS playback, settings, and approval use native shell and `osascript` JXA;
Windows uses native PowerShell. Linux uses Python 3's standard library and an
installed `pw-play`, `paplay`, `aplay`, or `ffplay`. Never install packages
implicitly. Headless, SSH, container, and WSL sessions may lack audible output.

The approval helper uses the same official local app-server approval mechanism
as Codex's [`/hooks` UI](https://github.com/openai/codex/blob/main/codex-rs/tui/src/hooks_rpc.rs):
list hooks, then `config/batchWrite` to upsert only the reviewed plugin hook
hashes into `hooks.state`. This is not permission to edit the trust store files
directly or approve another plugin. Never use
`--dangerously-bypass-hook-trust`.

If that interface is unavailable, use `setup --open-hooks` on macOS/Linux or
`setup -OpenHooks` on Windows. The fallback opens a new visible terminal and
starts the verified Codex CLI; the user enters `/hooks`, reviews, and explicitly
trusts the commands. If launching fails or the host is headless, guide the user
to start the selected CLI manually. Do not silently drive the review UI. Fully
close and relaunch Codex afterward before checking a real event.

The bundled scripts do not update Codex. Only when the user explicitly
requests a CLI update, establish installation provenance and update the selected
installation:

- npm: verify `npm list -g --depth=0 @openai/codex` and that the selected CLI is
  under the canonical `npm prefix -g`; use `npm install -g @openai/codex@latest`
  (`npm.cmd` on Windows).
- Homebrew: verify `brew list --cask codex` and that the CLI is under the canonical
  `brew --caskroom codex`; use `brew upgrade --cask codex`.
- Desktop-bundled or unknown installations: use that installation's supported
  update route; do not replace it with npm/Homebrew or another executable.

Verify the same selected path afterward. If it is in use, tell the user to close
that CLI before updating. Do not change system execution policy.

## Regular settings

Use the matching bundled settings script at the resolved plugin root.

macOS:

```bash
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" show
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice female --language ko
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice male --language ru
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice female --language zh-CN
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" test --event Stop
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" mute
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" mute
```

Linux:

```bash
python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" show
python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" set --voice male --language en
python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" test --event Stop
python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" mute
```

After a change, report effective voice, language, and enabled state. Preferences
contain only notification options. Diagnostic output and review receipts stay
local; redact paths and unrelated metadata before sharing any support report.
