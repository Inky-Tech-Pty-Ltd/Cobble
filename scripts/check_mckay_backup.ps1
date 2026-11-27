#requires -Version 5.1
<#
Read-only Cobble backup watchdog. It reads local files, log success markers
and Windows Cloud Files sync metadata; it never opens or changes an archive.
A Windows 'in sync' flag is NOT independent proof of off-machine recovery.
#>
[CmdletBinding()]
param(
    [string]$BackupDirectory = '\\wsl.localhost\Ubuntu\home\cobbler\cobble-data-backups',
    [string]$ICloudDirectory = (Join-Path $env:USERPROFILE 'iCloudDrive\CobbleBackups'),
    [string]$StatusDirectory = (Join-Path $env:LOCALAPPDATA 'Cobble\backup-watchdog'),
    [datetime]$AsOf = (Get-Date),
    [ValidateRange(1, 14)][int]$LocalLookbackDays = 3,
    [ValidateRange(1, 60)][int]$CloudLookbackDays = 30,
    [ValidateRange(1, 168)][int]$OverdueHours = 24,
    [switch]$SelfTest,
    [switch]$NoBalloon
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-CobbleCloudState {
    param([string]$Path)
    if (-not ('CobbleCloudFileStatus' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class CobbleCloudFileStatus {
    [StructLayout(LayoutKind.Sequential)]
    public struct FileTagInfo {
        public uint FileAttributes;
        public uint ReparseTag;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFile(
        string filename, uint access, uint share, IntPtr security,
        uint disposition, uint flags, IntPtr templateFile);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetFileInformationByHandleEx(
        SafeFileHandle handle, int infoClass, out FileTagInfo info, uint size);
    [DllImport("CldApi.dll")]
    static extern uint CfGetPlaceholderStateFromAttributeTag(
        uint attributes, uint reparseTag);

    public static string Check(string path) {
        using (SafeFileHandle h = CreateFile(
            path, 0x80, 7, IntPtr.Zero, 3, 0x00200000, IntPtr.Zero)) {
            if (h.IsInvalid) return "unknown-open-" + Marshal.GetLastWin32Error();
            FileTagInfo info;
            if (!GetFileInformationByHandleEx(h, 9, out info, 8))
                return "unknown-metadata-" + Marshal.GetLastWin32Error();
            uint state = CfGetPlaceholderStateFromAttributeTag(
                info.FileAttributes, info.ReparseTag);
            if (state == 0xffffffff) return "unknown-invalid";
            if ((state & 1) == 0) return "unknown-not-placeholder";
            return (state & 8) != 0 ? "synced" : "pending";
        }
    }
}
'@
    }
    try {
        return [CobbleCloudFileStatus]::Check($Path)
    } catch {
        return 'unknown-api-error'
    }
}

function Get-CobbleBackupHealth {
    param(
        [string]$LocalDir, [string]$CloudDir, [datetime]$Now,
        [int]$LocalDays, [int]$CloudDays, [int]$GraceHours,
        [scriptblock]$CloudReader
    )
    $alerts = [System.Collections.Generic.List[string]]::new()
    $details = [System.Collections.Generic.List[object]]::new()
    $today = $Now.Date
    if (-not (Test-Path -LiteralPath $LocalDir -PathType Container)) {
        $alerts.Add('Local backup directory is unavailable')
    }
    if (-not (Test-Path -LiteralPath $CloudDir -PathType Container)) {
        $alerts.Add('iCloud Drive backup directory is unavailable')
    }

    # Independently detect missing nightly archives and failed/missing logs.
    for ($i = 0; $i -lt $LocalDays; $i++) {
        $day = $today.AddDays(-$i).ToString('yyyy-MM-dd')
        $name = "cobble-$day-full.tar.gz.age"
        if (-not (Test-Path -LiteralPath (Join-Path $LocalDir $name) -PathType Leaf)) {
            $alerts.Add("Missing local backup: $day")
            continue
        }
        $logDir = Join-Path $LocalDir 'logs'
        $logs = @()
        if (Test-Path -LiteralPath $logDir -PathType Container) {
            $logs = @(Get-ChildItem -LiteralPath $logDir -Filter "backup-$day-*.log" -File)
        }
        $success = $false
        foreach ($log in $logs) {
            if (Select-String -LiteralPath $log.FullName -Pattern '^SUCCESS:' -Quiet) {
                $success = $true
                break
            }
        }
        if (-not $success) { $alerts.Add("No successful backup log: $day") }
    }

    # Compare filenames and sizes, then consult the cloud-provider metadata.
    # No archive payload is read, hashed or hydrated.
    if (Test-Path -LiteralPath $LocalDir -PathType Container) {
        foreach ($local in (Get-ChildItem -LiteralPath $LocalDir -Filter 'cobble-*-full.tar.gz.age' -File)) {
            if ($local.Name -notmatch '^cobble-(\d{4}-\d{2}-\d{2})-full\.tar\.gz\.age$') { continue }
            $day = [datetime]::MinValue
            if (-not [datetime]::TryParseExact(
                $Matches[1], 'yyyy-MM-dd',
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::None,
                [ref]$day)) { continue }
            if ($day -lt $today.AddDays(1 - $CloudDays) -or $day -gt $today) { continue }

            $cloud = Join-Path $CloudDir $local.Name
            $state = 'missing'
            $sameLength = $false
            if (Test-Path -LiteralPath $cloud -PathType Leaf) {
                $cloudItem = Get-Item -LiteralPath $cloud
                $sameLength = ($cloudItem.Length -eq $local.Length)
                if (-not $sameLength) {
                    $state = 'size-mismatch'
                } else {
                    try { $state = & $CloudReader $cloud }
                    catch { $state = 'unknown-api-error' }
                    if ([string]::IsNullOrWhiteSpace([string]$state)) {
                        $state = 'unknown-empty'
                    }
                }
            }
            $details.Add([pscustomobject]@{
                date = $day.ToString('yyyy-MM-dd')
                file = $local.Name
                local_bytes = $local.Length
                cloud_state = [string]$state
                cloud_length_matches = $sameLength
            })
            # The nominal backup start is 01:00 local time. This is deliberately
            # independent of changing iCloud sync and modified timestamps.
            $ageHours = ($Now - $day.AddHours(1)).TotalHours
            if ($state -eq 'size-mismatch') {
                $alerts.Add("Cloud copy has different length: $($local.Name)")
            } elseif ($state -ne 'synced' -and $ageHours -ge $GraceHours) {
                $alerts.Add("Cloud delivery unconfirmed ($state): $($local.Name)")
            }
        }
    }

    [pscustomobject]@{
        checked_at_local = $Now.ToString('o')
        status = $(if ($alerts.Count -eq 0) { 'OK_LOCAL_AND_PROVIDER_SYNC' } else { 'WARNING' })
        qualification = 'Local Windows sync-provider report only; independent retrieval not established'
        alerts = @($alerts.ToArray())
        archives = @($details.ToArray())
    }
}

function Invoke-CobbleSelfTest {
    $root = Join-Path ([IO.Path]::GetTempPath()) ("cobble-backup-check-" + [guid]::NewGuid().ToString('N'))
    $local = Join-Path $root 'local'
    $cloud = Join-Path $root 'cloud'
    $now = [datetime]'2026-11-27T09:00:00'
    $states = @{}
    try {
        New-Item -ItemType Directory -Path (Join-Path $local 'logs'), $cloud -Force | Out-Null
        foreach ($i in 0..2) {
            $day = $now.Date.AddDays(-$i).ToString('yyyy-MM-dd')
            $name = "cobble-$day-full.tar.gz.age"
            Set-Content -LiteralPath (Join-Path $local $name) -Value 'fixture'
            Set-Content -LiteralPath (Join-Path $cloud $name) -Value 'fixture'
            Set-Content -LiteralPath (Join-Path $local "logs/backup-$day-010001.log") -Value 'SUCCESS: fixture'
            $states[$name] = 'synced'
        }
        $reader = { param($path) $states[[IO.Path]::GetFileName($path)] }
        $ok = Get-CobbleBackupHealth $local $cloud $now 3 3 24 $reader
        if ($ok.alerts.Count -ne 0) { throw "Clean test failed: $($ok.alerts -join '; ')" }
        $old = $now.Date.AddDays(-2).ToString('yyyy-MM-dd')
        $states["cobble-$old-full.tar.gz.age"] = 'pending'
        $pending = Get-CobbleBackupHealth $local $cloud $now 3 3 24 $reader
        if ($pending.alerts.Count -ne 1 -or $pending.alerts[0] -notmatch 'Cloud delivery unconfirmed') {
            throw 'Overdue cloud upload was not detected'
        }
        $today = $now.Date.ToString('yyyy-MM-dd')
        Remove-Item -LiteralPath (Join-Path $local "cobble-$today-full.tar.gz.age")
        $missing = Get-CobbleBackupHealth $local $cloud $now 3 3 24 $reader
        if (@($missing.alerts | Where-Object { $_ -match 'Missing local backup' }).Count -eq 0) {
            throw 'Missing nightly backup was not detected'
        }
        # Exercise the real Windows DLL/P-Invoke path without cloud credentials
        # or any real backup. A plain local text file is not a cloud placeholder.
        $plain = Join-Path $local 'not-a-cloud-file.txt'
        Set-Content -LiteralPath $plain -Value 'fixture'
        $native = Get-CobbleCloudState $plain
        if ($native -ne 'unknown-not-placeholder') {
            throw "Unexpected native Cloud Files result on local fixture: $native"
        }
        Write-Output 'BACKUP WATCHDOG SELF-TEST PASS: clean, overdue cloud, missing night, native API'
    } finally {
        Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($SelfTest) {
    Invoke-CobbleSelfTest
    exit 0
}

$parameters = @{
    LocalDir = $BackupDirectory
    CloudDir = $ICloudDirectory
    Now = $AsOf
    LocalDays = $LocalLookbackDays
    CloudDays = $CloudLookbackDays
    GraceHours = $OverdueHours
    CloudReader = { param($path) Get-CobbleCloudState $path }
}
try {
    $report = Get-CobbleBackupHealth @parameters
} catch {
    # Even a filesystem or provider inspection failure must leave an alarm
    # record, rather than silently preventing status persistence.
    $report = [pscustomobject]@{
        checked_at_local = $AsOf.ToString('o')
        status = 'WARNING'
        qualification = 'Watchdog inspection failed; off-machine recovery not verified'
        alerts = @("Watchdog inspection error: $($_.Exception.GetType().Name)")
        archives = @()
    }
}

# Persistent metadata-only evidence even when no user is watching the screen.
New-Item -ItemType Directory -Path $StatusDirectory -Force | Out-Null
$latest = Join-Path $StatusDirectory 'latest.json'
$history = Join-Path $StatusDirectory 'history.jsonl'
$encoded = $report | ConvertTo-Json -Depth 6 -Compress
Set-Content -LiteralPath $latest -Value $encoded -Encoding UTF8
Add-Content -LiteralPath $history -Value $encoded -Encoding UTF8
Write-Output ("Cobble backup watchdog: " + $report.status)
Write-Output ("Archives inspected: " + $report.archives.Count)
foreach ($warning in $report.alerts) { Write-Warning $warning }

if ($report.alerts.Count -gt 0 -and -not $NoBalloon) {
    # Best-effort Windows balloon, not guaranteed in a headless session.
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $notice = New-Object System.Windows.Forms.NotifyIcon
        try {
            $notice.Icon = [System.Drawing.SystemIcons]::Warning
            $notice.Visible = $true
            $notice.BalloonTipTitle = 'Cobble backup warning'
            $notice.BalloonTipText = ('Backup delivery needs attention. See ' + $latest)
            $notice.ShowBalloonTip(10000)
            Start-Sleep -Seconds 5
        } finally { $notice.Dispose() }
    } catch {
        Write-Warning 'Desktop notification unavailable; persistent report and nonzero exit remain.'
    }
}
if ($report.alerts.Count -gt 0) { exit 2 }
exit 0
