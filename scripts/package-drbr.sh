#!/bin/bash
# DRBR: a complete, signed release in dist/<version>/release from the built game package.
#   1. the DRBR programs (scripts/build-installer.sh)      2. the payload (packaging/make_payload.py)
#   3. DRBR-Setup.exe with the payload appended             4. the release assets + update-manifest.json(.sig) + checks
# Usage: scripts/package-drbr.sh <version> [game package dir] [release notes .md]
#        env DRBR_SIGNING_KEY_FILE (or DRBR_KEY) = the private key - never in the repository
#        env DRBR_NO_MUSIC=1 = leave out the mod's fight songs (third-party works - see docs/RELEASING.md)
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VER="$1"; PKG="${2:-${DRBR_MOD_WORK:-/home/claude/work}/pkg51}"; NOTES="${3:-$HERE/CHANGELOG.md}"
KEY="${DRBR_SIGNING_KEY_FILE:-${DRBR_KEY:-/home/claude/drbr_keys/drbr-signing-key.pem}}"
D="$HERE/dist/$VER"; rm -rf "$D"; mkdir -p "$D"
python3 - "$HERE/drbr.json" "$VER" <<'PY'
import json, sys
p, v = sys.argv[1], sys.argv[2]
d = json.load(open(p)); d['version'] = v; json.dump(d, open(p, 'w'), indent=2); open(p, 'a').write('\n')
PY
bash "$HERE/scripts/build-installer.sh"
MUSIC=(); [ "${DRBR_NO_MUSIC:-0}" = 1 ] && MUSIC=(--no-music)
python3 "$HERE/packaging/make_payload.py" --pkg "$PKG" --apps "$HERE/build/bin" --out "$D/payload" --version "$VER" --notes "$NOTES" "${MUSIC[@]}"
python3 "$HERE/packaging/release_tools.py" setup --exe "$HERE/build/bin/DRBR-Setup.exe" --payload "$D/payload" --out "$D/DRBR-Setup.exe"
python3 "$HERE/packaging/release_tools.py" release --payload "$D/payload" --setup "$D/DRBR-Setup.exe" --out "$D/release" --key "$KEY"
python3 "$HERE/packaging/release_tools.py" check "$D/release"
echo "release $VER ready: $D/release"
