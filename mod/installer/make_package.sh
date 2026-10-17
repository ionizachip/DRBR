#!/bin/bash
# Assemble the distributable Knight Hub installer package.
# usage: make_package.sh VANILLA_DATA_WIN PATCHED_DATA_WIN OUTDIR [--version V] [--xdelta3-exe PATH] [--music-dir DIR] [--steam-dir DIR]
#   creates in OUTDIR: INSTALL_KNIGHT_HUB.bat RESTORE_VANILLA.bat install_knight_hub.ps1 README_INSTALL.txt
#   KNIGHT_HUB_MANIFEST.txt knight_hub_chapter3.xdelta.part0..N [xdelta3.exe] [knight_hub_extras.zip]
#   [kf_steam.dll steam_api64.dll steam_appid.txt]  (build 45: Knight Fights Online over Steam, from --steam-dir)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VAN="$1"; PAT="$2"; OUT="$3"; shift 3
VER=dev; EXE=""; MUS=""; STM=""; KFS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VER="$2"; shift 2;;
    --xdelta3-exe) EXE="$2"; shift 2;;
    --music-dir) MUS="$2"; shift 2;;
    --steam-dir) STM="$2"; shift 2;;
    --kfsongs-dir) KFS="$2"; shift 2;;
    *) echo "unknown option $1"; exit 2;;
  esac
done
mkdir -p "$OUT"
TMP="$(mktemp -d "$OUT/.mk.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
xdelta3 -e -9 -f -s "$VAN" "$PAT" "$TMP/knight_hub_chapter3.xdelta"
ARGS=(--mod-version "$VER" -o "$OUT/KNIGHT_HUB_MANIFEST.txt" --parts-out "$OUT" --part-size 24000000)
[ -n "$EXE" ] && ARGS+=(--xdelta3-exe "$EXE")
[ -n "$MUS" ] && ARGS+=(--music-dir "$MUS")
STEAMF=""
if [ -n "$STM" ]; then
  for f in kf_steam.dll steam_api64.dll steam_appid.txt; do
    [ -f "$STM/$f" ] || { echo "missing $STM/$f"; exit 2; }
    cp "$STM/$f" "$OUT/$f"; ARGS+=(--steam-file "$OUT/$f"); STEAMF="$STEAMF $f"
  done
fi
python3 "$HERE/make_manifest.py" "$VAN" "$PAT" "$TMP/knight_hub_chapter3.xdelta" "${ARGS[@]}"
cp "$HERE/package/INSTALL_KNIGHT_HUB.bat" "$HERE/package/RESTORE_VANILLA.bat" "$HERE/package/install_knight_hub.ps1" "$HERE/package/README_INSTALL.txt" "$OUT/"
[ -n "$EXE" ] && cp "$EXE" "$OUT/xdelta3.exe"
if [ -n "$MUS" ]; then
  python3 - "$MUS" "$OUT/knight_hub_extras.zip" "$OUT/knight_hub_music.zip" "$OUT/knight_hub_music2.zip" "$OUT/knight_hub_music3.zip" "$OUT/knight_hub_music4.zip" <<'PY'
import sys, os, zipfile
src, dst, dst2, dst3, dst4, dst5 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
names = ["knightmare_knight.ogg", "thorn_knight.ogg", "its_nothing_but_garbage_noise.ogg", "superchargedknight/cleaver.ogg"]
# build 47: the new fight songs (FIGHT SONG / online MUSIC); Flower Man is the game's own mus file, never shipped
names2 = ["kh_void_star.ogg", "kh_lv_crusher.ogg", "kh_true_hero.ogg", "kh_neotech_online.ogg", "kh_storyshift_black.ogg",
          "kh_anywhere_you_go.ogg", "kh_ever_ascending.ogg"]
# build 48: twelve more songs in a zip of their own (each zip stays under 30 MB); Guardian is the game's own titan_battle.ogg
names3 = ["kh_lost_dream.ogg", "kh_forget_me_not.ogg", "kh_hell_hammer.ogg", "kh_in_my_way.ogg", "kh_till_the_end.ogg", "kh_megalo_vania.ogg", "kh_megalo_strike_back.ogg", "kh_red_crimson_death.ogg", "kh_wrong_enemy.ogg", "kh_n1ght_of_n1ghtcore.ogg", "kh_that_feeling.ogg", "kh_identity_crisis.ogg"]
# build 50: the Claude Music Handoff's 20 new songs, in two zips (each under 30 MB)
names4 = ["kh_blood.ogg", "kh_close_to_inevitability.ogg", "kh_dusttale_sonata.ogg", "kh_fraight_fest.ogg", "kh_heir_of_grief.ogg", "kh_megalovania_itsaleccio.ogg", "kh_neo_chaos.ogg", "kh_penumbra_phantasm.ogg", "kh_petal_dance.ogg", "kh_white_cell.ogg"]
names5 = ["kh_chrysalis.ogg", "kh_deep_waters.ogg", "kh_hell_for_frandle.ogg", "kh_ice_shock.ogg", "kh_megalovania_sunhatgirl.ogg", "kh_our_flower_power.ogg", "kh_risen_up.ogg", "kh_venari.ogg", "kh_vs_susie_neo.ogg", "kh_wheel_of_misfortune.ogg"]
for d, ns in ((dst, names), (dst2, names2), (dst3, names3), (dst4, names4), (dst5, names5)):
    with zipfile.ZipFile(d, "w", zipfile.ZIP_STORED) as z:
        for rel in ns:
            p = os.path.join(src, *rel.split("/"))
            if os.path.isfile(p): z.write(p, "mus/" + rel)
            else: print("warning: music file missing, not in zip:", rel)
PY
fi
# build 50: the KF Song Pack's songs (a kfsongs folder: <song_id>/song.json, inst.ogg, vocals.ogg, lyrics.json), installed next
# to data.win by the installer (knight_hub_kfsongs.zip)
KFZ=""
if [ -n "$KFS" ]; then
  python3 - "$KFS" "$OUT/knight_hub_kfsongs.zip" <<'PY'
import sys, os, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dst, "w", zipfile.ZIP_STORED) as z:
    for root, dirs, files in os.walk(src):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            z.write(p, "kfsongs/" + os.path.relpath(p, src).replace(os.sep, "/"))
PY
  KFZ="knight_hub_kfsongs.zip"
fi
( cd "$OUT" && sha256sum INSTALL_KNIGHT_HUB.bat RESTORE_VANILLA.bat install_knight_hub.ps1 README_INSTALL.txt KNIGHT_HUB_MANIFEST.txt knight_hub_chapter3.xdelta.part* $( [ -n "$EXE" ] && echo xdelta3.exe ) $( [ -n "$MUS" ] && echo knight_hub_extras.zip knight_hub_music.zip knight_hub_music2.zip knight_hub_music3.zip knight_hub_music4.zip ) $KFZ $STEAMF > SHA256SUMS.txt )
echo "package written to $OUT"
