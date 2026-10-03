# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

在 Codex 需要您关注或完成任务时，用私密的本地语音提醒您。
支持 macOS、Windows 和 Linux。

### 使用

- 从 GitHub 安装后，请说：`用韩语女声首次设置 Voice Notify。说明钩子内容，并在批准前询问我。`
- Codex 检查兼容性和音频、保存偏好，并显示确切的 Voice Notify 钩子命令。您审阅并同意后，可以通过 Codex 官方本地接口自动处理批准。
- 随时选择语音、语言、生命周期事件、播放间隔，或测试、静音和取消静音。

### 试用

- `Codex 请求权限或完成任务时，用中文女声通知我。`
- `检查 Codex 更新后 Voice Notify 不工作的原因。`
- `测试本地 Stop 提醒，然后静音 Voice Notify。`

### 主要边界

- 播放完全离线，不保存或发送对话内容。
- 仅用于 Codex 生命周期语音设置，不用于通用 TTS、旁白、语音转写、云通知、任意系统音频自动化或截图操作提取。
- 钩子批准需要用户审阅和同意。只批准已审阅的 Voice Notify 钩子，不修改其他钩子或通知设置。

2026-10-03 核查：OpenAI Platform 中既有 0.1.7 条目显示 **Published**。0.2.0 尚未提交，当前目录上架及搜索状态未核实。历史记录 — Verified on 2026-08-29: **GLOBAL/AVAILABLE**、**UNLISTED** 是旧快照，不代表当前可发现性。[既有条目](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83)。

2026-10-03 核查的 [OpenAI 提交文档](https://developers.openai.com/plugins/deploy/submission)目前不接受含生命周期钩子的 ZIP。0.2.0 是已准备的更新候选版本，公开提交暂缓。请参阅 [SUBMISSION.md](SUBMISSION.md)。

这是独立插件，源代码使用 MIT 许可证，语音资源采用单独许可。它不隶属于 OpenAI，也不代表 OpenAI 的认可。

## 功能

为以下事件播放本地 WAV：

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

版本 0.2.0 包含 100 WAV 文件，覆盖 2 种声音、5 种语言和 10 个事件。语音资源和默认值未变。此版支持当前 Codex prerelease 版本字符串，增加只读诊断、用户同意后的钩子批准流程，以及 Linux 播放。

macOS 日常播放和设置使用系统自带的 `/bin/sh`、`plutil`、`afplay`、`osascript`，不需要 Python 或 Xcode Command Line Tools。Windows 使用 PowerShell 和 `System.Media.SoundPlayer`。Linux 使用 Python 3 标准库，并按 `pw-play`、`paplay`、`aplay`、`ffplay` 顺序选择首个已安装播放器，不自动安装音频软件。运行时播放不包含网络代码或遥测，不会存储提示词、消息、工具输入或工具输出。本地锁和短间隔避免声音重叠。

### 交互式代码本体

本仓库的自包含交互式本体是使用
[Code Ontology Companion](https://github.com/battle-doll/code-ontology-companion)
从 Voice Notify `0.1.6` 生成的。Code Ontology Companion 可以将已获授权的 Java/Spring 或 Python 代码库逆向分析为注重隐私的本地知识图谱。

[在线打开 Voice Notify 代码本体](https://rawcdn.githack.com/battle-doll/codex-voice-notify/ce42d10e88fc490271bea2c123a611bfa3d12b13/codex-voice-notify-code-ontology.html)，或[在 GitHub 上查看和下载源 HTML](https://github.com/battle-doll/codex-voice-notify/blob/code-ontology-showcase/codex-voice-notify-code-ontology.html)。

该快照分析了 6 个 Python 文件，包含 417 个节点和 769 条关系，解析警告为零，且每条关系都附有提取证据和源码位置范围。您可以搜索符号，检查调用者和依赖项，在 2D 结构视图与 3D 星座视图之间切换，并查看每条关系的规则、定性依据、运行时状态、源码位置范围和局限性。

这仍是静态分析证据，而非运行时证明。Voice Notify 在 Windows 和 macOS 上的实际钩子入口点分别是 PowerShell (`.ps1`) 和 POSIX shell (`.sh`)，超出了此 Python 快照的适配器覆盖范围。此示例在获得明确的发布授权后公开。在线预览仅使用 raw.githack 作为 HTML 内容类型桥接；自包含工作台本身在运行时不依赖 CDN 或网络。

这是历史 0.1.6 快照，并未为 0.2.0 的 Linux 和钩子批准改动重新生成。

## 从 GitHub 安装

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

## 首次设置

Codex 用您当前对话的语言说明设置，并列出韩语、英语、日语、俄语、简体中文五种语音语言，以及女声和男声。说明语言与通知语音语言可分别选择。保留已有设置及明确选择，只简短询问缺失选项。新设置建议女声及您使用的受支持语音语言；没有对应音频时建议韩语。脚本原始默认值仍为 `female/ko`。钩子审阅、同意和实际听音确认也用您的语言说明。

安装后选择 **Finish first-time setup**，或说：

> 用韩语女声首次设置 Voice Notify。说明钩子内容，并在批准前询问我。

可重复执行的设置流程：

1. 用只读 `doctor` 检查选定的 Codex CLI、版本、播放器和设置。需要 CLI `0.145.0` 或更高版本，并支持当前 prerelease 后缀。
2. 保存所选声音和语言，测试本地 `Stop` 提醒，确认您实际听到了声音。
3. 运行 `review-hooks`，显示确切的 Voice Notify 命令、范围和`approvalDigest`，请求批准这些命令。
4. 用户明确同意后，用相同 `approvalDigest`运行 `approve-hooks`。Codex 官方本地 app-server 接口只批准已审阅的 Voice Notify 钩子。命令发生变化就需要重新审阅；不直接编辑信任存储，也不绕过审阅。
5. 彻底退出并重新启动 Codex，实际听到一个已启用事件的声音。设置测试或批准记录本身不能证明生命周期提醒有效。

若自动批准接口不可用，在 macOS/Linux 使用 `setup --open-hooks`，Windows 使用 `setup -OpenHooks` 打开 CLI 终端。在其中输入 `/hooks`，检查插件自带的命令，并明确选择信任。彻底退出并重新启动 Codex 后测试真实事件。无图形环境或没有终端启动器时，手动启动选定的 CLI 并输入 `/hooks`。

脚本不会静默更新 Codex 或安装依赖。只有您另行明确授权更新，且已核实 npm 或 Homebrew 安装来源时，才可更新旧 CLI。桌面应用内置或来源不明的安装使用其官方更新渠道。更新前应退出占用可执行文件的 CLI。

## 配置

可以自然语言请求“改为英语女声”“改为日语男声”“改为俄语女声”“改为简体中文男声”或“静音 Voice Notify”。

将 `female` 或 `male` 与韩语/韩文 (`ko`)、日语 (`ja`)、英语 (`en`)、俄语 (`ru`) 或简体中文 (`zh-CN`) 映射到设置。笼统的“中文”或“Chinese”默认选择唯一中文变体 `zh-CN`（中国大陆普通话、简体中文）。从克隆目录手动执行：

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh doctor
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko
/bin/sh scripts/voice_notify_config.sh review-hooks
# 明确同意后，将 <approvalDigest> 替换为本次审阅返回的值：
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
# 明确同意后，将 <approvalDigest> 替换为本次审阅返回的值：
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
# 明确同意后，将 <approvalDigest> 替换为本次审阅返回的值：
python3 scripts/voice_notify_config.py approve-hooks --approve "<approvalDigest>"
python3 scripts/voice_notify_config.py show
python3 scripts/voice_notify_config.py set --voice male --language en
python3 scripts/voice_notify_config.py test --event Stop
python3 scripts/voice_notify_config.py mute
```

默认 `female`、`ko`、最小间隔 450 ms，并启用 8 个事件。`PreToolUse` 和 `PostToolUse` 可配置，但默认关闭。只有 Codex 实际请求权限时才播放 `PermissionRequest`。

## 故障排除

- 先运行 `doctor`。诊断不会改设置、批准钩子或播放音频。本地输出可能含路径，分享前请遮盖。
- 若没有 `/hooks`，检查所选 CLI，并在用户授权后更新。桌面应用和单独安装的 CLI 版本可能不同。
- 仅测试声音有效时，检查批准状态，彻底关闭并重启相应 Codex 进程，然后测试真实的已启用事件。
- PowerShell 阻止 `codex.ps1` 或 `npm.ps1` 时，使用 `codex.cmd` 或 `npm.cmd`。`-ExecutionPolicy Bypass` 仅作用于本次设置进程，不修改系统策略。
- Linux 需要 Python 3、受支持的播放器及可用音频设备或服务。SSH、容器、WSL 和无图形会话即使有播放器也可能听不到声音。不自动安装软件包。

## 兼容性

版本 0.2.0 支持 macOS、Windows 和 Linux。macOS 日常播放和设置不依赖 Python，Windows 使用系统 PowerShell，Linux 需要 Python 3 及一种受支持的本地播放器。自动钩子批准使用 macOS 自带的 `osascript` JXA、Windows 自带 PowerShell 或 Linux Python 3，还需要所选 CLI 的官方本地 app-server 接口；不可用时使用 `/hooks` 手动审阅。需要 CLI `0.145.0` 或更高版本。平台支持不代表已在每个桌面版本、音频后端或无图形会话中验证实际听音。

## 许可证

源代码采用 MIT 许可证。`assets/audio/` 下的所有 WAV 文件均不属于 MIT 许可证
范围。根据 [ASSET_LICENSE.md](ASSET_LICENSE.md) 中的有限授权，这些文件只能
保持原样，只能作为未经修改的免费 Voice Notify for Codex 副本的一部分，并且只能
用于个人、非商业通知播放；仅可在这些条件下使用、复制和重新分发。

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 仅记录生成来源。大多数男声通知
由 Fish Audio 生成，两个韩语子代理文件则使用 Qwen Base 重新生成，以匹配当前
文案。这些来源信息不会改变语音资源的使用条款。
