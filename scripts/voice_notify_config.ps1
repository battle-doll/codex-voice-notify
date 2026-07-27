param(
    [Parameter(Position = 0)]
    [ValidateSet("show", "set", "mute", "unmute", "reset", "test", "setup")]
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
    [switch]$DryRun,
    [switch]$SkipAudioTest,
    [switch]$OpenHooks,
    [string]$CodexCommand
)

$ErrorActionPreference = "Stop"
$PluginRoot = Split-Path -Parent $PSScriptRoot
if ($env:CODEX_VOICE_NOTIFY_CONFIG) {
    $ConfigPath = [IO.Path]::GetFullPath($env:CODEX_VOICE_NOTIFY_CONFIG)
    $ConfigDirectory = Split-Path -Parent $ConfigPath
}
else {
    $ConfigDirectory = Join-Path $HOME ".config\codex-voice-notify"
    $ConfigPath = Join-Path $ConfigDirectory "settings.json"
}
$MinimumHooksCodexVersion = [version]"0.145.0"
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
        $Events[$Name] = @("PreToolUse", "PostToolUse") -notcontains $Name
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

function Get-CodexPath([string]$ExplicitPath) {
    if ($ExplicitPath) {
        return [IO.Path]::GetFullPath($ExplicitPath)
    }
    if ($env:CODEX_VOICE_NOTIFY_CODEX) {
        return [IO.Path]::GetFullPath($env:CODEX_VOICE_NOTIFY_CODEX)
    }
    foreach ($Name in @("codex.cmd", "codex.exe", "codex")) {
        $Candidate = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $Candidate) {
            return $Candidate.Source
        }
    }
    return $null
}

function Get-CodexVersionInfo([string]$CodexPath) {
    try {
        $VersionOutput = (& $CodexPath --version 2>&1 | Out-String).Trim()
        $VersionExitCode = $LASTEXITCODE
    }
    catch {
        return $null
    }
    if ($VersionExitCode -ne 0) {
        return $null
    }
    if ($VersionOutput -notmatch "(?i)^\s*(?:openai\s+)?codex(?:-cli)?\s+(?:\(\s*)?v?(\d+)\.(\d+)\.(\d+)\s*\)?\s*$") {
        return $null
    }
    return [pscustomobject]@{
        Version = [version]("$($Matches[1]).$($Matches[2]).$($Matches[3])")
        Output  = $VersionOutput
    }
}

function Open-HookTrustTerminal([string]$CodexPath) {
    $EscapedCodexPath = $CodexPath.Replace("'", "''")
    $EscapedWorkingDirectory = (Get-Location).Path.Replace("'", "''")
    $LaunchCommand = @"
`$Host.UI.RawUI.WindowTitle = "Voice Notify - type /hooks in Codex"
Write-Host ""
Write-Host "Voice Notify opened this new Codex CLI terminal."
Write-Host "Type /hooks here and review the bundled hook."
Write-Host ""
& '$EscapedCodexPath' --no-alt-screen -C '$EscapedWorkingDirectory'
"@
    $EncodedCommand = [Convert]::ToBase64String(
        [Text.Encoding]::Unicode.GetBytes($LaunchCommand)
    )
    $PowerShellPath = (Get-Process -Id $PID).Path
    try {
        Start-Process -FilePath $PowerShellPath `
            -ArgumentList @(
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-NoExit",
                "-EncodedCommand",
                $EncodedCommand
            ) `
            -WindowStyle Normal | Out-Null
    }
    catch {
        return $false
    }
    return $true
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
    "setup" {
        if ($Voice) {
            $Settings.voice = $Voice
        }
        if ($Language) {
            $Settings.language = $Language
        }
        $Settings.enabled = $true

        $ResolvedCodexPath = Get-CodexPath $CodexCommand
        if (-not $ResolvedCodexPath) {
            [Console]::Error.WriteLine(
                "Codex CLI was not found. Install or expose Codex on PATH, then rerun setup."
            )
            exit 3
        }
        $CodexInfo = Get-CodexVersionInfo $ResolvedCodexPath
        if ($null -eq $CodexInfo) {
            [Console]::Error.WriteLine(
                "Could not determine the Codex CLI version from $ResolvedCodexPath."
            )
            exit 3
        }
        Write-Output "Codex CLI: $($CodexInfo.Version) ($ResolvedCodexPath)"
        if ($CodexInfo.Version -lt $MinimumHooksCodexVersion) {
            [Console]::Error.WriteLine((
                "Codex CLI {0} or newer is required for /hooks. Update Codex, then rerun setup." -f
                $MinimumHooksCodexVersion
            ))
            exit 3
        }

        $AudioPath = Join-Path $PluginRoot (
            "assets\audio\$($Settings.voice)\$($Settings.language)\$($EventFiles.Stop).wav"
        )
        if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
            [Console]::Error.WriteLine("Stop audio file is unavailable: $AudioPath")
            exit 1
        }
        Write-Output "Stop audio: $AudioPath"
        if (-not $DryRun -and -not $SkipAudioTest) {
            $Player = New-Object System.Media.SoundPlayer($AudioPath)
            $Player.PlaySync()
        }

        if ($DryRun) {
            Write-Output (
                "Dry run: would save voice={0} language={1}." -f
                $Settings.voice,
                $Settings.language
            )
        }
        else {
            Save-Settings $Settings
        }

        if ($OpenHooks) {
            if ($DryRun) {
                Write-Output (
                    "Dry run: would open a new terminal and start Codex CLI " +
                    "for manual /hooks review."
                )
            }
            else {
                if (Open-HookTrustTerminal $ResolvedCodexPath) {
                    Write-Output (
                        "Started Codex CLI in a new terminal window. Type /hooks " +
                        "in that window, review the Voice Notify hook, and trust it."
                    )
                }
                else {
                    [Console]::Error.WriteLine(
                        "Could not open a new Codex CLI terminal automatically. Start Codex CLI yourself, enter /hooks, and review the Voice Notify hook."
                    )
                    exit 4
                }
            }
        }
        else {
            Write-Output "Next: run Codex, enter /hooks, and review the Voice Notify hook."
        }
        Write-Output "After trust is granted, fully restart Codex before testing lifecycle events."
        exit 0
    }
}
