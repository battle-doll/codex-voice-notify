param(
    [Parameter(Position = 0)]
    [ValidateSet("show", "set", "mute", "unmute", "reset", "test", "setup", "doctor", "review-hooks", "approve-hooks")]
    [string]$Command = "show",
    [ValidateSet("female", "male")]
    [string]$Voice,
    [ValidateSet("ko", "ja", "en", "ru", "zh-CN")]
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
    [string]$CodexCommand,
    [string]$Approve
)

$ErrorActionPreference = "Stop"
$PluginRoot = Split-Path -Parent $PSScriptRoot
if (@("doctor", "review-hooks", "approve-hooks") -contains $Command) {
    $HookArguments = @{ Action = $Command; PluginRoot = $PluginRoot }
    if ($CodexCommand) { $HookArguments.Codex = $CodexCommand }
    if ($Approve) { $HookArguments.Approve = $Approve }
    & (Join-Path $PSScriptRoot "voice_notify_hooks.ps1") @HookArguments
    exit $LASTEXITCODE
}
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
        $CanonicalLanguage = ConvertTo-CanonicalLanguage $Candidate.language
        if ($null -ne $CanonicalLanguage) {
            $Result.language = $CanonicalLanguage
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
        return (Resolve-NativeVersionProbePath ([IO.Path]::GetFullPath($ExplicitPath)))
    }
    if ($env:CODEX_VOICE_NOTIFY_CODEX) {
        return (Resolve-NativeVersionProbePath ([IO.Path]::GetFullPath($env:CODEX_VOICE_NOTIFY_CODEX)))
    }
    if ($env:CODEX_CLI_PATH -and (Test-Path -LiteralPath $env:CODEX_CLI_PATH -PathType Leaf)) {
        return (Resolve-NativeVersionProbePath ([IO.Path]::GetFullPath($env:CODEX_CLI_PATH)))
    }
    foreach ($Name in @("codex.cmd", "codex.exe", "codex")) {
        $Candidate = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $Candidate) {
            return (Resolve-NativeVersionProbePath $Candidate.Source)
        }
    }
    return $null
}

function Resolve-NativeVersionProbePath([string]$Path) {
    # Resolve recognized npm Codex shims from package data, never script text.
    # Unrecognized wrappers retain the existing compatibility probe below.
    if (@('.cmd','.bat','.ps1') -notcontains [IO.Path]::GetExtension($Path).ToLowerInvariant() -or
        [IO.Path]::GetFileNameWithoutExtension($Path).ToLowerInvariant() -ne 'codex') { return $Path }
    $Architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $Architecture) { $Architecture = $env:PROCESSOR_ARCHITECTURE }
    if (@('ARM64','aarch64') -contains $Architecture) { $Target = 'aarch64-pc-windows-msvc'; $Package = 'codex-win32-arm64' }
    else { $Target = 'x86_64-pc-windows-msvc'; $Package = 'codex-win32-x64' }
    $Directory = Split-Path -Parent $Path
    $Scopes = @((Join-Path $Directory 'node_modules/@openai'))
    if ([IO.Path]::GetFileName($Directory) -eq '.bin') { $Scopes += (Join-Path (Split-Path -Parent $Directory) '@openai') }
    foreach ($Scope in $Scopes) {
        $Main = Join-Path $Scope 'codex'; $ManifestPath = Join-Path $Main 'package.json'
        try {
            if ((Get-Item -LiteralPath $ManifestPath).Length -gt 65536) { continue }
            if (([IO.File]::ReadAllText($ManifestPath) | ConvertFrom-Json).name -cne '@openai/codex') { continue }
        } catch { continue }
        foreach ($Root in @((Join-Path $Scope $Package), (Join-Path $Main ('node_modules/@openai/' + $Package)), $Main)) {
            foreach ($Location in @('bin','codex')) {
                $NativePath = Join-Path $Root ('vendor/' + $Target + '/' + $Location + '/codex.exe')
                if (Test-Path -LiteralPath $NativePath -PathType Leaf) { return [IO.Path]::GetFullPath($NativePath) }
            }
        }
    }
    return $Path
}

function Invoke-NativeVersionProbe([string]$CodexPath) {
    $Process = [Diagnostics.Process]::new()
    $Started = $false
    try {
        $Info = [Diagnostics.ProcessStartInfo]::new()
        $Info.FileName = $CodexPath; $Info.Arguments = '--version'
        $Info.UseShellExecute = $false; $Info.CreateNoWindow = $true
        $Info.RedirectStandardInput = $true; $Info.RedirectStandardOutput = $true; $Info.RedirectStandardError = $true
        $Utf8 = [Text.UTF8Encoding]::new($false, $true)
        $Info.StandardOutputEncoding = $Utf8; $Info.StandardErrorEncoding = $Utf8
        [Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
        $Process.StartInfo = $Info
        $Watch = [Diagnostics.Stopwatch]::StartNew()
        $Started = $Process.Start()
        if (-not $Started) { return $null }
        $Process.StandardInput.Close()
        # Drain both streams concurrently; a warning cannot block stdout.
        $OutputTask = $Process.StandardOutput.ReadToEndAsync()
        $ErrorTask = $Process.StandardError.ReadToEndAsync()
        $Remaining = [Math]::Max(0, 20000 - [int]$Watch.ElapsedMilliseconds)
        if (-not $Process.WaitForExit($Remaining)) { return $null }
        $Remaining = [Math]::Max(0, 20000 - [int]$Watch.ElapsedMilliseconds)
        # EOF can be delayed even after the parent exits. It shares the deadline.
        if (-not [Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($OutputTask, $ErrorTask), $Remaining)) { return $null }
        if ($Process.ExitCode -ne 0) { return $null }
        $Output = $OutputTask.GetAwaiter().GetResult()
        if ($Output.Length -gt 65536) { return $null }
        return $Output.Trim()
    } catch { return $null }
    finally {
        if ($Started) {
            try {
                if (-not $Process.HasExited) {
                    if ($Process.GetType().GetMethod('Kill', [type[]]@([bool]))) { $Process.Kill($true) }
                    else { $Process.Kill() }
                    $null = $Process.WaitForExit(1000)
                }
            } catch {}
        }
        $Process.Dispose()
    }
}

function Get-CodexVersionInfo([string]$CodexPath) {
    if ([IO.Path]::GetExtension($CodexPath).ToLowerInvariant() -eq '.exe') {
        $VersionOutput = Invoke-NativeVersionProbe $CodexPath
        if ($null -eq $VersionOutput) { return $null }
        $VersionExitCode = 0
    }
    else {
    $PreviousErrorActionPreference = $ErrorActionPreference
    try {
        # Windows PowerShell 5.1 turns native stderr into error records. Only
        # this read-only probe tolerates warnings; stdout and exit status still
        # have to match the Codex version contract.
        $ErrorActionPreference = 'Continue'
        $VersionOutput = (& $CodexPath --version 2>$null | Out-String).Trim()
        $VersionExitCode = $LASTEXITCODE
    }
    catch {
        return $null
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
    }
    if ($VersionExitCode -ne 0) {
        return $null
    }
    if ($VersionOutput -notmatch "(?i)^\s*(?:openai\s+)?codex(?:-cli)?\s+(?:\(\s*)?v?(\d+)\.(\d+)\.(\d+)(?:-[0-9a-z]+(?:[.-][0-9a-z]+)*)?(?:\+[0-9a-z]+(?:[.-][0-9a-z]+)*)?\s*\)?\s*$") {
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
if ($Language) {
    $Language = ConvertTo-CanonicalLanguage $Language
}
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
