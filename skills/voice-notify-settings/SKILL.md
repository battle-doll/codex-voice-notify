---
name: voice-notify-settings
description: Configure, test, mute, or unmute Voice Notify for Codex. Use when the user asks to change the notification voice, language, lifecycle events, playback interval, or to test local voice playback.
---

# Voice Notify settings

Use the bundled `scripts/voice_notify_config.py` command. Do not edit Codex prompts,
transcripts, or unrelated configuration.

Available values:

- Voice: `female` or `male`
- Language: `ko`, `ja`, or `en`
- Events: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
  `PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`,
  `SubagentStop`, and `Stop`

Use the command that matches the user's operating system.

macOS:

```bash
/usr/bin/python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" show
/usr/bin/python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" set --voice female --language ko
/usr/bin/python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" test --event Stop
/usr/bin/python3 "${PLUGIN_ROOT}/scripts/voice_notify_config.py" mute
```

Windows:

```powershell
powershell.exe -NoProfile -File "$env:PLUGIN_ROOT\scripts\voice_notify_config.ps1" show
powershell.exe -NoProfile -File "$env:PLUGIN_ROOT\scripts\voice_notify_config.ps1" set -Voice female -Language ko
powershell.exe -NoProfile -File "$env:PLUGIN_ROOT\scripts\voice_notify_config.ps1" test -Event Stop
powershell.exe -NoProfile -File "$env:PLUGIN_ROOT\scripts\voice_notify_config.ps1" mute
```

After installation, remind the user that plugin hooks require one-time review and
trust in `/hooks`. Never bypass hook trust on the user's behalf. The script stores
only voice-notification preferences. It never reads or retains conversation content.
