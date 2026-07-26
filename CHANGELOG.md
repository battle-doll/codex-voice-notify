# Changelog

## 0.1.3 - 2026-07-27

- Added guided first-time setup on macOS and Windows: save the selected voice
  and language, test local playback, verify Codex CLI support for `/hooks`, and
  open a visible terminal at the hook review step.
- Added a first-time setup prompt that explicitly authorizes a compatible Codex
  CLI update when required while preserving mandatory human hook trust.
- Added natural-language usage guidance for female or male voices in Korean,
  Japanese, and English.
- Replaced the macOS Python runtime dependency with native `/bin/sh`, `plutil`,
  `afplay`, and `osascript` tooling, so Python and Xcode Command Line Tools are
  no longer required.
- Updated Windows setup commands to avoid process-local PowerShell execution
  policy failures without changing the user's system policy.
- Kept all bundled audio assets unchanged from 0.1.2.

## 0.1.2 - 2026-07-27

- Removed an isolated trailing non-lexical vocalization from the approved
  female Korean `SubagentStart` notification without changing the spoken
  sentence, voice, or delivery.
- Rebuilt the audio manifest for the corrected asset; the other 59 bundled WAV
  files and notification defaults are unchanged.

## 0.1.1 - 2026-07-27

- Replaced the 30 bundled female notifications with the approved original
  warm-husky voice in Korean, Japanese, and English.
- Regenerated the ten English female notifications from the approved
  speaker-only English anchor for more natural English prosody and direct
  speech onset.
- Changed the Korean subagent wording from `보조 에이전트` to
  `서브 에이전트`.
- Disabled `PreToolUse` and `PostToolUse` playback by default on new installs
  while preserving both configurable lifecycle hooks.
- Documented the one-time hook review and the required full Codex restart.
- Expanded Qwen and Fish generation provenance and bundled the applicable Fish
  Audio Research License text.

## 0.1.0 - 2026-07-26

- Added ten Codex lifecycle voice notifications.
- Added two voice profiles in Korean, Japanese, and English.
- Added offline macOS playback, overlap prevention, and local settings.
- Added privacy, licensing, provenance, and submission documentation.
