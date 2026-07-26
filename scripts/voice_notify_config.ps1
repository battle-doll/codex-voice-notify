param(
    [Parameter(Position = 0)]
    [ValidateSet("show", "set", "mute", "unmute", "reset", "test")]
    [string]$Command = "show",
    [ValidateSet("female", "male")]
    [string]$Voice,
    [ValidateSet("ko", "ja", "en")]
    [string]$Language,
    [ValidateSet(
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PermissionRequest",
        "PreCompact",
        "PostCompact",
        "SubagentStart",
        "SubagentStop",
        "Stop"
    )]
    [string]$Event = "Stop",
    [switch]$EnableEvent,
    [switch]$DisableEvent,
    [int]$MinIntervalMs = -1,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$PluginRoot = Split-Path -Parent $PSScriptRoot
$ConfigDirectory = Join-Path $HOME ".config\codex-voice-notify"
$ConfigPath = Join-Path $ConfigDirectory "settings.json"
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

function New-DefaultSettings {
    $Events = [ordered]@{}
    foreach ($Name in $EventFiles.Keys) {
        $Events[$Name] = $true
    }
    return [ordered]@{
        enabled         = $true
        voice           = "female"
        language        = "ko"
        min_interval_ms = 450
        events          = $Events
    }
}

function Get-Settings {
    $Result = New-DefaultSettings
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        return $Result
    }
    try {
        $Candidate = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($Candidate.enabled -is [bool]) {
            $Result.enabled = $Candidate.enabled
        }
        if (@("female", "male") -contains $Candidate.voice) {
            $Result.voice = [string]$Candidate.voice
        }
        if (@("ko", "ja", "en") -contains $Candidate.language) {
            $Result.language = [string]$Candidate.language
        }
        if ($Candidate.min_interval_ms -is [int] -or $Candidate.min_interval_ms -is [long]) {
            $Result.min_interval_ms = [Math]::Max(
                0,
                [Math]::Min(10000, [int]$Candidate.min_interval_ms)
            )
        }
        foreach ($Name in $EventFiles.Keys) {
            $Value = $Candidate.events.$Name
            if ($Value -is [bool]) {
                $Result.events[$Name] = $Value
            }
        }
    }
    catch {
        return New-DefaultSettings
    }
    return $Result
}

function Save-Settings($Settings) {
    [IO.Directory]::CreateDirectory($ConfigDirectory) | Out-Null
    $Temporary = Join-Path $ConfigDirectory ([IO.Path]::GetRandomFileName())
    $Json = $Settings | ConvertTo-Json -Depth 5
    $Utf8NoBom = New-Object Text.UTF8Encoding($false)
    try {
        [IO.File]::WriteAllText($Temporary, $Json + [Environment]::NewLine, $Utf8NoBom)
        Move-Item -LiteralPath $Temporary -Destination $ConfigPath -Force
    }
    finally {
        Remove-Item -LiteralPath $Temporary -Force -ErrorAction SilentlyContinue
    }
    Write-Output "Saved $ConfigPath"
}

$Settings = Get-Settings
switch ($Command) {
    "show" {
        $Settings | ConvertTo-Json -Depth 5
        exit 0
    }
    "reset" {
        Remove-Item -LiteralPath $ConfigPath -Force -ErrorAction SilentlyContinue
        Write-Output "Defaults restored."
        exit 0
    }
    "mute" {
        $Settings.enabled = $false
        Save-Settings $Settings
        exit 0
    }
    "unmute" {
        $Settings.enabled = $true
        Save-Settings $Settings
        exit 0
    }
    "set" {
        if ($Voice) {
            $Settings.voice = $Voice
        }
        if ($Language) {
            $Settings.language = $Language
        }
        if ($MinIntervalMs -ge 0) {
            $Settings.min_interval_ms = [Math]::Min(10000, $MinIntervalMs)
        }
        if ($EnableEvent) {
            $Settings.events[$Event] = $true
        }
        if ($DisableEvent) {
            $Settings.events[$Event] = $false
        }
        Save-Settings $Settings
        exit 0
    }
    "test" {
        if ($Voice) {
            $Settings.voice = $Voice
        }
        if ($Language) {
            $Settings.language = $Language
        }
        $AudioPath = Join-Path $PluginRoot (
            "assets\audio\$($Settings.voice)\$($Settings.language)\$($EventFiles[$Event]).wav"
        )
        if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
            throw "Audio file is unavailable: $AudioPath"
        }
        Write-Output $AudioPath
        if (-not $DryRun) {
            $Player = New-Object System.Media.SoundPlayer($AudioPath)
            $Player.PlaySync()
        }
        exit 0
    }
}
