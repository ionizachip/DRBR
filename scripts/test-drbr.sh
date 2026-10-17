#!/bin/bash
# DRBR: the test suites. Each one says PASS / FAIL; a suite whose inputs are not on this machine says BLOCKED.
#   mod      the DRBR save profile in the game code (GameMaker emulator, the real merged GML)
#   core     the launcher / installer / updater logic (.NET, real data.win + real patch + real key + local release server)
#   wine     the real Windows programs under Wine (EMULATED Windows), a Steam-like DELTARUNE, a stand-in game
#   save     the provided starting save
# Usage: scripts/test-drbr.sh [suites...]     env: DRBR_VANILLA (vanilla Chapter 3 data.win), DRBR_KEY (private key)
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VAN="${DRBR_VANILLA:-/mnt/user-data/uploads/data.win}"; KEY="${DRBR_KEY:-/home/claude/drbr_keys/drbr-signing-key.pem}"
W="${DRBR_MOD_WORK:-/home/claude/work}"
SUITES="${*:-save mod core wine}"
declare -A R
for s in $SUITES; do
  case $s in
    save) python3 "$HERE/scripts/validate-save.py" > /dev/null && R[$s]=PASS || R[$s]=FAIL ;;
    mod)  if [ -f "$W/tests/t_drbr_save54.py" ]; then (cd "$W/tests" && timeout 1800 python3 t_drbr_save54.py | tail -1) && R[$s]=PASS || R[$s]=FAIL; else R[$s]=BLOCKED; fi ;;
    core) if [ -f "$VAN" ] && [ -f "$KEY" ] && [ -d "$HERE/build/payload" ]; then timeout 2400 bash "$HERE/scripts/test-core.sh" "$HERE/build/payload" "$VAN" "$KEY" | tail -1 && R[$s]=PASS || R[$s]=FAIL; else R[$s]=BLOCKED; fi ;;
    wine) if command -v xvfb-run > /dev/null && [ -x /usr/lib/wine/wine64 ] && [ -f "$HERE/build/DRBR-Setup.exe" ] && [ -f "$VAN" ]; then
            timeout 3500 bash "$HERE/tests/installation/wine_e2e.sh" "$HERE/build/DRBR-Setup.exe" "$HERE/build/payload" "$VAN" "$KEY" "$HERE/build/stub" | tail -1 && R[$s]=PASS || R[$s]=FAIL
          else R[$s]=BLOCKED; fi ;;
  esac
done
for s in $SUITES; do echo "$s: ${R[$s]}"; done
for s in $SUITES; do [ "${R[$s]}" = FAIL ] && exit 1; done; exit 0
