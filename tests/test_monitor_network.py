"""Synthetic tests for private network monitor: no real network calls."""
import importlib.util
from contextlib import closing
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "monitor_network.py"
spec = importlib.util.spec_from_file_location("monitor_network", SCRIPT)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class NetworkMonitorTests(unittest.TestCase):
    def test_windows_gateway_picks_real_private_ipv4(self):
        with patch.object(monitor.subprocess, "run") as run:
            run.return_value.stdout = "192.168.20.1\n"
            self.assertEqual(monitor.windows_router_gateway(), "192.168.20.1")
            self.assertIn("Get-NetIPConfiguration", run.call_args.args[0][-1])
            run.return_value.stdout = "8.8.8.8\n"
            self.assertIsNone(monitor.windows_router_gateway())

    def test_sample_records_all_four_independent_probes(self):
        with patch.object(monitor, "router_probe", return_value=(True, 3)), \
             patch.object(monitor, "http_probe", side_effect=[(True, 43, 204), (True, 100, 401)]), \
             patch.object(monitor, "tunnel_probe", return_value=("degraded", "backoff", 7)):
            obs = monitor.sample("192.168.1.1")
        self.assertTrue(obs["router_ok"])
        self.assertEqual(obs["openai_http"], 401)
        self.assertEqual(obs["tunnel_failures"], 7)

    def test_private_sqlite_and_report(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "private" / "network.sqlite3"
            with closing(monitor.connect_db(path)) as db:
                obs = {
                    "timestamp_utc": monitor.datetime.now(monitor.timezone.utc).isoformat(timespec="seconds"),
                    "gateway_ip": "192.168.1.1", "router_ok": True, "router_ms": 4,
                    "internet_ok": False, "internet_ms": 6000, "openai_ok": False,
                    "openai_ms": 6000, "openai_http": None,
                    "tunnel_status": "degraded", "tunnel_state": "backoff", "tunnel_failures": 2,
                }
                monitor.save(db, obs)
                totals = monitor.report(db)
                self.assertEqual(totals["samples_24h"], 1)
                self.assertEqual(totals["internet_failures"], 1)
                self.assertEqual(totals["router_unchecked"], 0)
                obs["router_ok"] = None
                obs["gateway_ip"] = None
                monitor.save(db, obs)
                self.assertEqual(monitor.report(db)["router_unchecked"], 1)
                self.assertEqual(totals["tunnel_non_ok"], 1)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
