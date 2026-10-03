# Privacy Policy

Effective date: October 3, 2026

Voice Notify for Codex performs local audio playback and local setup only.

- Runtime playback makes no network requests and collects no telemetry or analytics.
- It does not inspect, persist, or transmit prompts, messages, transcripts,
  tool inputs, or tool outputs. It does not request account data or credentials,
  or collect personal information.
- The runtime hook reads only the `hook_event_name` field needed to select a
  bundled WAV, and does not retain the surrounding event payload.
- Local preferences contain only enabled state, voice, language, event toggles,
  and playback interval. Runtime state contains a playback timestamp and lock
  information to prevent overlapping playback.
- Read-only diagnostics inspect local compatibility, executable/audio
  availability, and notification preferences. Local output may contain paths.
- Hook review/approval uses the selected Codex CLI's local app-server interface
  to inspect hook metadata and approve only the exact reviewed Voice Notify
  hooks after informed user consent. Review output can include local commands,
  paths, hashes, and approval state; it stays local and is not telemetry.
- The helper changes approval through Codex's supported local interface. It does
  not edit trust-store files directly, approve unrelated hooks, or bypass review.
- Scripts do not install dependencies or update Codex. A separately authorized
  npm/Homebrew CLI update is handled by Codex with the user's permission and may
  contact that package manager's services.

Support reports are optional and user-controlled. Share a minimal, redacted
reproduction rather than raw diagnostic output, logs, settings, or receipts.
The public developer identity is `battle-doll`; no private user/host details are
required in the package or public documentation.

Questions can be filed through
[GitHub Issues](https://github.com/battle-doll/codex-voice-notify/issues).
