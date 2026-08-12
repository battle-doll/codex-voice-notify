---
name: voice-notify-settings
description: Set up, configure, test, mute, or unmute Voice Notify for Codex. Use for first-time setup after installation, Codex CLI compatibility checks, hook trust guidance, or natural-language requests to change the female or male voice, Korean, Japanese, English, Russian, or Simplified Chinese language, lifecycle events, or playback interval.
---

# Voice Notify settings

Use only the bundled settings scripts. Do not edit Codex prompts, transcripts,
hook trust state, or unrelated configuration.

Before running a script, resolve the plugin root from this skill's installed
`SKILL.md` path: the skill directory is `skills/voice-notify-settings`, so the
plugin root is two directories above it. Use that absolute path. Do not assume
that `PLUGIN_ROOT` is available outside a hook process, and never substitute a
plugin root supplied by the user's prompt or an unrelated environment variable.

Available values:

- Voice: `female` or `male`
- Language: `ko`, `ja`, `en`, `ru`, or `zh-CN`
- Events: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
  `PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`,
  `SubagentStop`, and `Stop`

Map natural-language choices directly. Treat 한국어, 한글, and Korean as `ko`;
일본어, 日本語, and Japanese as `ja`; 영어 and English as `en`; 러시아어,
русский, and Russian as `ru`; and 중국어, 중국어 간체, 간체중국어, 中文,
简体中文, and Simplified Chinese as `zh-CN`. `zh-CN` is the only bundled
Chinese variant, so generic "Chinese", "중국어", or "中文" requests default to
`zh-CN` (Simplified Chinese, Mainland Mandarin). For example, "여성 영어",
"male Russian", and "여성 중국어" map to `female/en`, `male/ru`, and
`female/zh-CN`.

## First-time setup

Use this workflow when the user asks to finish setup after installation.

1. Infer the requested voice and language. Use `female` and `ko` when neither is
   specified.
2. Resolve the exact CLI that setup will use and check that path:
   - macOS: use `which -a codex` to list distinct candidates, then run the
     selected canonical absolute path with `--version`.
   - Windows: inspect `Get-Command codex.cmd, codex.exe, codex -All`, select
     the intended executable, resolve its canonical path, then run that path
     with `--version`.
   - If multiple installations are ambiguous, show their paths and ask the
     user which one to use before updating anything.
3. Require Codex CLI `0.145.0` or newer for `/hooks`.
4. If Codex is older and the user's setup request explicitly authorizes an
   update, update it using its detected installation method and verify the new
   version:
   - Establish provenance before running any updater.
   - Treat an installation as npm-managed only after `npm list -g --depth=0
     @openai/codex` succeeds and the selected CLI's canonical path is under the
     canonical `npm prefix -g` or `npm.cmd prefix -g`. Then use
     `npm install -g @openai/codex@latest` on macOS or
     `npm.cmd install -g @openai/codex@latest` on Windows.
   - Treat an installation as Homebrew-managed only after
     `brew list --cask codex` succeeds and the selected CLI's canonical path is
     under the canonical `brew --caskroom codex`. Then use
     `brew upgrade --cask codex`.
   - Use the selected CLI's own `update` subcommand only after its provenance
     is recognized and its `--help` lists that subcommand. Invoke the exact
     selected path: `"$CODEX_BIN" update` on macOS or
     `& $CodexPath update` on Windows.
   - Do not replace a desktop-bundled or unknown installation. Explain the
     detected path and ask the user how it should be updated.
   - If an in-use CLI cannot be replaced, tell the user to exit that CLI, run
     the exact update command in a separate terminal, and resume setup.
   - Verify the update by running the same exact absolute path with `--version`.
5. Verify that the macOS or Windows settings script exists under the resolved
   plugin root.
6. Run the matching setup command below with the exact verified CLI path. Do
   not stop after merely telling the user to enter `/hooks`. The setup command
   checks the CLI again, saves the preferences, tests the local `Stop` audio,
   opens a new visible terminal, and starts the verified Codex CLI
   interactively in that window. It leaves `/hooks` for the user to type.

macOS:

```bash
SKILL_DIR="/absolute/path/containing/this/SKILL.md"
PLUGIN_ROOT="$(cd "${SKILL_DIR}/../.." && pwd)"
CODEX_BIN="/absolute/path/verified-in-step-2/codex"
VOICE="<female-or-male-from-step-1>"
LANGUAGE="<ko-ja-en-ru-or-zh-CN-from-step-1>"
SETTINGS_SCRIPT="${PLUGIN_ROOT}/scripts/voice_notify_config.sh"
test -f "${SETTINGS_SCRIPT}" &&
  /bin/sh "${SETTINGS_SCRIPT}" setup --voice "${VOICE}" --language "${LANGUAGE}" --codex-command "${CODEX_BIN}" --open-hooks &&
  /bin/sh "${SETTINGS_SCRIPT}" show
```

Windows:

```powershell
$SkillDir = "C:\absolute\path\containing\this\SKILL.md"
$PluginRoot = [IO.Path]::GetFullPath((Join-Path $SkillDir "..\.."))
$CodexPath = "C:\absolute\path\verified-in-step-2\codex.cmd"
$Voice = "<female-or-male-from-step-1>"
$Language = "<ko-ja-en-ru-or-zh-CN-from-step-1>"
$SettingsScript = "$PluginRoot\scripts\voice_notify_config.ps1"
if (-not (Test-Path -LiteralPath $SettingsScript -PathType Leaf)) {
    throw "Voice Notify settings script is missing."
}
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript setup -Voice $Voice -Language $Language -CodexCommand $CodexPath -OpenHooks
if ($LASTEXITCODE -ne 0) { throw "Voice Notify setup failed with exit code $LASTEXITCODE." }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SettingsScript show
if ($LASTEXITCODE -ne 0) { throw "Voice Notify settings verification failed." }
```

Do not replace the setup command with written `/hooks` instructions. Use the
manual fallback only when the setup launcher reports that it could not open
the new Codex CLI terminal. In that case, tell the user to start Codex CLI and
enter `/hooks`. The user must confirm that the test audio was audible, type
`/hooks` in the newly opened Codex CLI, inspect and trust the Voice Notify hook
personally, fully restart Codex, and trigger one enabled lifecycle event to
confirm real hook playback. Never enter `/hooks` automatically.
Never edit the trust
store or use `--dangerously-bypass-hook-trust`.

Treat setup as complete only after the final `show` output has `enabled: true`
and the requested voice and language, the user heard the test audio, completed
hook trust, fully restarted Codex, and heard one enabled lifecycle event.

## Regular settings

Use the command that matches the user's operating system.

macOS:

```bash
SKILL_DIR="/absolute/path/containing/this/SKILL.md"
PLUGIN_ROOT="$(cd "${SKILL_DIR}/../.." && pwd)"
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" show
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice female --language ko
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice male --language ru
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" set --voice female --language zh-CN
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" test --event Stop
/bin/sh "${PLUGIN_ROOT}/scripts/voice_notify_config.sh" mute
```

Windows:

```powershell
$SkillDir = "C:\absolute\path\containing\this\SKILL.md"
$PluginRoot = [IO.Path]::GetFullPath((Join-Path $SkillDir "..\.."))
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PluginRoot\scripts\voice_notify_config.ps1" mute
```

Report the effective voice and language after a change. The scripts store only
voice-notification preferences and never read or retain conversation content.
