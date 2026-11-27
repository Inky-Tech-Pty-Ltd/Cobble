# Backup heartbeat email — proposed operational rollout

**Status:** Candidate. No scheduled task or SMTP credential is installed by
merging this PR. The existing 01:00 encrypted backup is unchanged.

## Why an email every day?

A failure-only warning is silent when McKay is powered off, its WSL filesystem
is unavailable, or Windows fails to start the watchdog. At 09:00 Sydney time
a separate Windows scheduled task should send **one email whether OK or WARNING**.
A missing heartbeat then becomes an operator-visible reason to investigate.

Expected subjects:

- `Cobble backup: OK | 2026-11-27`
- `Cobble backup: WARNING | 2026-11-27`

An OK is narrowly scoped to local archive/log checks and the *Windows Cloud
Files provider's IN_SYNC report*. **It does not establish independently
retrievable, decryptable iCloud storage**. That proof still requires a
download-and-restore test from Bogong.

## Components

1. Existing, tested `scripts/check_mckay_backup.ps1` runs against local
   Windows and WSL backup directories. Returns 0 for OK or 2 for warnings
   and writes `%LOCALAPPDATA%\Cobble\backup-watchdog\latest.json`.
2. New `scripts/run_mckay_backup_heartbeat.ps1` launches the watchdog,
   regardless of the prior night's backup task, and then invokes the email
   sender through McKay's Ubuntu WSL. It sends a warning even when the
   watchdog reports an unexpected exit, if the sender itself still runs.
3. New `scripts/send_mckay_backup_heartbeat.py` uses Python's standard
   library `smtplib.SMTP_SSL` with certificate verification (implicit TLS,
   normally TCP 465). It sends only status/date/counts, never archive bytes,
   corpus text, provider API keys or secrets. Password is read from a
   private local file accessible only by the `cobbler` user.

The sender relies on an existing, operator-controlled authenticated SMTP
mailbox rather than adding another intelligence provider or paid mail API.

## Security and limits

- The sender's config and SMTP credential live only in
  `~/.config/cobble/backup-heartbeat.json` and the adjacent
  `backup-heartbeat.password` with file mode 0600. Their parent directory
  is mode 0700. Neither is committed to Git or included in the current
  five-directory encrypted archives.
- Provision the password from the operator's 1Password record using the
  hidden interactive prompt; do not paste it into chat, a shell command,
  Windows Task Scheduler arguments or logs.
- The secret's recoverable original must remain in 1Password. The local
  copy is for **unattended** operation, rather than depending on 1Password
  being interactively unlocked every morning.
- The status email is **SMTP accepted**, not evidence of inbox receipt.
  Verify one real test in the recipient's mailbox.
- If WSL, internet access or the SMTP server fails, there may be **no**
  email at all. That is the design reason to expect a heartbeat every day.
  There is no independent service that automatically raises a second alarm.
- The credentials file is outside Cobble's backup, so a replacement host
  must re-provision it from 1Password. This is a feature, not an omission.
- A daily email is low-noise and can be filtered into a dedicated mailbox
  folder, but the operator needs to notice missing days.

## Step 1 — install and test sender (McKay Ubuntu WSL)

Once this PR has been reviewed and merged:

```bash
mkdir -p ~/.local/bin
curl -fsSL \
  https://raw.githubusercontent.com/Inky-Tech-Pty-Ltd/Cobble/main/scripts/send_mckay_backup_heartbeat.py \
  -o ~/.local/bin/send_mckay_backup_heartbeat.py
chmod 700 ~/.local/bin/send_mckay_backup_heartbeat.py
python3 ~/.local/bin/send_mckay_backup_heartbeat.py --self-test
```

Expect `BACKUP EMAIL SELF-TEST PASS`; this performs no network call.

Then provision the operator's existing SMTP account (sample placeholders
shown; replace with mailbox details already held in 1Password):

```bash
python3 ~/.local/bin/send_mckay_backup_heartbeat.py --setup \
  --smtp-host SMTP_HOST --smtp-port 465 \
  --username MAILBOX_ADDRESS --sender MAILBOX_ADDRESS \
  --recipient YOUR_NOTIFICATION_ADDRESS
```

The password prompt does **not echo**. A credential file is created once
and refused if it already exists. For a credential change, deliberately
re-provision the files locally; do not print or edit secrets in chat.

Send exactly one explicit SMTP transport test:

```bash
python3 ~/.local/bin/send_mckay_backup_heartbeat.py --test-mail
```

The script prints that the SMTP server accepted the message, but the
operator must check the receiving inbox for `Cobble backup: TEST heartbeat`.
Do not schedule until a real test email has been received.

## Step 2 — install and test Windows wrapper

Run from **McKay Windows PowerShell** after the reviewed version is on
GitHub `main`:

```powershell
$dir = Join-Path $env:LOCALAPPDATA 'Cobble'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$runner = Join-Path $dir 'run_mckay_backup_heartbeat.ps1'
Invoke-WebRequest -UseBasicParsing \
  'https://raw.githubusercontent.com/Inky-Tech-Pty-Ltd/Cobble/main/scripts/run_mckay_backup_heartbeat.ps1' \
  -OutFile $runner
& $runner -SelfTest
```

Note: PowerShell 5.1 uses its normal command-line continuation syntax;
the multiline URL above can instead be pasted as a single line if desired.

Then **manually** run `& $runner`. Expect an email saying WARNING if
backups remain in iCloud's queue. After the command, inspect:

```powershell
Get-Content "$env:LOCALAPPDATA\Cobble\backup-watchdog\heartbeat-last.json"
```

An `smtp_exit` of 0 means accepted by the SMTP server; inbox delivery must
still be confirmed. A watchdog warning gives exit code 2 even when its
email was sent successfully. Send failure returns 3.

## Step 3 — independent daily Windows schedule (only after successful manual test)

From PowerShell in the Windows account that owns iCloud Drive and Ubuntu:

```powershell
$runner = Join-Path $env:LOCALAPPDATA 'Cobble\run_mckay_backup_heartbeat.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument (
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $runner + '"'
)
$trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Cobble - Backup Delivery Heartbeat' `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Send daily Cobble OK/WARNING heartbeat independent of nightly backup'
```

Test the registered task once, then verify the actual email and
`Get-ScheduledTaskInfo` result. Ensure the correct Windows user and
WSL distribution can run while the user is not actively working.
`StartWhenAvailable` is opportunistic; it is **not** a guarantee that an
unavailable computer sends a message later.

This task replaces the *proposed* standalone 09:00 watchdog task.
Do not register **both** under the same time; the heartbeat wrapper already
invokes the watchdog.

## Acceptance criteria

- Offline tests pass on Ubuntu and Windows.
- One SMTP test reaches the intended inbox.
- One manually invoked WARNING heartbeat reaches the inbox with no secrets.
- Independent 09:00 task executes on McKay as intended; the next morning's
  email is actually received.
- Even after success, record the unresolved independent Bogong archive restore
  and wider McKay infrastructure recovery work.
