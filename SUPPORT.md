# Support

Use GitHub Issues for reproducible bugs and feature requests:

https://github.com/battle-doll/codex-voice-notify/issues

Include the Codex version, macOS version, selected voice and language, event
name, and whether the hook is trusted. Never include prompts, transcripts,
credentials, or private tool payloads.

If a bundled WAV plays through the settings test but a real lifecycle event is
silent, verify the hook in `/hooks`, explicitly trust the reviewed command,
fully restart Codex, and retry with a real event. Trusting a hook without
restarting may leave the current process on its previously loaded hook state.
The plugin must not grant or bypass hook trust automatically.
