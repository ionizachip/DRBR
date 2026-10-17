#!/bin/bash
# Copies the mod's own build sources from the build environment into mod/ (the GML, the generators, the build scripts,
# the emulator tests, the GameMaker emulator). Never copied: decompiled game code (*_gen/, base dumps), DELTARUNE data,
# build output, anyone's saves.
# Usage: scripts/sync-mod-sources.sh [scripts dir] [work dir] [gmlsim dir]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
S="${1:-/home/claude/scripts}"; W="${2:-/home/claude/work}"; E="${3:-/home/claude/gmlsim}"
M="$HERE/mod"
rm -rf "$M/scripts" "$M/gml" "$M/tests" "$M/build" "$M/notes" "$M/installer" "$HERE/tools/gmlsim"
mkdir -p "$M/scripts" "$M/gml" "$M/tests" "$M/build" "$M/notes" "$M/installer" "$HERE/tools"
cp "$S"/*.py "$S"/*.csx "$S"/knights.json "$S"/variant_default_sprites.json "$M/scripts/"
cp -r "$S/rules" "$S/extra_entries" "$M/scripts/"
cp "$S"/gml_templates_v6/*.gml "$M/gml/"
[ -d "$S/gml_templates_v6/kfsong" ] && cp -r "$S/gml_templates_v6/kfsong" "$M/gml/"
cp "$W"/tests/*.py "$W"/tests/*.sh "$M/tests/" 2>/dev/null || true
mkdir -p "$M/tests/data" && cp "$W/tests/data/ow_dump.tsv" "$M/tests/data/"
cp "$W"/runbuild51.sh "$W"/runchk51.sh "$W"/runverify51.sh "$W"/runrt51.sh "$W"/verify51.csx "$W"/funcdump51.csx "$W"/vardump51.csx \
   "$W"/check_runner51.py "$W"/rtdump.csx "$W"/assetidx.csx "$W"/objinfo.csx "$W"/pkg51.sh "$W"/make_tp51.sh "$M/build/" 2>/dev/null || true
cp "$W"/installer/make_package.sh "$W"/installer/make_manifest.py "$W"/installer/run_e2e51.sh "$M/installer/" 2>/dev/null || true
cp -r "$W/installer/package" "$W/installer/extra" "$M/installer/"
rm -rf "$M/installer/extra/Save file"
cp "$W"/online/notes/DRBR_ONLINE_GUIDE.txt "$W"/online/notes/DRBR_BOSSES.txt "$W"/online/notes/SKINS.txt "$W"/online/notes/JEVIL_SPEC.txt "$W"/FLOWERY_NOTES.txt "$W"/TESTING_REPORT.txt "$M/notes/"
cp -r "$W/online/server" "$M/online-server"  2>/dev/null || true
# the multiplayer DLL's own source and tests (the Steamworks SDK itself is Valve's and is not included)
mkdir -p "$M/online-steam/mock"
cp "$W"/online/steam/kf_steam.cpp "$W"/online/steam/build_kf_steam.sh "$W"/online/steam/t_steam_dll.py "$M/online-steam/" 2>/dev/null || true
cp "$W"/online/steam/mock/mock_steam_api.cpp "$W"/online/steam/mock/mock_steam_backend.py "$M/online-steam/mock/" 2>/dev/null || true
rm -rf "$M/online-server/node_modules"
cp -r "$E" "$HERE/tools/gmlsim"
find "$HERE/mod" "$HERE/tools" -name __pycache__ -type d -prune -exec rm -rf {} +
# nothing that must not be published
if find "$M" "$HERE/tools" \( -name '*.win' -o -name 'filech*' -o -name '*.pem' -o -name '*_gen' -o -name 'knight_hub.ini' -o -name 'knightfights_online.ini' \) | grep -q .; then
  echo "REFUSED: a file that must not be in the repository was copied:"; find "$M" "$HERE/tools" \( -name '*.win' -o -name 'filech*' -o -name '*.pem' -o -name '*_gen' \); exit 1
fi
du -sh "$M" "$HERE/tools/gmlsim"
