#!/bin/bash
# DRBR: build the three Windows programs (.NET Framework 4.8, with the .NET SDK - Windows or Linux) and, given a payload,
# DRBR-Setup.exe with the payload appended.
# Usage: scripts/build-installer.sh [payload dir] [out dir]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
if ! command -v dotnet > /dev/null && [ -x /home/claude/dotnet/dotnet ]; then export DOTNET_ROOT=/home/claude/dotnet; export PATH="$PATH:$DOTNET_ROOT"; fi
python3 "$HERE/packaging/gen_buildinfo.py"
python3 -c "import json; print(json.load(open('$HERE/drbr.json'))['launcher_version'])" > "$HERE/src/VERSION"
for P in Updater Launcher Setup; do
  dotnet build "$HERE/src/Drbr.$P" -c Release -o "$HERE/build/bin" 2>&1 | grep -E " error |Build succeeded" | sort -u
done
rm -f "$HERE/build/bin/"*.config
if [ $# -ge 1 ]; then
  OUT="${2:-$HERE/build}"
  mkdir -p "$OUT"
  python3 "$HERE/packaging/release_tools.py" setup --exe "$HERE/build/bin/DRBR-Setup.exe" --payload "$1" --out "$OUT/DRBR-Setup.exe"
fi
