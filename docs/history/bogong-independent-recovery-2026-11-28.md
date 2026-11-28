# Independent Cobble data recovery on Bogong — 28 November 2026

**Result: PASS — independent recovery of backed-up data.** This does not establish that a fully operating Cobble service can be recreated on the replacement host.

## Recovery boundary

The exercise asked whether the Cobble backup remains accessible if McKay is lost. A different Windows laptop, **Bogong**, downloaded the encrypted archive from iCloud.com and decrypted it with the separate recovery key retrieved from 1Password. Bogong initially had **no WSL** or Cobble installation. Recovery tools were Windows PowerShell 5.1, Windows tar, age v1.3.2, Git for Windows, and Python 3.13 with built-in SQLite. Free space before testing: **244 GB**.

No supplier APIs, local McKay archive, running Cobble application, or live memory store were needed on Bogong. No private key or plaintext record is included in this report.

## Specimen and exact archive verification

| Evidence | Observed |
| --- | --- |
| Source archive | **cobble-2026-11-27-full.tar.gz.age** |
| Source location | iCloud Drive / CobbleBackups, downloaded through iCloud.com on Bogong |
| SHA-256 at original McKay backup and independently on Bogong | **c09407fc6d2ca21bafc45853733bbea9473b704295b339da556f427f9e22cd19** |
| Independent decryption key | 1Password item **Cobble — Backup Recovery Key**, attachment **backup-key.txt** |
| Decryption result | age exit code 0 |
| Decrypted compressed tar size | **2,821,302,099 bytes** |
| Compressed archive listing | **85,021 entries**; tar integrity-listing exit code 0 |
| Extraction into isolated Bogong test directory | tar exit code 0; all five top-level directories present |

The archive contained exactly these five top-level directories:

- **Cobble**
- **VillageLink**
- **cobble-data**
- **cobble-arenas**
- **cobble-source-checkouts**

The SHA-256 match verifies the encrypted download matches the original digest. It does not prove that the original archive included every possible source.

## Recovered data integrity

| Test | Observed |
| --- | --- |
| Snug live JSON | **105 valid, 0 invalid** |
| Snug events JSON | **5 valid, 0 invalid** |
| Snug Doors JSON | **1 valid, 0 invalid** |
| JSON subtotal | **111 valid, 0 invalid** |
| Cobble Git full fsck, no reflogs | **PASS (exit 0)** |
| VillageLink Git full fsck, no reflogs | **PASS (exit 0)** |
| Genuine SQLite databases identified by file header | **7** |
| SQLite read-only PRAGMA quick_check | **7 OK, 0 failures** |

Cobble Git fsck reported 20 dangling commits, which are unreferenced history rather than corruption; the process exited successfully.

The first Python/Windows database inventory aborted with WinError 5 when traversal encountered a Linux-oriented hosting path under cobble-data/hosting/inkytech/www. The scan was corrected to use os.walk without following links and with link/junction filtering. The repeat completed: seven actual SQLite databases, no failures, no links skipped in the scanned path set. This supports database recoverability, but does not prove that every Linux symlink can function on Windows.

The data results agree with the earlier independent-directory restore conducted **on McKay** on 27 November: 105 live, 5 events, 1 Door JSON, seven SQLite databases, and both Git repositories intact. McKay additionally exercised application-native room readers: six meetings, 39 turns, one Door registry and no unresolved room_voice references. **Those application-native tests were not run on Bogong.**

## Related November synchronisation incident

During the 27 November audit, local encrypted backups and local iCloud Drive file copies reported success while no newer archive than 11 November appeared in iCloud.com. The iCloud for Windows client requested Apple Account reverification; after signing in, delivery resumed and a 50 MB independent browser upload succeeded. The later completion of the 13 November archive coincided with browser activity, but causation was not established.

The **12 November** archive and local run log were absent; the cause was not established. Windows Task Scheduler Operational history was disabled, so there is no historical task execution evidence for that date.

On **28 November**, all visible backlog entries had green sync indicators and the operator received the scheduled **09:00 AEDT Cobble backup: OK** email. The installed independent Windows heartbeat task executes the read-only backup watcher and sends OK or WARNING daily; missing email is itself grounds for investigation. The watcher relies on local Windows cloud-provider state; this completed Bogong download-and-restore provides stronger separate evidence for the specific **27 November** archive.

See [backup watchdog](../mckay-backup-watchdog.md) and [backup heartbeat](../mckay-backup-heartbeat.md).

## Cleanup: sensitive test copies

On Bogong, the operator removed and then verified absent (three false existence checks):

- The decrypted backup.tar.gz under the dated Bogong disaster-recovery directory
- The isolated extracted restored/ directory
- The temporary Downloads/backup-key.txt recovery key

The **encrypted archive** was retained. The authoritative key remains in 1Password. Ordinary deletion on an SSD is not a guarantee of forensic secure erasure. Metadata artifacts such as the remaining contents.txt archive listing may contain private path names; remove them when no longer needed.

## Scope of the milestone

**Demonstrated:** independent encrypted-cloud retrieval with exact SHA-256 match; independent recovery-key use; age decryption; full tar listing and extraction; JSON syntax checks; Git object integrity; SQLite quick-check integrity of the seven recognised database files.

**Not demonstrated:** a fully running restored Cobble service; application-native memory reads on Bogong; Windows Task Scheduler reconstruction; service and systemd configuration; tunnel/identity setup; complete restoration of secrets held outside the five directories; independent remote alerting when McKay is unavailable; or complete coverage of every possible data source.

In particular, the archived directories do **not** cover all machine configuration and secrets: local ~/.config/cobble, ~/.ssh, user service units, Windows tasks, and locally installed backup scripts may need separate provisioning. The SMTP credential for unattended daily reporting is deliberately outside Git and must be recovered separately.

**Disposition:** close the **independent backed-up-data recovery** milestone as PASS. Keep **whole-machine/service recovery** and **off-machine monitoring** open as distinct operational work. Periodically repeat the independent retrieval and restore test, including after significant backup-selection or key-management changes.

## Minimal repeatable runbook

1. On an independent computer, download a chosen encrypted archive from **iCloud.com**, not the original machine's local iCloud folder.
2. Compare its SHA-256 hash to the digest recorded when the original backup was created. Stop if they differ.
3. Independently retrieve backup-key.txt from 1Password without displaying or transmitting its contents.
4. Decrypt with age into an isolated directory; verify the gzip/tar listing and extract to a new directory.
5. Check expected directories and JSON, Git fsck, and read-only SQLite integrity; avoid following Linux links blindly on Windows.
6. Remove temporary decrypted tar, extracted data, and key; verify their absence. Retain the encrypted archive and evidence report.

This record reflects observed operator output, not an automated, signed attestation.
