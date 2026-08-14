# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

适用于 macOS 和 Windows 的离线多语言语音通知插件，可为十种 Codex 生命周期事件
播放提示。您可以在韩语、日语、英语、俄语和简体中文之间选择温暖沙哑的声音或低沉
明亮的声音。

这是一个独立插件，源代码采用 MIT 许可证，语音资源采用单独的许可证。它不隶属于
OpenAI，也未获 OpenAI 背书。

## 功能

插件会为以下事件播放本地 WAV：

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

版本 0.1.6 内含 100 WAV 文件，覆盖两种声音配置、五种语言与十种生命周期事件的
全部组合。本次补丁提供完整的英语、韩语、日语、简体中文和俄语 README；语音资源和
运行时行为与 0.1.5 相同。

在 macOS 上，插件使用系统自带的 `/bin/sh`、`plutil`、`afplay` 和 `osascript`；
在 Windows 上，则使用 PowerShell 和 `System.Media.SoundPlayer`。它不需要 Python
或 Xcode Command Line Tools。插件不包含网络代码或遥测，也不会存储提示词、消息、
工具输入或工具输出。播放不会阻塞任务，本地锁和短暂冷却时间可避免音频重叠。

## 从 GitHub 安装

将仓库 URL 交给 Codex 并要求安装此插件，或者运行以下命令。

macOS：

```bash
codex plugin marketplace add battle-doll/codex-voice-notify --ref main
codex plugin add codex-voice-notify@codex-voice-notify
```

Windows PowerShell：

```powershell
codex.cmd plugin marketplace add battle-doll/codex-voice-notify --ref main
codex.cmd plugin add codex-voice-notify@codex-voice-notify
```

## 首次设置

安装后，选择插件的 **Finish first-time setup** 提示，或直接用自然语言向 Codex
提出请求。

> 使用韩语女声完成 Voice Notify 的首次设置。需要时检查并更新 Codex CLI。

此启动提示可以安全地重复执行。目前 Codex 插件界面不会在首次使用后有条件地隐藏
提示，因此它会保留下来，便于恢复或重新设置。

引导式设置会执行以下操作：

1. 检查 Codex CLI 版本是否支持 `/hooks`；仅当设置提示明确授权时，才会按需更新
   npm 或 Homebrew 安装。
2. 保存所选声音和语言。
3. 试播本地 `Stop` 通知。
4. 打开一个新的终端窗口，并在其中启动已验证的 Codex CLI，而不只是显示
   `/hooks` 输入说明。

插件自带的设置脚本只报告兼容性，不会自行修改主机安装。Codex 会先检查 CLI 来自
npm、Homebrew cask 还是其他位置，再执行用户已经授权的更新。

在新打开的 Codex CLI 终端中输入 `/hooks`，检查插件自带的命令并明确选择信任。
然后彻底退出并重新启动 Codex，再测试实际的生命周期事件。钩子信任设置会被保留，
但已经运行的 Codex 进程可能要到下次启动时才会启用新信任的插件钩子。Codex 不会在
安装时自动信任第三方钩子，本插件也绝不会绕过该审核步骤。

如果正在运行的 CLI 可执行文件无法被替换而导致更新失败，请退出该 CLI，在另一终端中
运行显示的更新命令，然后重新开始设置。

## 配置

您可以随时使用自然语言提出请求，例如：

- “使用英语女声。”
- “把 Voice Notify 改为日语男声。”
- “使用俄语女声。”
- “把 Voice Notify 改为简体中文男声。”
- “改为韩语女声。”
- “将 Voice Notify 静音。”
- “测试 Stop 通知。”

Codex 会将 `female` 或 `male` 以及韩语/韩文 (`ko`)、日语 (`ja`)、英语 (`en`)、
俄语 (`ru`) 或简体中文 (`zh-CN`) 映射到插件自带的设置命令。插件仅内含
`zh-CN` 这一种中文变体，因此未指定变体的“中文”请求会默认映射到 `zh-CN`
（简体中文、中国大陆普通话）。您也可以从克隆的仓库中手动运行以下命令。

macOS：

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

Windows：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 setup -Voice female -Language ko -OpenHooks
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 show
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language ko
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice male -Language ru
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 set -Voice female -Language zh-CN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 test -Event Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\voice_notify_config.ps1 mute
```

默认值为 `female`、`ko`、450 毫秒最短播放间隔，并启用八种事件。为避免每次工具
调用都产生过多通知，`PreToolUse` 和 `PostToolUse` 保持可用但默认关闭。
`PermissionRequest` 只会在 Codex 实际请求权限时播放。

## 故障排除

- 如果无法识别 `/hooks`，请将 Codex CLI 更新至 `0.145.0` 或更高版本，然后重新
  开始设置。
- 如果 PowerShell 阻止 `codex.ps1` 或 `npm.ps1`，请使用 `codex.cmd` 或
  `npm.cmd`。插件自带 Windows 设置命令中的 `-ExecutionPolicy Bypass` 仅适用于
  当前进程，不会更改系统执行策略。
- 如果测试声音可以播放，但生命周期通知没有出现，请在 `/hooks` 中检查并信任该钩子，
  然后彻底重新启动 Codex。

## 兼容性

版本 0.1.6 支持 macOS 和 Windows，并使用系统自带的音频与脚本组件。macOS 不需要
Python 或 Xcode Command Line Tools。引导式钩子设置需要 Codex CLI `0.145.0`
或更高版本。暂不支持 Linux。

## 许可证

源代码采用 MIT 许可证。`assets/audio/` 下的所有 WAV 文件均不属于 MIT 许可证
范围。根据 [ASSET_LICENSE.md](ASSET_LICENSE.md) 中的有限授权，这些文件只能
保持原样，只能作为未经修改的免费 Voice Notify for Codex 副本的一部分，并且只能
用于个人、非商业通知播放；仅可在这些条件下使用、复制和重新分发。

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 仅记录生成来源。大多数男声通知
由 Fish Audio 生成，两个韩语子代理文件则使用 Qwen Base 重新生成，以匹配当前
文案。这些来源信息不会改变语音资源的使用条款。
