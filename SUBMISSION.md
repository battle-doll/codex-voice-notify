# Public plugin submission notes

Status: version update package prepared for submission.

- Slug: `codex-voice-notify`
- Display name: `Voice Notify for Codex`
- Developer: `battle-doll`
- Category: `Developer Tools`
- Version: `0.1.6`
- Platforms: macOS and Windows
- Authentication: none
- Runtime network access: none
- Optional setup network access: only an explicitly user-authorized npm or
  Homebrew Codex CLI update
- Data collection: none
- Positive tests: 7
- Negative tests: 3
- Release note: Added complete English, Korean, Japanese, Simplified Chinese,
  and Russian READMEs with a shared language switcher and parity across setup,
  configuration, troubleshooting, compatibility, privacy, and licensing
  guidance. All five READMEs are included and validated in the deterministic
  package. The 100 WAV assets, runtime behavior, and defaults are unchanged from
  0.1.5.
- Host update boundary: bundled scripts only inspect the installed Codex
  version. The skill updates a recognized npm or Homebrew installation only
  when the user's setup prompt explicitly requests it.

Required human steps in the OpenAI submission portal:

1. Complete developer or business identity verification.
2. Review the uploaded package and policy declarations.
3. Confirm sufficient audio redistribution rights.
4. Approve the legal attestations and final submission.
