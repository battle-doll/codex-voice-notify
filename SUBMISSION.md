# Public plugin submission notes

## Current publication state

Verified on 2026-08-29: OpenAI Platform shows **Published**; the latest remote catalog snapshot shows **GLOBAL/AVAILABLE** with discoverability **UNLISTED**.

- Directory URL: <https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83>
- `UNLISTED` does not mean listed or searchable in the public directory.
- Version 0.1.7 in this repository is an update candidate. The verified state
  above describes the existing remote entry and does not claim that 0.1.7 has
  been uploaded, reviewed, approved, or published.

## Update package

- Slug: `codex-voice-notify`
- Display name: `Voice Notify for Codex`
- Developer: `battle-doll`
- Category: `Developer Tools`
- Version: `0.1.7`
- Platforms: macOS and Windows
- Authentication: none
- Runtime network access: none
- Optional setup network access: only an explicitly user-authorized npm or
  Homebrew Codex CLI update
- Data collection: none
- Positive tests: 7
- Negative tests: 3
- Discovery golden set: 10 direct, 20 indirect, and 20 negative plugin/skill
  selection cases in English and Korean
- Release note: Clarified when to select Voice Notify for private, offline
  Codex lifecycle alerts and when not to select it for general TTS, narration,
  transcription, cloud notifications, arbitrary OS audio automation,
  screenshot action extraction, silent installation, or hook-trust bypass.
  Added equivalent first-screen guidance in five languages and deterministic
  discovery-eval validation. All 100 WAV assets, runtime behavior, defaults,
  permissions, privacy boundaries, and human hook trust remain unchanged from
  0.1.6.
- Host update boundary: bundled scripts only inspect the installed Codex
  version. The skill updates a recognized npm or Homebrew installation only
  when the user's setup prompt explicitly requests it.

The existing 0.1.6 release artifact must not be regenerated, replaced, or
relabelled. A 0.1.7 archive is a distinct update artifact and must pass the
repository's exact-file, audio-manifest, checksum, and deterministic-build
checks before upload.

## Required human steps in the OpenAI submission portal

1. Complete developer or business identity verification.
2. Open the existing plugin and create an update draft.
3. Review the uploaded 0.1.7 package and policy declarations.
4. Confirm sufficient audio redistribution rights.
5. Approve the legal attestations and submit the update for review.
6. Treat upload, review, approval, publication, and listed/searchable directory
   placement as distinct states; verify the final result through the direct URL.
