# Public plugin submission notes

Status: version update package prepared for submission.

- Slug: `codex-voice-notify`
- Display name: `Voice Notify for Codex`
- Developer: `battle-doll`
- Category: `Developer Tools`
- Version: `0.1.3`
- Platforms: macOS and Windows
- Authentication: none
- Runtime network access: none
- Optional setup network access: only an explicitly user-authorized npm or
  Homebrew Codex CLI update
- Data collection: none
- Positive tests: 5
- Negative tests: 3
- Release note: Added guided first-time setup on macOS and Windows with Codex
  CLI compatibility checks, optional user-authorized npm or Homebrew updates,
  local playback verification, natural-language voice and language controls,
  and a visible handoff to mandatory `/hooks` review. macOS playback and
  settings now use system `/bin/sh` tools and no longer require Python or Xcode
  Command Line Tools. Windows uses a process-local execution-policy override
  without changing system policy. Audio assets are unchanged.
- Host update boundary: bundled scripts only inspect the installed Codex
  version. The skill updates a recognized npm or Homebrew installation only
  when the user's setup prompt explicitly requests it.

Required human steps in the OpenAI submission portal:

1. Complete developer or business identity verification.
2. Review the uploaded package and policy declarations.
3. Confirm sufficient audio redistribution rights.
4. Approve the legal attestations and final submission.
