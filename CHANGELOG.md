# Changelog

## 0.2.0 - 2026-10-03

- Accept current Codex prerelease version strings during compatibility checks.
- Add read-only `doctor` and exact `review-hooks` / `approve-hooks` setup with
  a current `approvalDigest`, explicit informed consent, and Codex's supported
  local app-server approval API. Reject changed commands instead of bypassing
  review; retain visible manual `/hooks` fallback when the API is unavailable.
- Simplify first-time setup to one guided request and one reviewed hook approval.
- Guide setup, five audio-language options, female/male choices, consent, and
  hearing confirmation in the user's language while preserving saved choices.
- Declare `extensions.com.openai.onboardingSkill` and a public support URL so
  supporting hosts can connect the packaged first-time guide. Automatic host
  invocation remains unverified.
- Add Linux playback using Python 3's standard library and the first installed
  `pw-play`, `paplay`, `aplay`, or `ffplay`; do not install audio packages.
- Keep native macOS and Windows playback/settings and all 100 WAV bytes,
  notification defaults, and audio licensing unchanged.
- Maintain English, Korean, Japanese, Simplified Chinese, and Russian README
  parity; document headless limitations, privacy-safe diagnostics, and the
  current documented restriction on submitting lifecycle-hook ZIPs.
- Prepare a separate update candidate; do not claim public submission,
  approval, or publication from package/test success.

## 0.1.7 - 2026-08-29

- Clarified direct and indirect selection language for private, offline Codex
  lifecycle alerts while making non-selection boundaries explicit for general
  TTS, narration, transcription, cloud notifications, arbitrary OS audio,
  screenshot action extraction, silent installation, and hook-trust bypass.
- Added equivalent first-screen use guidance to all five READMEs and recorded
  the verified Published, GLOBAL/AVAILABLE, and UNLISTED directory state.
- Added a bilingual discovery golden set with 10 direct, 20 indirect, and 20
  negative cases plus deterministic schema validation.
- Kept all 100 WAV assets, runtime behavior, permissions, settings defaults,
  privacy boundaries, and human hook-trust requirements unchanged from 0.1.6.

## 0.1.6 - 2026-08-15

- Added complete Japanese, Simplified Chinese, and Russian READMEs and refreshed
  the English and Korean READMEs to the same seven-section product contract.
- Added one identical five-language switcher to every README and kept setup,
  hook trust, privacy, compatibility, and licensing guidance in parity.
- Included all five localized READMEs in the deterministic release artifact and
  added package validation for language links, version anchors, commands, and
  required product boundaries.
- Kept the 100 WAV assets, five spoken languages, runtime behavior, and default
  settings unchanged from 0.1.5.

## 0.1.5 - 2026-08-13

- Added Russian (`ru`) and Simplified Chinese (`zh-CN`) notification phrases
  for both bundled voice profiles and all ten lifecycle events.
- Expanded the release from 60 to 100 WAV files while preserving the existing
  female Korean defaults and event settings.
- Updated macOS and Windows playback, settings, validation, documentation, and
  natural-language evaluation coverage for all five supported languages.

## 0.1.4 - 2026-07-28

- Clarified and hardened guided setup so it opens a new terminal and starts the
  verified Codex CLI instead of merely displaying a `/hooks` instruction.
- Preserved mandatory human `/hooks` entry, review, and hook trust.
- Strengthened release checks for the exact Codex CLI terminal handoff on
  macOS and Windows.
- Kept audio assets and notification defaults unchanged from 0.1.3.

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
