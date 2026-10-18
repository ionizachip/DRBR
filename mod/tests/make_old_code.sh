#!/bin/bash
# DRBR 1.0.0's game code for the mixed-version room test: 1.0.0's own build inputs (the toolkit of its 51.10 game package)
# generated into <folder>/merged with 1.0.0's own generator, on the same Chapter 3 base. The build's own merged code is not
# touched.
# Usage: make_old_code.sh [folder]   -> prints the folder of 1.0.0's code (KH_OLD for t_mixver101.py)
set -euo pipefail
SBX="${1:-/tmp/claude-0/drbr-old-code}"
rm -rf "$SBX"; mkdir -p "$SBX"
# 1.0.0's exact build inputs: the 51.10 game package's toolkit.zip (its generator, rules, templates with their events, and
# the boss pieces) - the package kept from 1.0.0's build (work/pkg51_1010_backup)
mkdir -p "$SBX/tk"
python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" /home/claude/work/pkg51_1010_backup/toolkit.zip "$SBX/tk"
mv "$SBX/tk/toolkit" "$SBX/scripts"
cp -r /home/claude/work/build/merged "$SBX/merged"
cp /home/claude/work/build/assets.json "$SBX/assets.json"
for f in "$SBX"/scripts/*.py; do
  sed -i -e "s#/home/claude/scripts#$SBX/scripts#g" -e "s#/home/claude/work/build/merged#$SBX/merged#g" -e "s#/home/claude/work/build/assets.json#$SBX/assets.json#g" "$f"
done
(cd "$SBX/scripts" && python3 gen_hub.py > "$SBX/gen.log" 2>&1 && python3 lint_hub.py > "$SBX/lint.log" 2>&1) || { echo "SANDBOX GEN FAILED"; tail -20 "$SBX/gen.log" "$SBX/lint.log"; exit 1; }
grep -E "unresolved|collisions|accessors on|raw asset" "$SBX/lint.log" | tr '\n' ' '; echo
echo "1.0.0 code: start log build $(grep -o '"build", "51.1[0-9]"' "$SBX/merged/gml_GlobalScript_knight_core.gml"), kbr_hj_bot_face $(grep -c 'function kbr_hj_bot_face' "$SBX/merged/gml_GlobalScript_knight_core.gml")"
echo "$SBX/merged/"
