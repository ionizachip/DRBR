#!/bin/bash
# DRBR: the core tests on Linux (the same C# code as the Windows programs) with the real vanilla data.win, the real payload,
# a real signing key, and a local release server for the update tests.
# Usage: scripts/test-core.sh <payload dir> <vanilla data.win> <private key> [groups...]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PAYLOAD="$(realpath "$1")"; VANILLA="$(realpath "$2")"; KEY="$(realpath "$3")"; shift 3
WORK="${DRBR_TEST_WORK:-$HERE/build/test-work}"
rm -rf "$WORK"; mkdir -p "$WORK"
PORT=$((20000 + RANDOM % 20000))
python3 "$HERE/tests/updates/make_test_releases.py" "$PAYLOAD" "$WORK/releases" "$KEY" "http://127.0.0.1:$PORT"
: > "$WORK/http.log"
python3 "$HERE/tests/updates/range_server.py" "$WORK/releases" "$PORT" "$WORK/http.log" &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
export DOTNET_ROOT="${DOTNET_ROOT:-/home/claude/dotnet}"; export PATH="$PATH:$DOTNET_ROOT" DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
dotnet build "$HERE/src/Drbr.Tests" -c Release -o "$HERE/build/tests" 2>&1 | grep -E " error |Build succeeded" | sort -u
DRBR_TEST_WORK="$WORK/w" DRBR_TEST_VANILLA="$VANILLA" DRBR_TEST_PAYLOAD="$PAYLOAD" DRBR_TEST_KEY="$KEY" \
DRBR_TEST_RELEASE2="$WORK/releases/good" DRBR_TEST_HTTP="http://127.0.0.1:$PORT" DRBR_TEST_HTTP_LOG="$WORK/http.log" \
  dotnet "$HERE/build/tests/drbr-tests.dll" "$@"
