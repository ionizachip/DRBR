#!/bin/bash
# DRBR: build the game mod (the DRBR data.win) and its in-place package, from the mod's sources and the player-owned
# DELTARUNE files of the build machine. AUTHORIZED LOCAL STEP: it needs DELTARUNE's data.win files (Chapter 3, and
# Chapters 1/2/4/5 for the bosses' art), which must never be uploaded to GitHub or a hosted runner.
# Usage: scripts/build-drbr.sh            (env: DRBR_MOD_SCRIPTS, DRBR_MOD_WORK - default: the author's build machine)
set -euo pipefail
S="${DRBR_MOD_SCRIPTS:-/home/claude/scripts}"; W="${DRBR_MOD_WORK:-/home/claude/work}"
[ -f "$S/gen_hub.py" ] || { echo "The mod build environment is not here ($S). See docs/DEVELOPMENT.md."; exit 2; }
echo "== generate the merged GML";  (cd "$S" && python3 gen_hub.py > /dev/null && python3 lint_hub.py | grep -E "unresolved|raw asset")
echo "== build data.win (UndertaleModTool CLI)"; (cd "$W" && rm -f build51_done.txt && bash runbuild51.sh && tail -1 build51.log)
echo "== static checks + round trip"; (cd "$W" && bash runchk51.sh > /dev/null && tail -2 check_runner51.out && tail -1 rt51.log)
echo "== in-place package (xdelta patch + manifest)"; (cd "$W" && bash pkg51.sh > /dev/null && grep "verified" pkg51.log && tail -1 pkg51_sums.log)
echo "game package: $W/pkg51"
