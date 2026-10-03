# Voice Notify for Codex

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Слышите приватное локальное уведомление, когда Codex требует внимания или завершает работу.
Поддерживаются macOS, Windows и Linux.

### Использование

- Установите плагин с GitHub и попросите: `Настрой Voice Notify с женским корейским голосом. Объясни хуки и спроси меня перед их одобрением.`
- Codex проверит совместимость и звук, сохранит настройки и покажет точные команды хуков Voice Notify. После вашей проверки и согласия одобрение можно применить автоматически через официальный локальный интерфейс Codex.
- Выбирайте голос, язык, события и интервал; проверяйте звук, отключайте и включайте уведомления.

### Попробуйте

- `Сообщай женским русским голосом, когда Codex запрашивает разрешение или завершает работу.`
- `Проверь, почему Voice Notify перестал работать после обновления Codex.`
- `Проверь локальное уведомление Stop, затем отключи звук Voice Notify.`

### Границы

- Воспроизведение работает офлайн, не сохраняет и не передаёт содержимое разговоров.
- Плагин предназначен для голосовых событий Codex, а не для обычного TTS, озвучивания, транскрипции, облачных уведомлений, произвольной автоматизации звука ОС или извлечения действий из снимков экрана.
- Одобрение хуков требует вашей проверки и согласия. Одобряются только проверенные хуки Voice Notify; другие хуки и уведомления не меняются.

Проверено 2026-10-03: существующая запись 0.1.7 в OpenAI Platform имеет статус **Published**. Версия 0.2.0 не отправлена; текущая доступность в каталоге и поиске не проверена. Историческая запись — Verified on 2026-08-29: **GLOBAL/AVAILABLE**, **UNLISTED** относятся к старому снимку, а не к текущей видимости. [Существующая запись](https://chatgpt.com/plugins/plugins_6a6600dd92148191a6dfe0c16eb85c83).

Согласно [документации OpenAI](https://developers.openai.com/plugins/deploy/submission), проверенной 2026-10-03, ZIP с хуками жизненного цикла сейчас не принимаются. 0.2.0 — подготовленный кандидат на обновление; публичная отправка приостановлена. См. [SUBMISSION.md](SUBMISSION.md).

Это независимый плагин с исходным кодом MIT и отдельно лицензированными голосовыми ресурсами. Он не связан с OpenAI и не одобрен OpenAI.

## Возможности

Для следующих событий воспроизводится локальный WAV:

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

Версия 0.2.0 содержит 100 WAV-файлов: два голоса, пять языков и десять событий. Голосовые ресурсы и значения по умолчанию не изменены. Добавлены поддержка текущих prerelease-строк версии Codex, диагностика без изменений, одобрение хуков после согласия пользователя и воспроизведение в Linux.

Обычное воспроизведение и настройки macOS используют встроенные `/bin/sh`, `plutil`, `afplay`, `osascript` без Python и Xcode Command Line Tools. Windows использует PowerShell и `System.Media.SoundPlayer`. Linux использует стандартную библиотеку Python 3 и первый установленный проигрыватель из `pw-play`, `paplay`, `aplay`, `ffplay`. Аудиопакеты автоматически не устанавливаются. В воспроизведении нет сетевого кода и телеметрии; плагин не сохраняет запросы, сообщения, входные или выходные данные инструментов. Локальная блокировка и короткий интервал предотвращают наложение звука.

### Интерактивная онтология Voice Notify

Автономная интерактивная онтология этого репозитория была создана на основе
Voice Notify версии `0.1.6` с помощью
[Code Ontology Companion](https://github.com/battle-doll/code-ontology-companion).

[Открыть интерактивную онтологию](https://rawcdn.githack.com/battle-doll/codex-voice-notify/ce42d10e88fc490271bea2c123a611bfa3d12b13/codex-voice-notify-code-ontology.html)
или [посмотреть исходный автономный HTML-файл на GitHub](https://github.com/battle-doll/codex-voice-notify/blob/code-ontology-showcase/codex-voice-notify-code-ontology.html).

Граф содержит 417 узлов и 769 связей, извлечённых из шести файлов Python, без
предупреждений разбора. Для каждой связи указаны свидетельство и диапазон строк
исходного кода. В интерфейсе можно искать символы, исследовать вызывающий и
зависимый код, переключаться между двумерным и трёхмерным представлениями, а
также изучать правило, качественное основание, статус выполнения, исходный
диапазон строк и ограничения каждой связи.

Эти данные служат свидетельствами статического анализа, а не подтверждением
поведения во время выполнения. Фактические точки входа Voice Notify в Windows
и macOS реализованы соответственно на PowerShell (`.ps1`) и POSIX shell (`.sh`)
и поэтому не входят в покрытие этого снимка Python. Публикация выполнена с
явного разрешения. raw.githack используется только как мост для выдачи
размещённого на GitHub файла с типом содержимого HTML; сам автономный интерфейс
во время выполнения не зависит от CDN или сети.

Это исторический снимок 0.1.6; он не пересоздавался для изменений Linux и одобрения хуков в 0.2.0.

## Установка с GitHub

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

## Первоначальная настройка

Codex объясняет настройку на языке вашего разговора и показывает пять языков звука — корейский, английский, японский, русский и упрощённый китайский — и женский/мужской голос. Язык объяснений и звука выбираются отдельно. Существующие и явно выбранные настройки сохраняются; краткий вопрос задаётся только для отсутствующего выбора. При новой настройке предлагается женский голос на вашем поддерживаемом языке, а если такого звука нет — корейский. Исходные значения сценариев остаются `female/ko`. Проверка хуков, согласие и подтверждение слышимости также объясняются на вашем языке.

После установки выберите **Finish first-time setup** или попросите:

> Настрой Voice Notify с женским корейским голосом. Объясни хуки и спроси меня перед их одобрением.

Повторяемая последовательность настройки:

1. Команда `doctor` без изменений проверяет выбранный CLI, версию, проигрыватель и настройки. Требуется Codex CLI `0.145.0` или новее; текущие prerelease-суффиксы распознаются.
2. Сохраните голос и язык, проверьте локальный `Stop` и подтвердите, что услышали звук.
3. `review-hooks` показывает точные команды Voice Notify, область одобрения и `approvalDigest`. Попросите одобрить именно эти команды.
4. Только после явного согласия запустите `approve-hooks` с тем же `approvalDigest`. Официальный локальный интерфейс app-server Codex одобряет только проверенные хуки Voice Notify. Изменённые команды требуют новой проверки; хранилище доверия не редактируется напрямую и обход не используется.
5. Полностью закройте и заново запустите Codex, затем услышьте одно включённое реальное событие. Тест настроек или запись об одобрении сами по себе не доказывают работу событий.

Если интерфейс автоматического одобрения недоступен, `setup --open-hooks` в macOS/Linux или `setup -OpenHooks` в Windows открывает терминал CLI. В нём введите `/hooks`, проверьте встроенную команду и явно подтвердите доверие. Затем полностью закройте и заново запустите Codex перед реальным событием. В headless-среде или без средства запуска терминала запустите выбранный CLI вручную и введите `/hooks`.

Сценарии не обновляют Codex и не устанавливают зависимости скрытно. Устаревший CLI можно обновлять через проверенную установку npm или Homebrew лишь с отдельного явного разрешения. Для встроенных в приложение или неизвестных установок используйте их официальный путь обновления. Перед заменой используемого исполняемого файла закройте CLI.

## Настройка

Попросите обычными словами: «Используй женский английский голос», «Выбери мужской японский голос», «Выбери женский русский голос», «Используй мужской упрощённый китайский» или «Отключи звук Voice Notify».

`female` или `male` и корейский/хангыль (`ko`), японский (`ja`), английский (`en`), русский (`ru`), упрощённый китайский (`zh-CN`) сопоставляются настройкам. Без уточнения «китайский» или «中文» означает единственный китайский вариант `zh-CN` (упрощённый китайский, стандартный китайский материкового Китая). Команды из клона:

macOS:

```bash
/bin/sh scripts/voice_notify_config.sh doctor
/bin/sh scripts/voice_notify_config.sh setup --voice female --language ko
/bin/sh scripts/voice_notify_config.sh review-hooks
# Только после явного согласия замените <approvalDigest> текущим полученным значением:
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
# Только после явного согласия замените <approvalDigest> текущим полученным значением:
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
# Только после явного согласия замените <approvalDigest> текущим полученным значением:
python3 scripts/voice_notify_config.py approve-hooks --approve "<approvalDigest>"
python3 scripts/voice_notify_config.py show
python3 scripts/voice_notify_config.py set --voice male --language en
python3 scripts/voice_notify_config.py test --event Stop
python3 scripts/voice_notify_config.py mute
```

По умолчанию: `female`, `ko`, минимальный интервал 450 мс, восемь включённых событий. `PreToolUse` и `PostToolUse` доступны, но выключены по умолчанию. `PermissionRequest` звучит только при реальном запросе разрешения Codex.

## Устранение неполадок

- Сначала запустите `doctor`. Диагностика не меняет настройки, не одобряет хуки и не воспроизводит звук. Вывод может содержать локальные пути: скройте их перед публикацией.
- Если `/hooks` нет, проверьте выбранный CLI и обновите с разрешения пользователя. Версии приложения и отдельно установленного CLI могут отличаться.
- Если слышен только тест, проверьте одобрение, полностью закройте и снова запустите нужный Codex и проверьте включённое реальное событие.
- Если PowerShell блокирует `codex.ps1` или `npm.ps1`, используйте `codex.cmd` или `npm.cmd`. `-ExecutionPolicy Bypass` действует только для запущенного процесса настройки и не меняет системную политику.
- Linux требует Python 3, поддерживаемый проигрыватель и доступное аудиоустройство или сервер. В SSH, контейнерах, WSL и headless-сессиях проигрыватель может существовать без слышимого вывода. Пакеты автоматически не устанавливаются.

## Совместимость

Версия 0.2.0 поддерживает macOS, Windows и Linux. Обычные воспроизведение и настройки macOS не требуют Python; Windows использует встроенный PowerShell; Linux требует Python 3 и один поддерживаемый проигрыватель. Автоматическое одобрение использует встроенный `osascript` JXA в macOS, PowerShell в Windows или Python 3 в Linux и требует официального локального app-server выбранного CLI; иначе используйте ручную проверку `/hooks`. Требуется CLI `0.145.0` или новее. Поддержка платформы не означает подтверждённое прослушивание каждой версии приложения, аудиосистемы или headless-сессии.

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
