#!/bin/bash
# DRBR: publish a release made by scripts/package-drbr.sh to GitHub Releases, as a DRAFT (the GitHub Actions workflow
# "release-check" then checks it; publish it with: gh release edit v<version> --draft=false).
# Uses the GitHub CLI with YOUR login (gh auth login) - no token is stored anywhere in DRBR.
# Usage: scripts/release-drbr.sh <version>
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VER="$1"; R="$HERE/dist/$VER/release"
[ -f "$R/DRBR.zip" ] || { echo "No release in $R - run scripts/package-drbr.sh $VER first."; exit 2; }
python3 "$HERE/packaging/release_tools.py" check "$R/DRBR.zip"
OWNER=$(python3 -c "import json; print(json.load(open('$HERE/drbr.json'))['github']['owner'])")
REPO=$(python3 -c "import json; print(json.load(open('$HERE/drbr.json'))['github']['repo'])")
[ "$OWNER" != "OWNER" ] || { echo "Set github.owner in drbr.json first (and rebuild: the launcher's update address comes from it)."; exit 2; }
git -C "$HERE" tag -a "v$VER" -m "DRBR $VER" 2>/dev/null || true
git -C "$HERE" push origin "v$VER"
gh release create "v$VER" --repo "$OWNER/$REPO" --draft --title "DRBR $VER" --notes-file "$R/RELEASE_NOTES.md" "$R/DRBR.zip"
echo "Draft release v$VER created on $OWNER/$REPO. Check it, then: gh release edit v$VER --repo $OWNER/$REPO --draft=false"
