# Public plugin submission notes

Status: version update package prepared for submission.

- Slug: `codex-voice-notify`
- Display name: `Voice Notify for Codex`
- Developer: `battle-doll`
- Category: `Developer Tools`
- Version: `0.1.4`
- Platforms: macOS and Windows
- Authentication: none
- Runtime network access: none
- Optional setup network access: only an explicitly user-authorized npm or
  Homebrew Codex CLI update
- Data collection: none
- Positive tests: 5
- Negative tests: 3
- Release note: Guided first-time setup now explicitly opens a new terminal
  window and starts the exact verified Codex CLI there instead of merely
  displaying a `/hooks` instruction. The user still enters `/hooks`, reviews
  the bundled command, and grants hook trust personally. macOS and Windows
  launcher validation was strengthened. Audio assets and notification defaults
  are unchanged.
- Host update boundary: bundled scripts only inspect the installed Codex
  version. The skill updates a recognized npm or Homebrew installation only
  when the user's setup prompt explicitly requests it.

Required human steps in the OpenAI submission portal:

1. Complete developer or business identity verification.
2. Review the uploaded package and policy declarations.
3. Confirm sufficient audio redistribution rights.
4. Approve the legal attestations and final submission.
