#!/bin/bash
# DRBR end to end with the REAL Windows programs (DRBR-Setup.exe, DRBR Launcher.exe, DRBR Updater.exe) under Wine
# (EMULATED Windows: Wine + wine-mono, not real Windows). The game is a TEST STAND-IN for DELTARUNE.exe (GameStub: it does
# what the DRBR build's start does with the files); the data.win is the REAL vanilla Chapter 3 data.win, the patch the
# REAL release patch, the starting save the REAL provided save.
# Usage: tests/installation/wine_e2e.sh <DRBR-Setup.exe with payload> <payload dir> <vanilla data.win> <private key> <stub dir>
set -uo pipefail
SETUP="$(realpath "$1")"; PAYLOAD="$(realpath "$2")"; VANILLA="$(realpath "$3")"; KEY="$(realpath "$4")"; STUB="$(realpath "$5")"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
W="${DRBR_WINE_WORK:-$HERE/build/wine-e2e}"
rm -rf "$W"; mkdir -p "$W"
export WINEPREFIX="$W/prefix" WINEARCH=win64 WINEDEBUG=-all
WINE=/usr/lib/wine/wine64
PASS=0; FAIL=0; RESULTS="$W/results.txt"; : > "$RESULTS"
ok()  { echo "PASS  $*" | tee -a "$RESULTS"; PASS=$((PASS+1)); }
bad() { echo "FAIL  $*" | tee -a "$RESULTS"; FAIL=$((FAIL+1)); }
chk() { local what="$1"; shift; if "$@"; then ok "$what"; else bad "$what"; fi; }
j()   { python3 -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8-sig')); print(eval(sys.argv[2]))" "$@" 2>/dev/null; }
snap(){ (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$2"; }
run() { timeout "${T:-900}" xvfb-run -a "$WINE" "$@" > "$W/last.out" 2>&1; echo $?; }

echo "== Wine prefix"
timeout 300 xvfb-run -a "$WINE" wineboot --init > "$W/wineboot.log" 2>&1
C="$WINEPREFIX/drive_c"
LOCAL="$C/users/root/AppData/Local"
mkdir -p "$LOCAL"

echo "== a Steam-like DELTARUNE"
STEAM="$C/Program Files (x86)/Steam"
G="$STEAM/steamapps/common/DELTARUNE"
CH="$G/chapter3_windows"
mkdir -p "$CH/lang" "$CH/vid" "$G/mus/superchargedknight"
cp "$STUB/DELTARUNE.exe" "$G/DELTARUNE.exe"
printf '[Windows]\r\nSleepMargin=30\r\nUsex64=True\r\n' > "$G/options.ini"
printf '[Windows]\r\nSleepMargin=30\r\nUsex64=True\r\n[Easing_and_Tweening]\r\n' > "$CH/options.ini"
cp "$VANILLA" "$CH/data.win"; chmod 444 "$CH/data.win"
head -c 5000 /dev/urandom > "$CH/audiogroup1.dat"; echo "OggS" > "$CH/snd_icespell.ogg"; echo '{"x":1}' > "$CH/lang/lang_ja.json"
head -c 3000 /dev/zero > "$CH/vid/tennaIntroF1_compressed_28.mp4"; echo "OggS" > "$G/mus/knight.ogg"; echo "OggS" > "$G/mus/superchargedknight/x.ogg"
echo "a stray save" > "$CH/filech3_1"; echo "old" > "$CH/KNIGHT_HUB_MANIFEST.txt"; echo "another mod" > "$G/dxgi.dll"
printf '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"C:\\\\Program Files (x86)\\\\Steam"\n\t}\n}\n' > "$STEAM/steamapps/libraryfolders.vdf"
printf '"AppState"\n{\n\t"appid"\t\t"1671210"\n\t"installdir"\t\t"DELTARUNE"\n}\n' > "$STEAM/steamapps/appmanifest_1671210.acf"
timeout 120 "$WINE" reg add 'HKCU\Software\Valve\Steam' /v SteamPath /t REG_SZ /d 'c:/program files (x86)/steam' /f > /dev/null 2>&1
SA="$LOCAL/DELTARUNE"; mkdir -p "$SA"
echo "player save 3" > "$SA/filech3_0"; echo "player save 2" > "$SA/filech2_0"; printf '[G3_0]\r\nName="KRIS"\r\n' > "$SA/dr.ini"
printf '[KEYBOARD_CONTROLS]\r\n0=40\r\n' > "$SA/keyconfig_0.ini"; printf '[online]\r\nskin=3\r\n' > "$SA/knightfights_online.ini"
snap "$G" "$W/steam.before"; snap "$SA" "$W/saves.before"
D="$LOCAL/DRBR"

echo "== 1. install (silent, DELTARUNE found through Steam's registry entry)"
cp "$SETUP" "$C/DRBR-Setup.exe"
rc=$(T=1800 run 'C:\DRBR-Setup.exe' /S --result 'C:\r_install.json')
chk "Setup exits 0 (rc=$rc)" [ "$rc" = 0 ]
chk "Setup result ok, DELTARUNE found and vanilla: $(j "$C/r_install.json" "d.get('game_state'), d.get('version'), d.get('error','')")" [ "$(j "$C/r_install.json" "d['ok'] and d['game_state']=='vanilla'")" = "True" ]
DRBRSHA=$(python3 -c "import json; print(json.load(open('$PAYLOAD/payload.json'))['drbr_data_win']['sha256'])")
chk "DRBR's data.win is the DRBR build (real vanilla + real patch, by Windows xdelta3.exe)" [ "$(sha256sum < "$D/game/chapter3_windows/data.win" | cut -d' ' -f1)" = "$DRBRSHA" ]
chk "the provided starting save is next to it" [ "$(sha256sum < "$D/game/chapter3_windows/drbr_data/start_filech3" | cut -d' ' -f1)" = "fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082" ]
chk "the profile config says template mode" grep -q "start_mode=template" "$D/game/chapter3_windows/drbr_data/drbr_profile.cfg"
chk "DRBR Launcher, DRBR Updater and xdelta3.exe are installed" [ -f "$D/DRBR Launcher.exe" -a -f "$D/DRBR Updater.exe" -a -f "$D/tools/xdelta3.exe" ]
chk "the game's own files are copied, the leftovers are not" [ -f "$D/game/chapter3_windows/audiogroup1.dat" -a -f "$D/game/chapter3_windows/lang/lang_ja.json" -a ! -f "$D/game/chapter3_windows/filech3_1" -a ! -f "$D/game/dxgi.dll" -a ! -f "$D/game/chapter3_windows/KNIGHT_HUB_MANIFEST.txt" ]
chk "the Apps & features entry is written (HKCU, no admin)" bash -c "timeout 60 '$WINE' reg query 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DRBR' /v DisplayName 2>/dev/null | grep -q 'DELTARUNE BATTLE ROYALE'"
snap "$G" "$W/steam.after1"; chk "the Steam DELTARUNE folder is unchanged" cmp -s "$W/steam.before" "$W/steam.after1"
snap "$SA" "$W/saves.after1"; chk "the player's saves are unchanged" cmp -s "$W/saves.before" "$W/saves.after1"

echo "== 2. verify, play"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_verify.json')
chk "launcher --verify ok (rc=$rc)" [ "$rc" = 0 ]
rc=$(DRBR_STUB_SECONDS=2 run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --play --wait-exit --result 'C:\r_play.json')
chk "PLAY: the game started and reported the starting room: $(j "$C/r_play.json" "d.get('start'), d.get('room'), d.get('error','')")" [ "$(j "$C/r_play.json" "d['ok'] and d['start']=='ok' and d['room']=='room_dw_snow_zone'")" = "True" ]
chk "PLAY: the player's own saves were not touched (the launcher's after-game check)" [ "$(j "$C/r_play.json" "len(d.get('vanilla_changes',[1]))")" = "0" ]
chk "the game was started in DRBR's copy with -game chapter3_windows\\data.win" grep -q 'DRBR\\game game=chapter3_windows\\data.win' "$SA/stub_runs.log"
chk "the game's DRBR save went to drbr_profile (the provided save)" [ "$(sha256sum < "$SA/drbr_profile/filech3_0" | cut -d' ' -f1)" = "fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082" ]
rm -f "$SA/stub_runs.log"; snap "$SA" "$W/saves.after2"
python3 - "$W/saves.before" "$W/saves.after2" > "$W/savediff.txt" <<'PY'
import sys
a = dict((l.split()[1], l.split()[0]) for l in open(sys.argv[1]))
b = dict((l.split()[1], l.split()[0]) for l in open(sys.argv[2]))
print(sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k) and not k.startswith('./drbr_profile/')))
PY
chk "only drbr_profile changed in the save folder: $(cat "$W/savediff.txt")" [ "$(cat "$W/savediff.txt")" = "[]" ]

echo "== 3. restore starting save"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --restore-save --result 'C:\r_restore.json')
chk "RESTORE STARTING SAVE moved the DRBR save aside ($(j "$C/r_restore.json" "d.get('moved')"))" [ "$(j "$C/r_restore.json" "d['ok'] and d['moved']>=1")" = "True" -a ! -f "$SA/drbr_profile/filech3_0" ]

echo "== 4. update from a local release server (signed manifest, only changed files downloaded)"
PORT=$((20000 + RANDOM % 20000))
python3 "$HERE/tests/updates/make_test_releases.py" "$PAYLOAD" "$W/releases" "$KEY" "http://127.0.0.1:$PORT" > /dev/null
: > "$W/http.log"
python3 "$HERE/tests/updates/range_server.py" "$W/releases" "$PORT" "$W/http.log" & SRV=$!
sleep 1
python3 - "$D/drbr-settings.json" "http://127.0.0.1:$PORT/good/update-manifest.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig'))
d['update_url_override'] = sys.argv[2]
json.dump(d, open(sys.argv[1], 'w'))
PY
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --check --result 'C:\r_check.json')
chk "update check: $(j "$C/r_check.json" "d.get('installed'), d.get('available'), d.get('update'), d.get('error','')")" [ "$(j "$C/r_check.json" "d['ok'] and d['update']")" = "True" ]
rc=$(T=1800 run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --update --result 'C:\r_update.json')
chk "update installed: $(j "$C/r_update.json" "d.get('installed_before'), d.get('installed_after'), d.get('error','')")" [ "$(j "$C/r_update.json" "d['ok'] and d['installed_after']=='1.0.1'")" = "True" ]
chk "only the changed file was downloaded ($(grep -c . "$W/http.log") requests)" bash -c "! grep -q 'drbr-chapter3.xdelta\|drbr-music' '$W/http.log' && grep -q 'doc-README.md' '$W/http.log'"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_verify2.json')
chk "after the update the install verifies (rc=$rc)" [ "$rc" = 0 ]
chk "after the update the same starting save is in place" [ "$(sha256sum < "$D/game/chapter3_windows/drbr_data/start_filech3" | cut -d' ' -f1)" = "fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082" ]
python3 - "$D/drbr-settings.json" "http://127.0.0.1:$PORT/badsig/update-manifest.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig')); d['update_url_override'] = sys.argv[2]; json.dump(d, open(sys.argv[1], 'w'))
PY
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --update --result 'C:\r_badsig.json')
chk "a release not signed by DRBR's key is refused: $(j "$C/r_badsig.json" "d.get('code')")" [ "$(j "$C/r_badsig.json" "d.get('code')")" = "bad_signature" ]
python3 - "$D/drbr-settings.json" "http://127.0.0.1:$PORT/corrupt/update-manifest.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig')); d['update_url_override'] = sys.argv[2]; json.dump(d, open(sys.argv[1], 'w'))
PY
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --update --result 'C:\r_corrupt.json')
chk "a damaged download is refused: $(j "$C/r_corrupt.json" "d.get('code')")" [ "$(j "$C/r_corrupt.json" "d.get('code')")" = "bad_download" ]
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_verify3.json')
chk "after the refused updates DRBR 1.0.1 still verifies" [ "$rc" = 0 ]
kill $SRV 2>/dev/null

echo "== 5. repair"
python3 -c "
f=open('$D/game/chapter3_windows/data.win','r+b'); f.seek(4096); b=f.read(1); f.seek(4096); f.write(bytes([b[0]^0xff])); f.close()"
rm -f "$D/game/chapter3_windows/drbr_data/start_filech3"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_v4.json')
chk "a damaged install is noticed (rc=$rc: $(j "$C/r_v4.json" "d.get('problem')"))" [ "$rc" = 10 ]
rc=$(T=1800 run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --repair --result 'C:\r_repair.json')
chk "REPAIR rebuilt it (rc=$rc $(j "$C/r_repair.json" "d.get('error','')"))" [ "$rc" = 0 ]
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_v5.json')
chk "after REPAIR the install verifies" [ "$rc" = 0 ]

echo "== 6. an interrupted reinstall (the process killed mid-way) is undone at the next start"
( timeout 1800 xvfb-run -a "$WINE" 'C:\DRBR-Setup.exe' /S --result 'C:\r_killed.json' > /dev/null 2>&1 & )
for i in $(seq 1 600); do
  if [ -f "$D/drbr-transaction.json" ] && ls "$D/staging/"*/game/chapter3_windows/data.win > /dev/null 2>&1; then break; fi
  sleep 0.5
done
sleep 1
timeout 30 /usr/lib/wine/wineserver -k 2>/dev/null; sleep 2
chk "the reinstall was killed mid-way (a transaction was open)" [ -f "$D/drbr-transaction.json" ]
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_v6.json')
chk "the next launcher start undid it and the install verifies: $(j "$C/r_v6.json" "d.get('recovered','')")" [ "$rc" = 0 ]
chk "  ... no transaction is left open" [ ! -f "$D/drbr-transaction.json" ]

echo "== 7. DRBR Updater swaps the launcher (self-update)"
cp "$D/DRBR Launcher.exe" "$W/newlauncher.exe"; printf 'DRBR-TEST-OVERLAY' >> "$W/newlauncher.exe"
mkdir -p "$D/staging/pending"; cp "$W/newlauncher.exe" "$D/staging/pending/DRBR Launcher.exe"
NEWSHA=$(sha256sum < "$W/newlauncher.exe" | cut -d' ' -f1)
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Updater.exe" --swap 'C:\users\root\AppData\Local\DRBR\staging\pending\DRBR Launcher.exe' --target 'C:\users\root\AppData\Local\DRBR\DRBR Launcher.exe' --sha256 "$NEWSHA" --root 'C:\users\root\AppData\Local\DRBR')
chk "the updater replaced the launcher with the new, checked file (rc=$rc)" [ "$rc" = 0 -a "$(sha256sum < "$D/DRBR Launcher.exe" | cut -d' ' -f1)" = "$NEWSHA" -a ! -f "$D/DRBR Launcher.exe.old" ]
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_v7.json')
chk "the swapped launcher runs" [ "$rc" = 0 ]
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Updater.exe" --swap 'C:\users\root\AppData\Local\DRBR\DRBR Updater.exe' --target 'C:\users\root\AppData\Local\DRBR\DRBR Launcher.exe' --sha256 0000000000000000000000000000000000000000000000000000000000000000 --root 'C:\users\root\AppData\Local\DRBR')
chk "a new launcher with the wrong checksum is refused; the old one stays (rc=$rc)" [ "$rc" = 4 -a "$(sha256sum < "$D/DRBR Launcher.exe" | cut -d' ' -f1)" = "$NEWSHA" ]

echo "== 8. uninstall"
mkdir -p "$SA/drbr_profile"; echo x > "$SA/drbr_profile/filech3_0"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --uninstall --quiet --result 'C:\r_uninstall.json')
chk "uninstall (rc=$rc)" [ "$rc" = 0 ]
chk "DRBR's game copy, package, base and records are gone" [ ! -d "$D/game" -a ! -d "$D/payload" -a ! -d "$D/base" -a ! -f "$D/drbr-install.json" ]
chk "the Apps & features entry is gone" bash -c "! timeout 60 '$WINE' reg query 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DRBR' > /dev/null 2>&1"
snap "$G" "$W/steam.after9"; chk "the Steam DELTARUNE folder is still unchanged" cmp -s "$W/steam.before" "$W/steam.after9"
rm -rf "$SA/drbr_profile"; snap "$SA" "$W/saves.after9"; chk "the player's saves are still unchanged" cmp -s "$W/saves.before" "$W/saves.after9"

echo "== 9. install from a package folder in pieces (DRBR-Setup.exe + payload\\ with files of at most 24 MB)"
PLAIN="$(dirname "$SETUP")/bin/DRBR-Setup.exe"
if [ -f "$PLAIN" ]; then
  mkdir -p "$C/DRBR-folder"
  cp "$PLAIN" "$C/DRBR-folder/DRBR-Setup.exe"
  python3 "$HERE/packaging/split_payload.py" "$PAYLOAD" "$C/DRBR-folder/payload" > /dev/null
  chk "the package folder has only pieces of at most 24 MB" bash -c "[ \$(find '$C/DRBR-folder/payload' -size +24000000c | wc -l) = 0 ]"
  rc=$(T=1800 run 'C:\DRBR-folder\DRBR-Setup.exe' /S --result 'C:\r_folder.json')
  chk "install from the folder in pieces: $(j "$C/r_folder.json" "d.get('ok'), d.get('version'), d.get('error','')")" [ "$(j "$C/r_folder.json" "d['ok']")" = "True" ]
  rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --verify --result 'C:\r_v9.json')
  chk "  ... and it verifies (rc=$rc)" [ "$rc" = 0 ]
  chk "  ... DRBR's data.win is the DRBR build" [ "$(sha256sum < "$D/game/chapter3_windows/data.win" | cut -d' ' -f1)" = "$DRBRSHA" ]
  chk "  ... no unpacked package is left in staging" bash -c "! ls -d '$D/staging/'setup-* > /dev/null 2>&1"
fi

echo "== 10. a PC with the older Knight Hub installed in Steam's folder (its own clean backup next to it)"
rc=$(run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --uninstall --quiet --result 'C:\r_uninstall10.json')
chmod 644 "$CH/data.win"; cp "$VANILLA" "$CH/data.win.vanilla"; chmod 444 "$CH/data.win.vanilla"
python3 -c "
f=open('$CH/data.win','r+b'); f.seek(1000); f.write(b'KNIGHT HUB IN PLACE'); f.close()"
printf 'mod_version=51\r\npatched_size=1\r\n' > "$CH/knight_hub_build.txt"
snap "$G" "$W/steam.before10"
rc=$(T=1800 run 'C:\DRBR-Setup.exe' /S --result 'C:\r_install10.json')
chk "install on a game with the Knight Hub in place: $(j "$C/r_install10.json" "d.get('game_state'), d.get('ok'), d.get('error','')")" [ "$(j "$C/r_install10.json" "d['ok'] and d['game_state']=='knight_hub_in_place'")" = "True" ]
chk "  ... DRBR's data.win is the DRBR build (from the Knight Hub's clean backup)" [ "$(sha256sum < "$D/game/chapter3_windows/data.win" | cut -d' ' -f1)" = "$DRBRSHA" ]
snap "$G" "$W/steam.after10"; chk "  ... the Steam folder (the Knight Hub, its backup) is unchanged" cmp -s "$W/steam.before10" "$W/steam.after10"
rc=$(DRBR_STUB_SECONDS=2 run "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" --play --wait-exit --result 'C:\r_play10.json')
chk "  ... PLAY starts in the starting room: $(j "$C/r_play10.json" "d.get('start'), d.get('room')")" [ "$(j "$C/r_play10.json" "d['ok'] and d['room']=='room_dw_snow_zone'")" = "True" ]

echo
echo "wine e2e: $PASS passed, $FAIL failed" | tee -a "$RESULTS"
[ $FAIL = 0 ]
