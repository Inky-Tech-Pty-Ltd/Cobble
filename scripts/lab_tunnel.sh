#!/usr/bin/env bash
# McKay's existing Cobble tunnel, with explicit local operator switches.
# Never stores or prints keys; inherits the credential already loaded by the operator.
set -euo pipefail
mode="${1:-observe}"
case "$mode" in
  observe)
    export COBBLE_MCP_ALLOW_SOURCE_READS=1
    unset COBBLE_MCP_ALLOW_LAB_TESTS COBBLE_MCP_ALLOW_LAB_NOTES
    ;;
  operate)
    export COBBLE_MCP_ALLOW_SOURCE_READS=1
    export COBBLE_MCP_ALLOW_LAB_TESTS=1
    export COBBLE_MCP_ALLOW_LAB_NOTES=1
    ;;
  *)
    printf 'Usage: %s [observe|operate]\n' "$0" >&2
    exit 2
    ;;
esac
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
tunnel="$HOME/.local/opt/cobble-tunnel/tunnel-client"
if [[ ! -x "$tunnel" ]]; then
  echo "Cobble tunnel client was not found at the expected location." >&2
  exit 1
fi
if [[ -z "${CONTROL_PLANE_API_KEY:-}" ]]; then
  echo "Load the existing CONTROL_PLANE_API_KEY securely into this terminal before starting." >&2
  echo "No credential will be requested or stored by this script." >&2
  exit 1
fi
printf 'Starting Cobble lab tunnel (mode: %s)\n' "$mode"
printf 'Source text reads: enabled for authorised laboratory tools\n'
if [[ "$mode" == "operate" ]]; then
  printf 'Fixed offline tests and private journal: enabled\n'
else
  printf 'Fixed tests and private journal writing: disabled\n'
fi
printf 'To stop: Ctrl+C. Then refresh the Cobble plugin tools in ChatGPT.\n'
exec "$tunnel" run --profile cobble-memory
