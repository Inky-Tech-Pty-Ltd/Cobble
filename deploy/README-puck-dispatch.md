# Protected McKay deployment — staged, NOT YET ACTIVATED

The installer creates a dedicated `puck-dispatch` Linux service identity
and `puck-dispatch-clients` group. It copies exactly two reviewed Python
modules into root-owned `/opt/puck-dispatch/cobble/` and installs a systemd
service definition. Ordinary `cobbler` can access the service socket
through supplementary group membership, **but cannot modify the installed
Python modules or read the key** under ordinary Unix discretionary permissions.

**Do not run the installer before review and publication.**
It requires `sudo` and changes local user/group state. It deliberately
does NOT load the 1Password attachment, start the service, or enable dispatch.

The service expects the private key at
`/etc/puck-dispatch/private-key.pem` (mode 0600, owned by
`puck-dispatch`) and exposes
`/run/puck-dispatch/broker.sock` (mode 0660, owned by
`puck-dispatch:puck-dispatch-clients`).
The directory `/etc/puck-dispatch` is owned by the dedicated service\naccount and its private group, mode 0700. The client group does not\ntraverse it. The key must be service-owned and mode 0600.

Before installation, compare the two source files to the previously
tested commit, and run the offline suite. After review, an operator
may execute `sudo bash deploy/install-puck-dispatch.sh "$PWD"`.

**Next operations require separate deliberate actions:**
provision the 1Password key without pasting it into chat, install with
0600 permissions to the service account, start the unit, test a safe
canary, and only then enable `COBBLE_MCP_ALLOW_PUCK_DISPATCH=1`
for the MCP subprocess. The existing tunnel wrapper does not enable
this option.

Security qualifications:
- A user who has unrestricted `sudo`/root on McKay can defeat Unix
  account separation. This isn't a boundary against the machine owner.
- The existing connected Joe-authenticated GitHub plugin is still a
  separate write bypass until removed or replaced.
- GitHub Actions **write** permission can trigger other workflows in
  InkyTech, not just the one hardcoded by the broker. Review that exposure.
- No actual GitHub App authentication or end-to-end operation has yet
  been tested through this service. Issue #5 must remain open.
