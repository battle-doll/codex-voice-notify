# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

macOS と Windows で 10 種類の Codex ライフサイクルイベントを知らせる、
オフラインの多言語音声通知プラグインです。韓国語、日本語、英語、ロシア語、
簡体字中国語から、温かみのあるハスキーボイスまたは低く明るい声を選べます。

これは、MIT ライセンスのソースコードと別途ライセンスされた音声アセットを
使用する独立したプラグインです。OpenAI との提携や OpenAI による承認を
示すものではありません。

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

バージョン 0.1.6 には、2 種類の音声プロファイル、5 言語、10 種類の
ライフサイクルイベントの全組み合わせに対応する 100 WAV ファイルが含まれます。
このパッチでは、英語、韓国語、日本語、簡体字中国語、ロシア語の完全な README
を追加しました。音声アセットと実行時の動作は 0.1.5 から変更していません。

macOS に標準搭載されている `/bin/sh`、`plutil`、`afplay`、`osascript`、
または Windows PowerShell と `System.Media.SoundPlayer` を使用します。
Python や Xcode Command Line Tools は不要です。ネットワークコードや
テレメトリはなく、プロンプト、メッセージ、ツール入力、ツール出力を保存しません。
再生はノンブロッキングで、ローカルロックと短いクールダウンによって音声の重複を
防ぎます。

## GitHub からインストール

Codex にリポジトリ URL を渡してインストールを依頼するか、次を実行します。

macOS:

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

インストール後、プラグインの **Finish first-time setup** プロンプトを選択するか、
Codex に自然な言葉で依頼します。

> 韓国語の女性音声で Voice Notify の初回セットアップを完了して。
> 必要であれば Codex CLI を確認して更新して。

この開始プロンプトは安全に繰り返し実行できます。現在の Codex プラグイン UI は、
初回使用後にプロンプトを条件付きで非表示にしないため、復旧や再セットアップにも
引き続き利用できます。

ガイド付きセットアップでは、次を行います。

1. `/hooks` に対応する Codex CLI バージョンを確認し、セットアッププロンプトで
   明示的に許可された場合に限り、必要に応じて npm または Homebrew の
   インストールを更新します。
2. 選択した音声と言語を保存します。
3. ローカルの `Stop` 通知をテスト再生します。
4. 新しいターミナルウィンドウを開き、確認済みの Codex CLI をその中で起動します。
   単に `/hooks` の入力案内を表示するだけではありません。

同梱のセットアップスクリプト自体は互換性を報告するだけで、ホストの
インストールを変更しません。Codex は CLI が npm、Homebrew cask、または
その他の場所からインストールされたかを確認し、許可された更新だけを行います。

新しく開いた Codex CLI ターミナルで `/hooks` と入力し、同梱コマンドを確認して、
明示的に信頼してください。その後、実際のライフサイクルイベントをテストする前に
Codex を完全に終了して再起動します。フックの信頼設定は保存されますが、すでに
実行中の Codex プロセスでは、次回起動まで新たに信頼したプラグインフックが
有効にならない場合があります。Codex はインストール時にサードパーティ製フックを
自動的に信頼せず、このプラグインもその確認を回避しません。

実行中の CLI 実行ファイルを置き換えられず更新に失敗した場合は、その CLI を終了し、
表示された更新コマンドを別のターミナルで実行してからセットアップをやり直してください。

## 設定

いつでも自然な言葉で依頼できます。例:

- 「英語の女性音声を使って。」
- 「Voice Notify を日本語の男性音声に変更して。」
- 「ロシア語の女性音声を使って。」
- 「Voice Notify を簡体字中国語の男性音声に変更して。」
- 「韓国語の女性音声に変更して。」
- 「Voice Notify をミュートして。」
- 「Stop 通知をテストして。」

Codex は `female` または `male` と、韓国語／ハングル (`ko`)、日本語 (`ja`)、
英語 (`en`)、ロシア語 (`ru`)、簡体字中国語 (`zh-CN`) を同梱の設定コマンドに
対応付けます。同梱の中国語バリエーションは `zh-CN` だけなので、種類を指定しない
「中国語」または「中文」という依頼は `zh-CN`（簡体字中国語、中国本土の標準中国語）
になります。クローンしたリポジトリから手動で実行することもできます。

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko --open-hooks
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko -OpenHooks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

既定値は `female`、`ko`、最小再生間隔 450 ms、8 イベント有効です。
ツールごとの通知が多くなりすぎないよう、`PreToolUse` と `PostToolUse` は利用可能な
まま既定で無効になっています。`PermissionRequest` は、Codex が実際に権限を
求めたときだけ再生されます。

## トラブルシューティング

- `/hooks` が認識されない場合は、Codex CLI を `0.145.0` 以降に更新し、
  セットアップをやり直してください。
- PowerShell が `codex.ps1` または `npm.ps1` をブロックする場合は、
  `codex.cmd` または `npm.cmd` を使用してください。同梱の Windows 設定コマンドの
  `-ExecutionPolicy Bypass` はそのプロセスだけに適用され、システムの実行ポリシーを
  変更しません。
- テスト音声は再生されるのにライフサイクル通知が出ない場合は、`/hooks` でフックを
  確認して信頼し、Codex を完全に再起動してください。

## 互換性

バージョン 0.1.6 は、システム提供の音声・スクリプト機能を使用する macOS と
Windows に対応します。macOS では Python や Xcode Command Line Tools は不要です。
ガイド付きフック設定には Codex CLI `0.145.0` 以降が必要です。Linux はまだ
対応していません。

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
