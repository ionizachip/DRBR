#!/bin/bash
# Build 50 full-size end-to-end test: the real vanilla data.win, the build 50 PACKAGE AS DELIVERED (pkg51), and the upgrade from the real build 49 data.win.
# usage: run_e2e51.sh [VANILLA] [PATCHED] [STEAMDIR]    (cleans up its big temp files)
set -uo pipefail
export DOTNET_ROOT=/home/claude/dotnet PATH=$PATH:/home/claude/dotnet:/home/claude/pwsh
HERE="$(cd "$(dirname "$0")" && pwd)"
VAN="${1:-/mnt/user-data/uploads/data.win}"; PAT="${2:-/home/claude/work/out/merged_full51.win}"; OLD="/home/claude/work/out/merged_full50.win"; PKG="/home/claude/work/pkg51"; STM="${3:-/home/claude/work/steamstage}"
W="$HERE/_e2e51"; rm -rf "$W"; mkdir -p "$W"
trap 'rm -rf "$W"' EXIT
fail=0; chk() { if "$@"; then echo "  ok: $*"; else echo "  FAIL: $*"; fail=1; fi; }
echo "== the package as delivered (pkg51)"
mkdir -p "$W/pkg"; cp "$PKG"/* "$W/pkg/"
chk grep -q "^mod_version=51[[:space:]]*$" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
( cd "$W/pkg" && sha256sum -c SHA256SUMS.txt > "$W/sums.log" 2>&1 ); chk test $? -eq 0
ls -l "$W/pkg" | sed -n 1,40p
chk grep -q "^steam=kf_steam.dll|" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
chk grep -q "^steam=steam_api64.dll|" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
chk grep -q "^steam=steam_appid.txt|" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
chk grep -q " kf_steam.dll$" "$W/pkg/SHA256SUMS.txt"
# build 47: the new fight songs in their own zip, listed in the manifest and the checksums
chk grep -q " knight_hub_music.zip$" "$W/pkg/SHA256SUMS.txt"
# build 50: twelve more in knight_hub_music2.zip
chk grep -q " knight_hub_music2.zip$" "$W/pkg/SHA256SUMS.txt"
for s in kh_lost_dream kh_forget_me_not kh_hell_hammer kh_in_my_way kh_till_the_end kh_megalo_vania kh_megalo_strike_back kh_red_crimson_death kh_wrong_enemy kh_n1ght_of_n1ghtcore kh_that_feeling kh_identity_crisis; do
  chk grep -q "^music=$s.ogg|" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
done
for s in kh_void_star kh_lv_crusher kh_true_hero kh_neotech_online kh_storyshift_black kh_anywhere_you_go kh_ever_ascending; do
  chk grep -q "^music=$s.ogg|" "$W/pkg/KNIGHT_HUB_MANIFEST.txt"
done
R="$W/Program Files (x86)/Steam/steamapps/common/DELTARUNE"
G="$R/chapter3_windows"
mkdir -p "$G"; cp "$W"/pkg/* "$G/"; cp "$VAN" "$G/data.win"; chmod 644 "$G/data.win"
export KH_XDELTA=/usr/bin/xdelta3 KH_NOPAUSE=1 KH_ASSUME_YES=1
run() { ( cd "$W" && pwsh -NoProfile -File "$G/install_knight_hub.ps1" "$@" ) > "$W/run.log" 2>&1; local rc=$?; tail -12 "$W/run.log"; echo "  exit code: $rc"; return $rc; }
echo "== install"; run; chk test $? -eq 0
chk cmp "$G/data.win" "$PAT"
chk cmp "$G/data.win.vanilla" "$VAN"
chk grep -q "Steam files are in place" "$W/run.log"
# build 47: every song in DELTARUNE\mus, byte for byte the packaged one (11: the 4 old ones and the 7 new)
chk grep -q "Music summary: 43 installed" "$W/run.log"
for s in kh_void_star kh_lv_crusher kh_true_hero kh_neotech_online kh_storyshift_black kh_anywhere_you_go kh_ever_ascending kh_lost_dream kh_forget_me_not kh_hell_hammer kh_in_my_way kh_till_the_end kh_megalo_vania kh_megalo_strike_back kh_red_crimson_death kh_wrong_enemy kh_n1ght_of_n1ghtcore kh_that_feeling kh_identity_crisis; do
  chk cmp "$R/mus/$s.ogg" "/home/claude/work/deliver/mus/$s.ogg"
done
echo "== the music zip missing: the game still installs, the songs are reported missing (optional)"
mv "$G/knight_hub_music.zip" "$W/music.bak"; rm -f "$R"/mus/kh_*.ogg
run -Force; chk test $? -eq 0
chk grep -q "Optional music file not found: kh_void_star.ogg" "$W/run.log"
chk cmp "$G/data.win" "$PAT"
mv "$W/music.bak" "$G/knight_hub_music.zip"
run -Force; chk test $? -eq 0
chk grep -q "Music: installed kh_ever_ascending.ogg" "$W/run.log"
echo "== second run (already installed)"; run; chk test $? -eq 0
chk grep -q "Steam files are in place" "$W/run.log"
echo "== a damaged steam_api64.dll is noticed (warning, not a failure)"
cp "$G/steam_api64.dll" "$W/sapi.bak"; printf 'x' >> "$G/steam_api64.dll"
run; chk test $? -eq 0
chk grep -q "steam_api64.dll is not the file from this package" "$W/run.log"
cp "$W/sapi.bak" "$G/steam_api64.dll"
echo "== a missing kf_steam.dll is noticed"
mv "$G/kf_steam.dll" "$W/kf.bak"
run; chk test $? -eq 0
chk grep -q "kf_steam.dll is missing from this folder" "$W/run.log"
mv "$W/kf.bak" "$G/kf_steam.dll"
echo "== restore (the package files - the Steam files too - stay in the folder)"; run -Restore; chk test $? -eq 0
chk cmp "$G/data.win" "$VAN"
for f in kf_steam.dll steam_api64.dll steam_appid.txt; do chk cmp "$G/$f" "$W/pkg/$f"; done
chk grep -q "package files stay in this folder" "$W/run.log"
echo "== reinstall after restore (nothing copied back)"
run; chk test $? -eq 0
chk cmp "$G/data.win" "$PAT"
chk grep -q "Steam files are in place" "$W/run.log"
# PLAY_KNIGHT_HUB.bat in chapter3_windows, replacing an older Knight Hub build: INSTALL says 6, RESTORE, INSTALL again,
# all in this one folder (build 45 as first delivered deleted the Steam files in the RESTORE step: "kf_steam.dll is
# missing" on the ONLINE page after an upgrade from build 44). Same steps and exit-code checks as the .bat.
play_inplace() {
  run; local rc=$?
  [ $rc = 0 ] && return 0
  [ $rc = 6 ] || return 10
  run -Restore || return 11
  run || return 12
  return 0
}
echo "== PLAY_KNIGHT_HUB.bat upgrade from the REAL build 50 data.win (in place: INSTALL 6 -> RESTORE -> INSTALL)"
cp "$OLD" "$G/data.win"
( cd "$W" && pwsh -NoProfile -File "$G/install_knight_hub.ps1" ) > "$W/run.log" 2>&1; chk test $? -eq 6
play_inplace; chk test $? -eq 0
chk cmp "$G/data.win" "$PAT"
for f in kf_steam.dll steam_api64.dll steam_appid.txt; do chk cmp "$G/$f" "$W/pkg/$f"; done
chk grep -q "Steam files are in place" "$W/run.log"
echo "== leftovers"; chk test -z "$(find "$G" -name '.knighthub_tmp_*' -o -name 'data.win.knighthub_prev')"
[ $fail = 0 ] && echo "E2E51: ALL OK" || echo "E2E51: FAILURES"
exit $fail
