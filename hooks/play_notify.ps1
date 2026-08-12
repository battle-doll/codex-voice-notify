param(
    [switch]$Worker,
    [string]$AudioPathBase64,
    [string]$StatePathBase64,
    [int]$IntervalMs = 450
)

$ErrorActionPreference = "SilentlyContinue"
$EventFiles = @{
    SessionStart      = "session-start"
    UserPromptSubmit  = "user-prompt-submit"
    PreToolUse        = "pre-tool-use"
    PostToolUse       = "post-tool-use"
    PermissionRequest = "permission-request"
    PreCompact        = "pre-compact"
    PostCompact       = "post-compact"
    SubagentStart     = "subagent-start"
    SubagentStop      = "subagent-stop"
    Stop              = "stop"
}

function ConvertTo-CanonicalLanguage($Value) {
    if ($Value -isnot [string]) {
        return $null
    }
    switch ($Value) {
        "ko" { return "ko" }
        "ja" { return "ja" }
        "en" { return "en" }
        "ru" { return "ru" }
        "zh-CN" { return "zh-CN" }
        default { return $null }
    }
}

function ConvertFrom-Base64Utf8([string]$Value) {
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Value))
}

function Read-BoundedStandardInput([int]$MaxBytes) {
    if ($MaxBytes -lt 1) {
        return $null
    }

    $InputStream = [Console]::OpenStandardInput()
    $Buffer = New-Object byte[] 8192
    $Captured = New-Object IO.MemoryStream
    try {
        while ($true) {
            # Read at most one byte beyond the limit so oversized producers do
            # not make this process wait for EOF or allocate their full input.
            $Remaining = ([long]$MaxBytes + 1L) - $Captured.Length
            if ($Remaining -le 0) {
                return $null
            }
            $ReadLength = [int][Math]::Min([long]$Buffer.Length, $Remaining)
            $ReadCount = $InputStream.Read($Buffer, 0, $ReadLength)
            if ($ReadCount -eq 0) {
                break
            }
            $Captured.Write($Buffer, 0, $ReadCount)
            if ($Captured.Length -gt $MaxBytes) {
                return $null
            }
        }

        try {
            $StrictUtf8 = [Text.UTF8Encoding]::new($false, $true)
            return $StrictUtf8.GetString($Captured.ToArray())
        }
        catch {
            return $null
        }
    }
    finally {
        $Captured.Dispose()
    }
}

if ($Worker) {
    $AudioPath = ConvertFrom-Base64Utf8 $AudioPathBase64
    $StatePath = ConvertFrom-Base64Utf8 $StatePathBase64
    if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
        exit 0
    }

    $Mutex = New-Object Threading.Mutex($false, "Local\CodexVoiceNotifyPlayback")
    $Acquired = $false
    try {
        $Acquired = $Mutex.WaitOne(0)
        if (-not $Acquired) {
            exit 0
        }

        $Now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        $Previous = 0L
        if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
            [long]::TryParse(
                [IO.File]::ReadAllText($StatePath, [Text.Encoding]::ASCII),
                [ref]$Previous
            ) | Out-Null
        }
        if (($Now - $Previous) -lt [Math]::Max(0, $IntervalMs)) {
            exit 0
        }
        [IO.File]::WriteAllText(
            $StatePath,
            $Now.ToString([Globalization.CultureInfo]::InvariantCulture),
            [Text.Encoding]::ASCII
        )

        $Player = New-Object System.Media.SoundPlayer($AudioPath)
        $Player.PlaySync()
    }
    finally {
        if ($Acquired) {
            $Mutex.ReleaseMutex()
        }
        $Mutex.Dispose()
    }
    exit 0
}

$RawInput = Read-BoundedStandardInput 1048576
if ($null -eq $RawInput) {
    exit 0
}
try {
    $Payload = $RawInput | ConvertFrom-Json
    $EventName = [string]$Payload.hook_event_name
}
catch {
    exit 0
}
if (-not $EventFiles.ContainsKey($EventName)) {
    exit 0
}

$Enabled = $true
$Voice = "female"
$Language = "ko"
$MinimumInterval = 450
$EventEnabled = @("PreToolUse", "PostToolUse") -notcontains $EventName
if ($env:CODEX_VOICE_NOTIFY_CONFIG) {
    $ConfigPath = [IO.Path]::GetFullPath($env:CODEX_VOICE_NOTIFY_CONFIG)
}
else {
    $ConfigPath = Join-Path $HOME ".config\codex-voice-notify\settings.json"
}
if ((Test-Path -LiteralPath $ConfigPath -PathType Leaf) -and
    ((Get-Item -LiteralPath $ConfigPath).Length -le 65536)) {
    try {
        $Settings = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Settings.enabled -is [bool]) {
            $Enabled = $Settings.enabled
        }
        if (@("female", "male") -contains $Settings.voice) {
            $Voice = [string]$Settings.voice
        }
        $CanonicalLanguage = ConvertTo-CanonicalLanguage $Settings.language
        if ($null -ne $CanonicalLanguage) {
            $Language = $CanonicalLanguage
        }
        if ($Settings.min_interval_ms -is [int] -or $Settings.min_interval_ms -is [long]) {
            $MinimumInterval = [Math]::Max(0, [Math]::Min(10000, [int]$Settings.min_interval_ms))
        }
        if ($null -ne $Settings.events) {
            $ConfiguredEvent = $Settings.events.$EventName
            if ($ConfiguredEvent -is [bool]) {
                $EventEnabled = $ConfiguredEvent
            }
        }
    }
    catch {
        # Malformed settings safely fall back to defaults.
    }
}
if (-not $Enabled -or -not $EventEnabled) {
    exit 0
}

$AudioRoot = Join-Path $env:PLUGIN_ROOT "assets\audio"
$AudioPath = Join-Path $AudioRoot "$Voice\$Language\$($EventFiles[$EventName]).wav"
if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
    exit 0
}
$ResolvedRoot = [IO.Path]::GetFullPath($AudioRoot).TrimEnd("\") + "\"
$ResolvedAudio = [IO.Path]::GetFullPath($AudioPath)
if (-not $ResolvedAudio.StartsWith($ResolvedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    exit 0
}

if ($env:PLUGIN_DATA) {
    $RuntimeDirectory = $env:PLUGIN_DATA
}
elseif ($env:LOCALAPPDATA) {
    $RuntimeDirectory = Join-Path $env:LOCALAPPDATA "codex-voice-notify"
}
else {
    $RuntimeDirectory = Join-Path $HOME "AppData\Local\codex-voice-notify"
}
[IO.Directory]::CreateDirectory($RuntimeDirectory) | Out-Null
$StatePath = Join-Path $RuntimeDirectory "playback.timestamp"

if ($env:CODEX_VOICE_NOTIFY_NO_PLAY -eq "1") {
    exit 0
}

$AudioBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($ResolvedAudio))
$StateBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($StatePath))
$WorkerCommand = (
    "& '" + $PSCommandPath.Replace("'", "''") + "'" +
    " -Worker -AudioPathBase64 '" + $AudioBase64 +
    "' -StatePathBase64 '" + $StateBase64 +
    "' -IntervalMs " + $MinimumInterval
)
$EncodedCommand = [Convert]::ToBase64String(
    [Text.Encoding]::Unicode.GetBytes($WorkerCommand)
)
$PowerShell = (Get-Process -Id $PID).Path
Start-Process -FilePath $PowerShell `
    -ArgumentList @("-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", $EncodedCommand) `
    -WindowStyle Hidden | Out-Null
exit 0
