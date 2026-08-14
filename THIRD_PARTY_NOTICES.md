# Third-party notices and provenance

The release WAV files were generated locally through an MLX runtime. The plugin
does not include model weights, runtime code, a generation service, or reference
recordings.

## Female notification set

The female WAV files were generated with
`mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`, pinned to revision
`1eccf1cb2519b5a4e8a95b5f0544f3303568164f`. The original local reference was
synthetic material created for this project with
`mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16`, pinned to revision
`7d3824abff87e49756bb0f83fb5411de75d160c4`.

The Korean and Japanese female sets use that original local reference. For the
English set, Qwen Base first created an approved English speaker-embedding-only
anchor from the same reference. The anchor and its exact English transcript
then served as the English reference for the other nine notification phrases.
The approved anchor itself is the English `stop.wav`. Leading low-level inactive
audio was trimmed where necessary without changing the spoken content.

The upstream Qwen3-TTS project and both model repositories identify their
license as Apache-2.0:

- https://github.com/QwenLM/Qwen3-TTS/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
- https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16
- https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16

## Version 0.1.5 Russian and Simplified Chinese expansion

The 40 Russian (`ru`) and Simplified Chinese (`zh-CN`) WAV files added in
version 0.1.5 were generated with
`mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16`, pinned to revision
`1eccf1cb2519b5a4e8a95b5f0544f3303568164f`. The female files used the
approved local `female-warm-husky-v1` reference, and the male files used the
approved local `male-deep-bright-v1` reference. Russian generation used the
paired reference transcript. Simplified Chinese generation used Qwen Base's
speaker-embedding-only path (`ref_text=None`) to preserve each approved voice
without pairing a Korean reference recording with Chinese text. The female reference is
original synthetic material created for this project with Qwen VoiceDesign.
The male reference was normalized from this project's existing Fish S2
Pro-generated Korean `session-start.wav` notification described below.
Reference recordings are not included in the plugin, and the asset license's
non-commercial boundary continues to apply to the expanded set.

## Male notification set

The original male set was generated with Fish S2 Pro, using model revision
`c8d4481b3f7cbfe64d855c8b7cda7739502fc3ff`. The Korean
`subagent-start.wav` and `subagent-stop.wav` files were regenerated with the
Qwen Base model above so the spoken wording matches the version 0.1.1 phrase
catalog. An original male notification from this project was used as the local
reference.

Built with Fish Audio.

This model is licensed under the Fish Audio Research License, Copyright © 39
AI, INC. All Rights Reserved. A complete copy of the applicable agreement is
included in
[`FISH_AUDIO_RESEARCH_LICENSE.md`](FISH_AUDIO_RESEARCH_LICENSE.md), and the
upstream source is:
https://github.com/fishaudio/fish-speech/blob/main/LICENSE

For both sets, voice-design source material was original synthetic material
created for this project. No third-party performer, actor, or
fictional-character recording was used as a generation reference. Voice
descriptions are generic and do not claim identity, endorsement, or affiliation
with any real person or fictional property.

The audio assets are governed by `ASSET_LICENSE.md`, not the MIT code license.
