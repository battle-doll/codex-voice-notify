# Security

Report security issues privately through the GitHub repository's security
advisory feature.

The plugin has no network code and no dependency installation. The hook accepts
Codex JSON on standard input, selects an audio file from fixed allowlists, and
discards the input without logging it. Users must inspect and trust the hook in
`/hooks`; do not bypass that review.
