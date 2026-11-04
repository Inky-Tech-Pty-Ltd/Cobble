# Hosting filesystem sync: versioned custody and news

This is source acquisition, **not** memory indexing or graph construction.
McKay's existing captures are at:
- `~/cobble-data/hosting/inkytech/`
- `~/cobble-data/hosting/villagelink/`

`scripts/sync_hosting_filesystems.py` refreshes them using rsync over the
already-authorised dedicated SSH keys. It **never writes to the hosting servers**.

## Manual test on McKay (Ubuntu WSL)

```sh
cd ~/Cobble
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_sync_hosting_filesystems.py' -v
python3 scripts/sync_hosting_filesystems.py --dry-run
python3 scripts/sync_hosting_filesystems.py --source inkytech
python3 scripts/sync_hosting_filesystems.py --source villagelink
```

Review the dry run first. `--source all` (the default) runs both sources.
The endpoints, exclusions and key locations are fixed in the script.
Inky Tech uses `~/.ssh/cobble_inkytech` and its custom remote
`/home12/inkytech/.local/bin/rsync`; Village Link uses
`~/.ssh/cobble_villagelink` and system rsync. SSH host keys must
already be trusted. Requires Python 3.11+, `ssh` and `rsync`.
Authentication is noninteractive. No private credentials belong in Git.

## Local layout

```text
~/cobble-data/
  hosting/
    inkytech/                       Current mirror
    villagelink/                    Current mirror
    history/inkytech/<run>/refresh/  Superseded file contents
    history/inkytech/<run>/finalise/ Deleted and second-pass replaced contents
    history/villagelink/<run>/...    Same for Village Link
    news/inkytech/<run>.json        File changes and status
    news/villagelink/<run>.json
  logs/hosting-sync/.sync.lock
```

Each run uses a UTC timestamp plus a random suffix. The script creates
owner-only directories and a process lock that prevents overlapping instances.
This material is private, including the file names in news. It sits within
the existing encrypted backup scope; the script does not itself run the backup.

The first rsync pass updates files **without deleting locally**. Only if it
succeeds does the second pass delete files absent upstream. Both use
`--backup --backup-dir` with separate phase directories, preserving previous
contents of overwritten and deleted files. If rsync fails, exit status is
nonzero and a `status: failed` news file is written; the mirror can be
partially refreshed. Inspect and rerun rather than treating a failed snapshot
as complete. This is not a transactional filesystem snapshot.

Exclusions match initial custody: top-level `mail/` on both accounts, and
Village Link's inaccessible `public_ftp/.ftpquota`. Symlinks are preserved
as symlinks, never traversed. Live MediaWiki and WordPress MySQL databases
**are not exported by rsync** and require separate database acquisition.
This mechanism does not establish historical completeness before initial capture.

## Interpreting news

News records the added, modified and deleted relative paths and counts, plus
status and completion time. Comparison is based on local file size, timestamp,
mode, link target and directory presence. Directory metadata can appear too.
No file bodies, text diffs or remote secrets are intentionally included in
news; full earlier contents are stored privately in `history`.

Rsync's default quick-check uses file size and modification time. It does
**not** cryptographically verify every byte: same-size, same-timestamp changes
may go unnoticed. Live files may change between the two passes, and a hosting
bookkeeping file like `.dns` can generate unimportant news. A permissions
error may leave partial results and must be investigated. Old versions remain
in history; they are not automatically pruned.

## Scheduling

GitHub Actions tests the script against **local temporary directories** with
real rsync, without credentials or network contact. Before installing a new
Windows Task Scheduler job, check the first live run and news output. Choose
a time that fits around the existing 23:00 GitHub sync and 01:00 encrypted
backup; a merge does **not** install a schedule or begin remote acquisition.

## Unattended sync on McKay (Windows 11 / Ubuntu WSL)

`scripts/run_hosting_sync.sh` runs both sources through the Python
synchroniser and writes a private timestamped log under
`~/cobble-data/logs/hosting-sync/sync-*.log`. The Python synchroniser
already holds a non-blocking per-run lock in that directory, so overlapping
hosting runs are rejected. Both scripts propagate a nonzero status on failure.

After merging this change, verify the scheduled entry point manually from
**Ubuntu WSL**, before creating a Windows schedule:

```bash
cd ~/Cobble
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_run_hosting_sync.py' -v
bash scripts/run_hosting_sync.sh --dry-run
ls -t ~/cobble-data/logs/hosting-sync/sync-*.log | head -n 1
tail -n 30 "$(ls -t ~/cobble-data/logs/hosting-sync/sync-*.log | head -n 1)"
```

Install the following job from **Windows PowerShell** under the Windows
account owning the Ubuntu WSL distribution, not from Ubuntu. The proposed
time is **midnight Sydney/Windows local time**, after the 23:00 GitHub job
and before the existing 01:00 encrypted backup. A 45-minute run limit leaves
some separation before backup, but cannot guarantee consistency if an earlier
job overruns, Windows sleeps, or a delayed task starts late.

```powershell
$taskName = 'Cobble - Daily Hosting Sync'
$action = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\wsl.exe" -Argument '-d Ubuntu -u cobbler -- /bin/bash /home/cobbler/Cobble/scripts/run_hosting_sync.sh'
$trigger = New-ScheduledTaskTrigger -Daily -At 00:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 45)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Versioned Cobble capture and news from Inky Tech and Village Link hosting'
```

To test the installed schedule from PowerShell:

```powershell
Start-ScheduledTask -TaskName 'Cobble - Daily Hosting Sync'
Get-ScheduledTaskInfo -TaskName 'Cobble - Daily Hosting Sync'
```

Then inspect the latest private Ubuntu log for both sources reporting
`complete` and a final `exit=0`. The task is **not installed by
merging this PR**. The system can only run while the Windows/WSL machine,
network and SSH credentials are available. Task Scheduler's
`StartWhenAvailable` is opportunistic, not a guaranteed catch-up.
