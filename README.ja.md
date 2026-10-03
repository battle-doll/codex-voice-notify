# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Codex が注意を求めたときや作業を終えたとき、非公開のローカル音声で知らせます。
macOS、Windows、Linux に対応します。

### 使い方

- GitHub からインストールし、`Voice Notify を韓国語の女性音声で初回設定して。フックを説明し、承認前に確認して。` と依頼します。
- Codex が互換性と音声を確認し、設定を保存して正確な Voice Notify フックコマンドを示します。内容を確認して承認した後、Codex の公式ローカルインターフェイスで承認処理を自動化できます。
- 音声、言語、イベント、再生間隔を選択し、いつでもテスト、ミュート、ミュート解除できます。

### 試してみる

- `Codex が権限を求めるか終了したら、女性の日本語音声で知らせて。`
- `Codex 更新後に Voice Notify が動かない原因を調べて。`
- `ローカルの Stop 通知をテストしてから Voice Notify をミュートして。`

### 重要な境界

- 再生はオフラインで、会話内容を保存も送信もしません。
- Codex ライフサイクル音声の設定専用です。一般的な TTS、ナレーション、文字起こし、クラウド通知、任意の OS 音声自動化、スクリーンショットからのアクション抽出には使いません。
- フック承認には利用者の確認と同意が必要です。確認済みの Voice Notify フックだけを承認し、他のフックや通知設定は変更しません。

2026-10-03 確認: OpenAI Platform の既存 0.1.7 項目は **Published** です。0.2.0 は未提出で、現在のディレクトリ掲載・検索可否は未確認です。過去の記録 — Verified on 2026-08-29: **GLOBAL/AVAILABLE**、**UNLISTED** は過去のスナップショットで、現在の掲載状態を示しません。[既存項目](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83)。

2026-10-03 に確認した [OpenAI の提出文書](https://developers.openai.com/plugins/deploy/submission)では、ライフサイクルフックを含む ZIP は現在提出できません。0.2.0 は準備済みの更新候補で、公開提出は保留中です。[SUBMISSION.md](SUBMISSION.md) を参照してください。

MIT ライセンスのソースと別途ライセンスされた音声アセットを使用する独立したプラグインです。OpenAI との提携や OpenAI による承認を示しません。

## 機能

次のイベントごとにローカル WAV を再生します。

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PermissionRequest`
- `PreCompact`
- `PostCompact`
- `SubagentStart`
- `SubagentStop`
- `Stop`

バージョン 0.2.0 は、2 音声、5 言語、10 イベントに対応する 100 WAV ファイルを同梱します。音声アセットと既定値は変更していません。最新 Codex の prerelease バージョン表記、読み取り専用診断、利用者の同意後のフック承認処理、Linux 再生に対応しました。

macOS の通常の再生・設定は標準の `/bin/sh`、`plutil`、`afplay`、`osascript` を使い、Python や Xcode Command Line Tools は不要です。Windows は PowerShell と `System.Media.SoundPlayer` を使います。Linux は Python 3 標準ライブラリと、`pw-play`、`paplay`、`aplay`、`ffplay` の順で最初に見つかった再生ソフトを使います。音声パッケージは自動インストールしません。実行時の再生には外部へのネットワークコードやテレメトリはなく、プロンプト、メッセージ、ツール入力、ツール出力を保存しません。ローカルロックと短い間隔で重複再生を防ぎます。

### インタラクティブなコードオントロジー

このリポジトリの自己完結型インタラクティブオントロジーは、
[Code Ontology Companion](https://github.com/battle-doll/code-ontology-companion) を使用して
Voice Notify `0.1.6` から生成したものです。

[インタラクティブグラフを開く](https://rawcdn.githack.com/battle-doll/codex-voice-notify/ce42d10e88fc490271bea2c123a611bfa3d12b13/codex-voice-notify-code-ontology.html)。
GitHub 上の [HTML ソースを表示・ダウンロード](https://github.com/battle-doll/codex-voice-notify/blob/code-ontology-showcase/codex-voice-notify-code-ontology.html)することもできます。

このスナップショットは 6 個の Python ファイルから 417 ノードと 769 関係を抽出しており、
パース警告は 0 件です。すべての関係に抽出根拠とソース範囲が付与されています。
シンボルを検索し、呼び出し元や依存関係を調べ、2D 構造ビューと 3D コンステレーションビューを
切り替えられます。また、各関係の抽出ルール、定性的な根拠、ランタイム状態、ソース範囲、制限事項を
詳細に確認できます。

ここで示すのは静的解析の証拠であり、実際のランタイム動作の証明ではありません。
Windows と macOS で実際に使用される PowerShell `.ps1` および POSIX shell `.sh` のフックエントリポイントは、
この Python スナップショットの解析範囲には含まれません。この例は明示的な公開許可を得て公開されています。
raw.githack は、GitHub 上のファイルを HTML の Content-Type でブラウザーに配信するための橋渡しにのみ使用しています。
自己完結型グラフ自体には、実行時の CDN やネットワーク依存関係はありません。

これは過去の 0.1.6 スナップショットで、0.2.0 の Linux・フック承認変更を反映して再生成したものではありません。

## GitHub からインストール

macOS / Linux:

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Windows PowerShell:

```powershell
codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main
codex.cmd plugin add codex-voice-notify@codex-voice-notify
```

## 初回セットアップ

Codex は会話中の言語で設定を案内し、韓国語・英語・日本語・ロシア語・簡体字中国語の5言語と女性・男性の声を示します。案内の言語と音声の言語は別々に選べます。既存の設定や指定した選択を維持し、未指定の項目だけ簡潔に確認します。新規設定では女性の声と利用者の対応音声言語を提案し、対応する音声がなければ韓国語を提案します。スクリプトの既定値 `female/ko` は変わりません。フックの確認、同意、実際に聞こえたかの確認も利用者の言語で行います。

インストール後、**Finish first-time setup** を選択するか、次のように依頼します。

> Voice Notify を韓国語の女性音声で初回設定して。フックを説明し、承認前に確認して。

繰り返し実行できるセットアップ手順です。

1. 読み取り専用の `doctor` で選択した CLI、バージョン、再生ソフト、設定を確認します。Codex CLI `0.145.0` 以上が必要で、現在の prerelease 接尾辞も認識します。
2. 音声と言語を保存し、ローカル `Stop` 音声をテストします。実際に聞こえたか確認します。
3. `review-hooks` で正確な Voice Notify コマンド、範囲、`approvalDigest`を提示し、そのコマンドの承認を求めます。
4. 明示的な承認後、同じ `approvalDigest`を指定して `approve-hooks` を実行します。Codex の公式ローカル app-server インターフェイスが確認済みの Voice Notify フックだけを承認します。変更されたコマンドは再確認が必要です。信頼ストアを直接編集せず、確認を回避しません。
5. Codex を完全に終了して再起動し、有効なイベントの音声を一度聞きます。設定テストや承認記録だけではライフサイクル再生の成功を証明できません。

自動承認インターフェイスを使えない場合、macOS/Linux の `setup --open-hooks` または Windows の `setup -OpenHooks` で CLI ターミナルを開きます。その中で `/hooks` と入力し、同梱コマンドを確認して、明示的に信頼してください。Codex を完全に終了して再起動してから実際のイベントをテストします。headless 環境や起動用ターミナルがない場合、選択した CLI を手動で起動して `/hooks` を入力します。

スクリプトは Codex や依存関係を無断で更新・インストールしません。古い CLI は、別途明示的に許可された場合だけ、導入元が確認済みの npm・Homebrew で更新できます。デスクトップ同梱版や不明な導入元は、その導入方法の公式更新経路を使います。使用中の CLI は更新前に終了します。

## 設定

「女性の英語音声に変更して」「男性の日本語にして」「女性のロシア語にして」「男性の簡体字中国語にして」「Voice Notify をミュートして」のように依頼できます。

`female` または `male` と、韓国語/ハングル (`ko`)、日本語 (`ja`)、英語 (`en`)、ロシア語 (`ru`)、簡体字中国語 (`zh-CN`) を設定に対応させます。単に「中国語」「中文」と指定した場合は唯一の中国語音声 `zh-CN`（簡体字、中国本土の標準中国語）を選びます。クローンから手動実行するコマンド:

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh doctor
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko
/bin/sh scripts/voice_notify_config.sh review-hooks
# 明示的な承認後、<approvalDigest> を今回の確認で返された値に置き換えます:
/bin/sh scripts/voice_notify_config.sh approve-hooks --approve "<approvalDigest>"
/bin/sh scripts/voice_notify_config.sh show
/bin/sh scripts/voice_notify_config.sh set --voice female --language ko
/bin/sh scripts/voice_notify_config.sh set --voice male --language en
/bin/sh scripts/voice_notify_config.sh set --voice female --language ru
/bin/sh scripts/voice_notify_config.sh set --voice male --language zh-CN
/bin/sh scripts/voice_notify_config.sh test --event Stop
/bin/sh scripts/voice_notify_config.sh mute
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 doctor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 review-hooks
# 明示的な承認後、<approvalDigest> を今回の確認で返された値に置き換えます:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 approve-hooks -Approve "<approvalDigest>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

Linux:

```bash
python3 scripts/voice_notify_config.py doctor
python3 scripts/voice_notify_config.py setup --voice female --language ko
python3 scripts/voice_notify_config.py review-hooks
# 明示的な承認後、<approvalDigest> を今回の確認で返された値に置き換えます:
python3 scripts/voice_notify_config.py approve-hooks --approve "<approvalDigest>"
python3 scripts/voice_notify_config.py show
python3 scripts/voice_notify_config.py set --voice male --language en
python3 scripts/voice_notify_config.py test --event Stop
python3 scripts/voice_notify_config.py mute
```

既定値は `female`、`ko`、最短間隔 450 ms、8 イベント有効です。`PreToolUse` と `PostToolUse` は使用できますが既定では無効です。`PermissionRequest` は Codex が実際に権限を要求したときだけ再生します。

## トラブルシューティング

- まず `doctor` を実行します。診断は設定変更、フック承認、音声再生をしません。ローカル出力にはパスが含まれる場合があるため、共有前に伏せてください。
- `/hooks` がない場合、選択した CLI を確認し、利用者の許可を得て更新します。デスクトップアプリと別途導入した CLI の版は異なる場合があります。
- テスト音声だけ聞こえる場合、承認を確認して対象の Codex を完全に終了・再起動し、実際の有効イベントをテストします。
- PowerShell が `codex.ps1`・`npm.ps1` をブロックする場合は `codex.cmd`・`npm.cmd` を使います。`-ExecutionPolicy Bypass` はその設定プロセスだけに適用され、システム方針は変えません。
- Linux は Python 3、対応再生ソフト、利用可能な音声デバイス・サーバーが必要です。SSH、コンテナー、WSL、headless セッションでは再生ソフトがあっても音が出ない場合があります。パッケージは自動導入しません。

## 互換性

バージョン 0.2.0 は macOS、Windows、Linux をサポートします。macOS の通常の再生・設定は Python 不要で、Windows は標準 PowerShell、Linux は Python 3 と対応再生ソフトを使います。自動フック承認は macOS 標準の `osascript` JXA、Windows 標準 PowerShell、Linux Python 3 を使い、選択した CLI の公式ローカル app-server インターフェイスが必要です。利用できなければ `/hooks` で手動確認します。CLI `0.145.0` 以上が必要です。対応表記はすべてのデスクトップ版や音声環境、headless セッションでの実際の聴取確認を意味しません。

## ライセンス

ソースコードは MIT ライセンスです。`assets/audio/` 以下のすべての WAV
ファイルは MIT ライセンスの対象外です。
[ASSET_LICENSE.md](ASSET_LICENSE.md) の限定的許諾により、これらは未改変の
まま、未改変かつ無償の Voice Notify for Codex のコピーに含める場合に限り、
個人的・非商用の通知再生目的でのみ使用、複製、再配布できます。

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) は生成来歴のみを記録します。
男性通知セットの大部分は Fish Audio で作成され、韓国語のサブエージェント用
ファイル 2 個は現在の文言に合わせて Qwen Base で再生成されました。これらの
来歴情報によって音声アセットの利用条件が変わることはありません。
