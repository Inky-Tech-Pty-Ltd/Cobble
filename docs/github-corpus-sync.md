# Organisation-wide GitHub corpus sync

`bash scripts/sync_github_corpus.sh` discovers the repositories visible to the
authenticated GitHub CLI in `Inky-Tech-Pty-Ltd`, including newly created and
private repositories that the account can read. For each repository it refreshes
a **dedicated source checkout**, calls Cobble's existing Git archive importer,
then calls the GitHub conversation importer (issues, PRs and Discussions).

From McKay's Ubuntu environment, with GitHub CLI authentication and the Cobble
Python environment available:

```sh
cd ~/Cobble
git pull --ff-only
bash scripts/sync_github_corpus.sh --dry-run
bash scripts/sync_github_corpus.sh
```

The script can be run from any directory. Defaults are:

- Archive: `~/cobble-data/github/` (outside Git).
- Disposable source checkouts: `~/cobble-source-checkouts/` (not the developer's
  own `~/Cobble` or `~/InkyBooks` checkout).
- Organisation: `Inky-Tech-Pty-Ltd`.

Use `--org`, `--store` and `--checkouts` to override these paths or the owner.
`--dry-run` discovers repositories and prints its intended actions without
writing files. Private repositories require the authenticated account to have
read access; the conversation importer also requires authenticated access to
Discussions. Do not pass tokens as command arguments, copy them into scripts,
or store GitHub archive material in the Cobble repository.

On a subsequent run, a dedicated checkout is fetched and fast-forwarded rather
than reset. If it has local edits, diverged commits, or the directory is not a
Git checkout, the script stops instead of overwriting it. This is intentionally
conservative. The Git archive retains prior captured HEAD references; the
conversation importer retains immutable, versioned snapshots. The final count
reports **new conversation-version files**, not messages or threads.

The command fails visibly if repository discovery, clone/fetch, either importer,
or archival checks fail. Already archived snapshots are retained, so a failure
can leave a partially refreshed organisation corpus. Re-running is supported.
This tool is designed for manual use today; it does not install a scheduler,
coordinate simultaneous invocations, or create Cobble memory graphs.

**Completeness limits:** only repositories visible to the authenticated user
are enumerated (up to 1,000 per invocation). The Git importer archives Git
objects and refs observed from the checkout, not Git LFS binaries or submodule
contents; the conversation importer does not download attached binaries or
recover deleted/unavailable messages. API acquisition is not an atomic
organisation-wide snapshot. Source-reported timestamps and authorship are
evidence, not verified identity claims. The archive may contain sensitive
content and Git history may include secrets: keep it private and include it in
an encrypted off-device backup strategy. The script changes local files only;
it never pushes to GitHub.

This is **source acquisition**, deliberately independent of arenas, hypothesis
links, memory addresses, salience and any proposed memory graph architecture.

## Unattended daily sync on McKay (Windows 11 / Ubuntu WSL)

The checked-in `scripts/run_github_sync.sh` is a narrow operational wrapper
around the existing importer. It saves a private timestamped log under
`~/cobble-data/logs/github-sync/`, takes a non-blocking `flock` lock so
two scheduled runs cannot overlap, and propagates failures to Task Scheduler.
Exit code 75 means an already-running sync prevented another invocation.
It does **not** change the importer or update the Cobble checkout.

From Ubuntu, verify the wrapper before installing a schedule:

```bash
cd ~/Cobble
bash scripts/run_github_sync.sh --dry-run
ls -t ~/cobble-data/logs/github-sync/sync-*.log | head -n 1
tail -n 25 "$(ls -t ~/cobble-data/logs/github-sync/sync-*.log | head -n 1)"
```

The wrapper logs even a dry run, but forwards `--dry-run` to the importer,
so no archive content or checkouts are changed by this test.

On **McKay**, run the following in **Windows PowerShell under the Windows
account that owns the Ubuntu WSL installation**, not in the Ubuntu shell.
It schedules daily at **11:00 pm Sydney/Windows local time**, leaving a
two-hour window before the existing 1:00 am encrypted backup. Windows
Task Scheduler is used because a Linux cron timer inside a stopped WSL
instance cannot reliably start that instance.

```powershell
$taskName = 'Cobble - Daily GitHub Sync'
$action = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\wsl.exe" -Argument '-d Ubuntu -u cobbler -- /bin/bash /home/cobbler/Cobble/scripts/run_github_sync.sh'
$trigger = New-ScheduledTaskTrigger -Daily -At 23:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 90)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Archive Inky Tech GitHub sources to Cobble before the 01:00 backup'
```

The schedule is **not installed by checking out this repository**. Its
first real run needs verification. To exercise the newly registered task:

```powershell
Start-ScheduledTask -TaskName 'Cobble - Daily GitHub Sync'
Get-ScheduledTaskInfo -TaskName 'Cobble - Daily GitHub Sync'
```

Inspect the latest log in Ubuntu for `Sync complete: ...` and `exit=0`.
A failed run can leave earlier repositories refreshed and later ones
unchanged; rerunning remains safe. A successful run does not prove historical
gap closure or that every upstream API item was available.

Task Scheduler can only start the job when Windows and the relevant user
session/credentials permit it. If McKay is asleep or off, the run may occur
later or not at all. `StartWhenAvailable` provides a catch-up opportunity,
**not** guaranteed completion before backup. The 90-minute limit also
does not establish transactional consistency with a backup that begins
during a delayed or unusually long sync. Check the task history and logs.

Logs and the lock file remain in the private corpus store and are included
in the existing encrypted backup; they are not committed to Git. The log
files are owner-readable only. Keep GitHub authentication in `gh`'s existing
credential store, not in a scheduled-task command line.
