# McKay connectivity monitor

Read-only probes distinguish physical router/LAN reachability, general HTTPS,
OpenAI HTTPS, and the Cobble tunnel's control-plane health. Python standard
library only. Takes one sample per minute and retains a rolling **31 days**
in private SQLite at `~/cobble-data/monitoring/network.sqlite3`, outside Git.
No API keys, prompts, browsing contents, or response bodies are recorded.

- Router: ping the **Windows physical Ethernet gateway**, not WSL's virtual NAT gateway. McKay's unit pins the verified gateway at `192.168.20.1`.
- General internet: HTTP 204 from Google's `generate_204` endpoint.
- OpenAI: unauthenticated GET to `https://api.openai.com/v1/models`, expecting HTTP 401.
- Tunnel: local read-only `http://127.0.0.1:8080/health/control-plane`.

The interactive script discovers the physical router address from Windows PowerShell.
The background systemd service instead passes `--gateway 192.168.20.1`, because
PowerShell gateway discovery failed in its noninteractive environment. If McKay's
router IP changes, update that value in the unit and redeploy. If an interactive
run cannot discover the router, the saved sample reports a null gateway and
router status rather than misleadingly pinging the WSL gateway. The report
explicitly counts such untested samples under `router_unchecked`.
An ICMP non-response is not conclusive when a router blocks ping; first
establish a successful router baseline.

## Install on McKay (WSL Ubuntu)

```bash
cd ~/Cobble
git switch main
git pull --ff-only
python3 -m unittest discover -s tests -p 'test_monitor_network.py' -v
python3 scripts/monitor_network.py --once
python3 scripts/monitor_network.py --report
mkdir -p ~/.config/systemd/user
cp ops/cobble-network-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cobble-network-monitor.service
# Existing installations: restart to apply updated ExecStart.
systemctl --user restart cobble-network-monitor.service
systemctl --user is-active cobble-network-monitor.service
```

After several minutes, `python3 scripts/monitor_network.py --report`
reports 24-hour counts of failures and the latest sample timestamp.
For service logs: `journalctl --user -u cobble-network-monitor.service -n 20 --no-pager`.

Interpret carefully: if router answers but both HTTPS checks fail, suspect
the upstream route; if only OpenAI fails, inspect its route or service; if
both HTTPS probes succeed but tunnel is degraded, investigate the tunnel
long poll. A sample cannot definitively establish the cause of an outage.
The 60-second sampling interval misses some brief dropouts. The monitor
uses very little bandwidth but does make regular unauthenticated requests.

The monitor runs in WSL's existing systemd user environment and therefore
still depends on Windows keeping WSL alive via the **Cobble WSL Keepalive**
scheduled task; it does not independently ensure Windows starts WSL.
