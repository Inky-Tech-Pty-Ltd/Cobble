#requires -Version 5.1
<#
Daily independent wrapper for Cobble backup watchdog + email heartbeat.
Runs regardless of the 01:00 backup task's success or failure.
No credentials on the Windows command line; SMTP password is in a private
WSL mode-0600 local file, provisioned from 1Password.
#>
[CmdletBinding()]
param(
    [string]$Watchdog = (Join-Path $env:LOCALAPPDATA 'Cobble\check_mckay_backup.ps1'),
    [string]$Sender = '/home/cobbler/.local/bin/send_mckay_backup_heartbeat.py',
    [string]$Report = (Join-Path $env:LOCALAPPDATA 'Cobble\backup-watchdog\latest.json'),
    [string]$StatusDirectory = (Join-Path $env:LOCALAPPDATA 'Cobble\backup-watchdog'),
    [switch]$SelfTest
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-CobbleWslPath {
    param([Parameter(Mandatory)][string]$WindowsPath)
    # Construct a Linux mount path on Windows. Passing a backslash path
    # directly to WSL's native argument parser strips the backslashes.
    # This uses the default /mnt drive mount layout of McKay's Ubuntu WSL.
    $absolute = [IO.Path]::GetFullPath($WindowsPath)
    if ($absolute -notmatch '^([A-Za-z]):\\(.+)$') {
        throw 'Expected a Windows drive-letter path for the backup report'
    }
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2].Replace('\', '/')
    return "/mnt/$drive/$rest"
}

if ($SelfTest) {
    $fixture = 'C:\Users\example\AppData\Local\Cobble\backup-watchdog\latest.json'
    $expected = '/mnt/c/Users/example/AppData/Local/Cobble/backup-watchdog/latest.json'
    if ((ConvertTo-CobbleWslPath $fixture) -ne $expected) {
        throw 'Windows-to-WSL path conversion failed'
    }
    Write-Output 'HEARTBEAT WRAPPER SELF-TEST PASS: path conversion; no network or backups'
    exit 0
}

$watchExit = 99
$started = Get-Date
if (Test-Path -LiteralPath $Watchdog -PathType Leaf) {
    try {
        & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $Watchdog -NoBalloon
        $watchExit = [int]$LASTEXITCODE
    } catch {
        Write-Warning 'Backup watchdog could not execute'
    }
} else {
    Write-Warning 'Backup watchdog script is missing'
}

# A successful process exit cannot legitimise an old report from earlier
# on the same day. The report must have been written by this invocation.
if ($watchExit -eq 0 -or $watchExit -eq 2) {
    try {
        if (-not (Test-Path -LiteralPath $Report -PathType Leaf)) {
            $watchExit = 98
        } elseif ((Get-Item -LiteralPath $Report).LastWriteTimeUtc -lt $started.ToUniversalTime()) {
            $watchExit = 98
        }
    } catch { $watchExit = 98 }
    if ($watchExit -eq 98) {
        Write-Warning 'Watchdog report was not refreshed by this run'
    }
}

# Explicit Windows-to-WSL mount path avoids wsl.exe stripping backslashes.
$wslReport = ''
try {
    $wslReport = ConvertTo-CobbleWslPath $Report
} catch {
    Write-Warning 'Unable to convert Windows report path into WSL mount path'
}

$mailExit = 3
if ($wslReport) {
    try {
        $argsToWsl = @(
            '-d', 'Ubuntu', '-u', 'cobbler', '--',
            '/usr/bin/python3', $Sender, '--send',
            '--report', $wslReport
        )
        if ($watchExit -ne 0 -and $watchExit -ne 2) {
            $argsToWsl += '--watchdog-error'
        }
        & wsl.exe @argsToWsl
        $mailExit = [int]$LASTEXITCODE
    } catch {
        Write-Warning 'Cannot execute WSL email helper'
    }
} else {
    Write-Warning 'No WSL path; daily heartbeat could not be sent'
}

# Metadata-only delivery audit; SMTP acceptance does not prove inbox arrival.
try {
    New-Item -ItemType Directory -Path $StatusDirectory -Force | Out-Null
    [pscustomobject]@{
        checked_at = (Get-Date).ToString('o')
        watchdog_exit = $watchExit
        smtp_exit = $mailExit
        outcome = $(if ($mailExit -eq 0) { 'accepted_by_smtp' } else { 'email_not_confirmed' })
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $StatusDirectory 'heartbeat-last.json') -Encoding UTF8
} catch {
    Write-Warning 'Unable to persist heartbeat delivery status'
}

if ($mailExit -ne 0) {
    Write-Warning 'Daily heartbeat was not accepted by SMTP; check credentials/connectivity'
    exit 3
}
if ($watchExit -ne 0) { exit 2 }
exit 0
