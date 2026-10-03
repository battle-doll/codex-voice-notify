# Public plugin submission notes

## Current publication state

Checked on 2026-10-03: OpenAI Platform shows the existing **0.1.7** entry as
**Published**. This does not show that the prepared **0.2.0** package is uploaded,
reviewed, approved, or published. Current directory discoverability has not
been verified.

- [Existing plugin entry](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83)
- Historical record, Verified on 2026-08-29: the catalog reported
  **GLOBAL/AVAILABLE** and **UNLISTED**. `UNLISTED` did not mean searchable or
  listed in the public directory; this old snapshot is not a current check.
- As checked on 2026-10-03, [OpenAI's submission documentation](https://developers.openai.com/plugins/deploy/submission)
  says lifecycle-hook ZIPs cannot currently be submitted. Voice Notify uses
  lifecycle hooks, so current public submission is on hold. A valid local ZIP
  does not prove portal acceptance or review eligibility.

## Prepared update package

- Slug: `codex-voice-notify`
- Display name: `Voice Notify for Codex`
- Public developer: `battle-doll`
- Category: `Developer Tools`
- Version: `0.2.0`
- Platforms: macOS, Windows, Linux
- Spoken/documentation languages: Korean, Japanese, English, Russian,
  Simplified Chinese
- Authentication: none
- Runtime network access: none
- Local setup: compatibility/audio diagnostics and exact hook review; approval
  only after informed consent through Codex's supported local interface
- Optional setup network access: a separately authorized npm/Homebrew Codex
  CLI update performed by Codex, not silently by the bundled scripts
- Data collection: none
- Behavioral evaluation cases: 10 positive and 5 negative; discovery cases:
  10 direct, 20 indirect, and 20 negative (English/Korean)
- Release scope: recognize current Codex prerelease version strings, diagnose
  compatibility without changes, simplify first-time setup with reviewed exact
  hook approval, and add Linux playback. macOS and Windows use native tools;
  Linux uses Python 3 and an already installed supported audio player.
- Localized setup guides cover five languages and both voices, following the
  user's conversation language while preserving explicit or saved choices.
- Manifest onboarding: `extensions.com.openai.onboardingSkill` references
  `./skills/voice-notify-settings/SKILL.md`; supporting hosts can connect that
  initial guide. Automatic host invocation remains unverified.
- Public support URL: the existing repository `SUPPORT.md` page.
- All 100 WAV asset bytes, audio licensing, and notification defaults are
  unchanged. The historical 0.1.6 code-ontology showcase is not 0.2.0 evidence.

Retain existing release artifacts without overwriting or relabelling them. The
0.2.0 archive is distinct and must pass exact-file, audio-manifest, checksum,
privacy, multilingual documentation, and deterministic-build checks before
any upload. Report cross-platform automated tests and actual audible lifecycle
verification separately; dry-runs do not prove audible success on every OS.

## Privacy review before public upload

Include only intentional source, bundled approved assets, public documentation,
and `battle-doll` attribution. Exclude local usernames, absolute private paths,
hostnames, device/account identifiers, emails, credentials, tokens, settings,
review receipts, raw logs, chats, and screenshots of account/identity pages.
Use synthetic paths and data in examples and tests. Do not add a personal
identity document or private attestation to the release archive.

## Human submission boundary

Prepare the package, declarations, release notes, test evidence, and a reviewable
update draft only where the portal permits it. Stop before legal attestations
or **Submit for review**. Public submission needs separate explicit user
approval, and current documented lifecycle-hook restrictions may prevent even
an upload. Do not claim submission readiness at the portal when it rejects the
package; preserve its exact reason in a private, redacted handoff.

Identity verification, sufficient audio redistribution rights, legal
attestations, submission, review, publication, and public listing are distinct
steps. An existing Published entry is not proof that this update completed any
of them.
