# McKay backup delivery watchdog

**Operational status (28 November 2026):** Installed and calibrated on McKay; the
real Windows provider reported 11 November as synced and 13/27 November as
pending during the observed queue. The alarm detected 14 overdue uploads.
The separate daily **09:00 Backup Delivery Heartbeat** Windows task now runs
this watchdog, emails OK or WARNING, and delivered an independently observed
OK email on 28 November. **Do not additionally install a second standalone
09:00 watchdog task.** The original setup procedure below is retained as
historical rollout guidance.

The independently downloaded 27 November archive was restored successfully
on Bogong on 28 November: [see the dated recovery evidence](history/bogong-independent-recovery-2026-11-28.md).

## Why

On 27 November 2026, nightly encrypted backups successfully wrote
`~/cobble-data-backups` and copied into McKay's local iCloud Drive folder.
However, iCloud.com on independent laptop Bogong showed no newer archive than
11 November. The iCloud for Windows app demanded Apple Account verification
and reported an upload backlog. A tiny fresh probe file synchronised after
verification; large archives remained pending. The 12 November archive and
its run log were absent from local storage. Task Scheduler operational history
was disabled, so the missed run's cause is unknown.

The existing `scripts/run_scheduled_backup.sh` and `scripts/backup_mckay.sh`
are presently **McKay-local**, not versioned on `main`; their recovery and
reconciliation belong to the wider disaster-recovery audit.

## Scope and limitations

`scripts/check_mckay_backup.ps1` is an independent **read-only** Windows
PowerShell 5.1 watchdog. It:

- Checks archive presence and a `SUCCESS:` line in local backup logs for the
  most recent three calendar dates (run it **after** the 01:00 backup).
- Checks local and iCloud Drive copies have matching reported file lengths.
- Uses the native Windows Cloud Files API
  (`CfGetPlaceholderStateFromAttributeTag`) to ask whether the cloud
  provider reports the file `IN_SYNC`. Checks archives from the last 30 days.
- Warns when an archive remains pending, missing or unknown 24 hours after
  its nominal 01:00 backup time; immediately warns on size mismatch.
- Writes metadata-only `latest.json` and append-only `history.jsonl` under
  `%LOCALAPPDATA%\Cobble\backup-watchdog` and returns process exit code 2
  on warnings; offers a best-effort Windows notification balloon.

It does **not** read/decrypt/hydrate archive bytes, restart services, alter
Task Scheduler, authenticate to iCloud.com, or call supplier APIs.
A green `IN_SYNC` bit is *only the local provider's claim*; it is not evidence
that Bogong can actually download, decrypt and restore the archive.
A notification balloon is not guaranteed when no desktop user is logged in.
The persistent local status record and task exit code can also disappear with
McKay. True independent alerting will need a separate off-machine monitor.

## Offline test (McKay PowerShell)

After reviewing and merging the candidate, and updating McKay's checkout:

```powershell
$src = '\\wsl.localhost\Ubuntu\home\cobbler\Cobble\scripts\check_mckay_backup.ps1'
& $src -SelfTest
```

Expect `BACKUP WATCHDOG SELF-TEST PASS` (three test cases: healthy, overdue
cloud file, missing nightly archive). Fixtures are temporary **tiny** text
files under Windows Temp, not real backups.

## Calibrate on real iCloud files

While the November backlog still exists, run:

```powershell
& $src -NoBalloon
$LASTEXITCODE
Get-Content "$env:LOCALAPPDATA\Cobble\backup-watchdog\latest.json" |
  ConvertFrom-Json |
  Select-Object status,alerts
```

Expected: `WARNING` and at least the still-pending archives (plus any other
missing or unknown results). **Do not assume the API works with iCloud for
Windows until this comparison agrees with Explorer's green tick / blue arrows.**
If the states are all `unknown-`, inspect the metadata/API error and keep
the watchdog *unscheduled*. Never reinterpret errors as `synced`.

After one large archive eventually completes, repeat and verify that the file
changes to `synced`. The alarm must then continue to report remaining overdue
archives and clear only after local and Windows-provider checks are healthy.

## Suggested independent Windows schedule — only after calibration

Copy the reviewed script to a Windows-owned, stable location, so the watchdog
can work even if the WSL filesystem has to be investigated:

```powershell
$dir = Join-Path $env:LOCALAPPDATA 'Cobble'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
Copy-Item -LiteralPath $src -Destination (Join-Path $dir 'check_mckay_backup.ps1')
$installed = Join-Path $dir 'check_mckay_backup.ps1'
& $installed -SelfTest
```

Once approved, install a **separate** Windows Task Scheduler task at 09:00
Sydney/Windows local time, using the interactive Windows user account.
Do not create it as SYSTEM or through a credential that lacks access to
`\\wsl.localhost\Ubuntu` or the signed-in iCloud Drive.

```powershell
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument (
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $installed + '"'
)
$trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Cobble - Backup Delivery Watchdog' `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Independent check of nightly backup presence and cloud sync backlog'
```

Manually run the task and check `latest.json`, the Task Scheduler
`LastTaskResult`, and the Windows notification. PowerShell exits 2 when
unhealthy; `0` when checks are healthy. Re-copy the script after upgrades.

**Known limitations:** Task Scheduler can fail to run, Windows can sleep, the
user may not see an interactive balloon, and iCloud may falsely report
`IN_SYNC`. None of these is an independent remote alarm. The **independent data-recovery** milestone has now passed on Bogong (28 November;
see the linked evidence above). A complete replacement-host/service rebuild and
an off-machine monitoring system are not yet demonstrated.

## References

- Microsoft `CF_PLACEHOLDER_STATE`:
  https://learn.microsoft.com/en-us/windows/win32/api/cfapi/ne-cfapi-cf_placeholder_state
- Microsoft `CfGetPlaceholderStateFromAttributeTag`:
  https://learn.microsoft.com/en-us/windows/win32/api/cfapi/nf-cfapi-cfgetplaceholderstatefromattributetag
