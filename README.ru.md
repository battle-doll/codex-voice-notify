# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Автономный плагин многоязычных голосовых уведомлений для десяти событий
жизненного цикла Codex в macOS и Windows. Можно выбрать тёплый голос с хрипотцой
или низкий ясный голос на корейском, японском, английском, русском либо
упрощённом китайском языке.

Это независимый плагин: исходный код распространяется по лицензии MIT, а для
голосовых ресурсов действует отдельная лицензия. Плагин не связан с OpenAI и
не одобрен OpenAI.

## Возможности

Плагин воспроизводит локальный WAV-файл для каждого из следующих событий:

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

Версия 0.1.6 содержит 100 WAV-файлов: по одному для каждой комбинации из двух
голосовых профилей, пяти языков и десяти событий жизненного цикла. В этом
обновлении добавлены полные README на английском, корейском, японском,
упрощённом китайском и русском языках. Голосовые ресурсы и поведение во время
выполнения не изменились по сравнению с 0.1.5.

В macOS используются уже установленные `/bin/sh`, `plutil`, `afplay` и
`osascript`, а в Windows — PowerShell и `System.Media.SoundPlayer`. Python и
Xcode Command Line Tools не требуются. В плагине нет сетевого кода и телеметрии;
он не сохраняет запросы, сообщения, входные или выходные данные инструментов.
Воспроизведение не блокирует работу, а локальная блокировка и короткая пауза
предотвращают наложение записей.

## Установка с GitHub

Передайте Codex URL репозитория и попросите установить плагин либо выполните
следующие команды.

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

## Первоначальная настройка

После установки выберите подсказку плагина **Finish first-time setup** или
попросите Codex обычными словами:

> Заверши первоначальную настройку Voice Notify с женским голосом на корейском.
> При необходимости проверь и обнови Codex CLI.

Эту начальную подсказку можно безопасно запускать повторно. Текущий интерфейс
плагинов Codex не скрывает её после первого использования, поэтому она остаётся
доступной для восстановления или повторной настройки.

Пошаговая настройка выполняет следующие действия:

1. Проверяет, поддерживает ли версия Codex CLI команду `/hooks`, и только при
   явном разрешении в запросе на настройку при необходимости обновляет установку
   из npm или Homebrew.
2. Сохраняет выбранные голос и язык.
3. Тестирует локальное уведомление `Stop`.
4. Открывает новое окно терминала и запускает в нём проверенный Codex CLI, а не
   просто выводит инструкцию ввести `/hooks`.

Встроенный сценарий настройки только сообщает о совместимости и сам не изменяет
установку на компьютере. Codex определяет, был ли CLI установлен из npm,
Homebrew cask или другого источника, и выполняет лишь явно разрешённое обновление.

В новом терминале Codex CLI введите `/hooks`, проверьте встроенную команду и
явно подтвердите доверие к ней. Затем полностью закройте и заново запустите
Codex, прежде чем проверять реальные события жизненного цикла. Решение о доверии
сохраняется, но уже запущенный процесс Codex может активировать новый доверенный
хук плагина лишь при следующем запуске. Codex намеренно не доверяет сторонним
хукам во время установки, и плагин не обходит эту проверку.

Если обновление не может заменить запущенный исполняемый файл CLI, закройте этот
CLI, выполните показанную команду обновления в другом терминале и снова начните
настройку.

## Настройка

В любое время можно использовать обычный язык. Например:

- «Используй женский голос на английском».
- «Переключи Voice Notify на мужской голос на японском».
- «Используй женский голос на русском».
- «Переключи Voice Notify на мужской голос на упрощённом китайском».
- «Переключи на женский голос на корейском».
- «Отключи звук Voice Notify».
- «Проверь уведомление Stop».

Codex сопоставляет `female` или `male` и корейский/хангыль (`ko`), японский
(`ja`), английский (`en`), русский (`ru`) либо упрощённый китайский (`zh-CN`)
со встроенной командой настройки. Поскольку в комплект входит только китайский
вариант `zh-CN`, запрос без уточнения «китайский» или «中文» по умолчанию означает
`zh-CN` (упрощённый китайский, стандартный китайский материкового Китая).
Команды также можно запустить вручную из клона репозитория.

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

Значения по умолчанию: `female`, `ko`, минимальный интервал 450 мс и восемь
включённых событий. Чтобы избежать слишком частых уведомлений при каждом вызове
инструмента, `PreToolUse` и `PostToolUse` доступны, но по умолчанию отключены.
`PermissionRequest` воспроизводится только тогда, когда Codex действительно
запрашивает разрешение.

## Устранение неполадок

- Если команда `/hooks` не распознаётся, обновите Codex CLI до версии `0.145.0`
  или новее и повторите настройку.
- Если PowerShell блокирует `codex.ps1` или `npm.ps1`, используйте `codex.cmd`
  или `npm.cmd`. Параметр `-ExecutionPolicy Bypass` во встроенных командах
  настройки Windows действует только в текущем процессе и не меняет системную
  политику выполнения.
- Если тестовый звук работает, а уведомления о событиях жизненного цикла — нет,
  проверьте хук в `/hooks`, явно доверьтесь ему и полностью перезапустите Codex.

## Совместимость

Версия 0.1.6 поддерживает macOS и Windows с системными компонентами звука и
сценариев. В macOS не требуются Python или Xcode Command Line Tools. Для
пошаговой настройки хука нужен Codex CLI `0.145.0` или новее. Linux пока не
поддерживается.

## Лицензирование

Исходный код распространяется по лицензии MIT. Все WAV-файлы в `assets/audio/`
исключены из лицензии MIT. Согласно ограниченному разрешению в
[ASSET_LICENSE.md](ASSET_LICENSE.md), их можно использовать, копировать и
распространять только без изменений, только как часть неизменённой бесплатной
копии Voice Notify for Codex и только для личного некоммерческого воспроизведения
уведомлений.

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) содержит только сведения о
происхождении генерации. Большая часть мужского набора уведомлений создана с
помощью Fish Audio, а два корейских файла уведомлений субагента были повторно
созданы с помощью Qwen Base в соответствии с текущим текстом. Эти сведения о
происхождении не изменяют условия использования голосовых ресурсов.
