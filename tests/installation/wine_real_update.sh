#!/bin/bash
# DRBR: the update a player gets, end to end with the REAL programs under Wine (EMULATED Windows: Wine + wine-mono, not real
# Windows). The previous real release is installed from its DRBR-Setup.exe; its own launcher window finds the new real release
# and UPDATE NOW is clicked, as a player does. The new release is the real DRBR.zip's contents (the same DRBR-Setup.exe and
# package), signed with the real key, but its manifest points at this local server instead of GitHub; the server answers like
# GitHub (latest -> v<version> -> a file host, by redirects). The game is the test stand-in (GameStub).
# Checks: only the changed files' bytes are downloaded, the running launcher is replaced by DRBR Updater after it closes and
# comes back as the new version, the install verifies, PLAY reaches the starting room, Steam's folder and the saves stay.
# Usage: tests/installation/wine_real_update.sh <old DRBR-Setup.exe> <new payload dir> <new DRBR-Setup.exe> <vanilla data.win>
#        <private key> <stub dir> [screenshot dir]
set -uo pipefail
OLD="$(realpath "$1")"; NEWPAY="$(realpath "$2")"; NEWSETUP="$(realpath "$3")"; VANILLA="$(realpath "$4")"; KEY="$(realpath "$5")"
STUB="$(realpath "$6")"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
W="${DRBR_WINE_WORK:-$HERE/build/wine-real-update}"
SHOTS="$(realpath -m "${7:-$W/shots}")"
rm -rf "$W"; mkdir -p "$W" "$SHOTS"
export WINEPREFIX="$W/prefix" WINEARCH=win64 WINEDEBUG=-all
WINE=/usr/lib/wine/wine64
PASS=0; FAIL=0; RESULTS="$W/results.txt"; : > "$RESULTS"
ok()  { echo "PASS  $*" | tee -a "$RESULTS"; PASS=$((PASS+1)); }
bad() { echo "FAIL  $*" | tee -a "$RESULTS"; FAIL=$((FAIL+1)); }
chk() { local what="$1"; shift; if "$@"; then ok "$what"; else bad "$what"; fi; }
j()   { python3 -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8-sig')); print(eval(sys.argv[2]))" "$@" 2>/dev/null; }
snap(){ (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$2"; }
run() { timeout "${T:-900}" xvfb-run -a "$WINE" "$@" > "$W/last.out" 2>&1; echo $?; }
sha() { sha256sum < "$1" | cut -d' ' -f1; }
L='C:\users\root\AppData\Local\DRBR\DRBR Launcher.exe'

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
echo "OggS" > "$G/mus/knight.ogg"; echo "OggS" > "$G/mus/superchargedknight/x.ogg"
printf '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"C:\\\\Program Files (x86)\\\\Steam"\n\t}\n}\n' > "$STEAM/steamapps/libraryfolders.vdf"
printf '"AppState"\n{\n\t"appid"\t\t"1671210"\n\t"installdir"\t\t"DELTARUNE"\n}\n' > "$STEAM/steamapps/appmanifest_1671210.acf"
timeout 120 "$WINE" reg add 'HKCU\Software\Valve\Steam' /v SteamPath /t REG_SZ /d 'c:/program files (x86)/steam' /f > /dev/null 2>&1
SA="$LOCAL/DELTARUNE"; mkdir -p "$SA"
echo "player save 3" > "$SA/filech3_0"; echo "player save 2" > "$SA/filech2_0"; printf '[G3_0]\r\nName="KRIS"\r\n' > "$SA/dr.ini"
snap "$G" "$W/steam.before"; snap "$SA" "$W/saves.before"
D="$LOCAL/DRBR"

echo "== 1. the previous release, installed from its DRBR-Setup.exe"
cp "$OLD" "$C/DRBR-Setup.exe"
rc=$(T=1800 run 'C:\DRBR-Setup.exe' /S --result 'C:\r_install.json')
OLDVER=$(j "$C/r_install.json" "d.get('version')")
chk "the previous release installs (rc=$rc): DRBR $OLDVER" [ "$(j "$C/r_install.json" "d['ok']")" = "True" ]
cp "$D/payload/payload.json" "$W/old-payload.json"
OLDL=$(sha "$D/DRBR Launcher.exe")

echo "== 2. the new release on a local server that answers like GitHub"
NEWVER=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$NEWPAY/payload.json")
PORT=$((20000 + RANDOM % 20000))
SRVD="$W/srv"; mkdir -p "$SRVD/cdn/r" "$SRVD/latest" "$SRVD/download/v$NEWVER"
python3 "$HERE/packaging/release_tools.py" package --payload "$NEWPAY" --setup "$NEWSETUP" --out "$SRVD/cdn/r/DRBR.zip" --key "$KEY" \
  --base-url "http://127.0.0.1:$PORT/download/v$NEWVER/" > "$W/package.out" 2>&1
chk "the new release's DRBR.zip, signed, with this server's address ($(tail -1 "$W/package.out"))" [ -f "$SRVD/cdn/r/DRBR.zip" ]
echo "http://127.0.0.1:$PORT/download/v$NEWVER/DRBR.zip" > "$SRVD/latest/DRBR.zip.redirect"
echo "http://127.0.0.1:$PORT/cdn/r/DRBR.zip?sp=r&sig=test" > "$SRVD/download/v$NEWVER/DRBR.zip.redirect"
: > "$W/http.log"
python3 "$HERE/tests/updates/range_server.py" "$SRVD" "$PORT" "$W/http.log" & SRV=$!
sleep 1
python3 - "$D/drbr-settings.json" "http://127.0.0.1:$PORT/latest/DRBR.zip" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig')); d['update_url_override'] = sys.argv[2]; d['check_updates_on_start'] = True
json.dump(d, open(sys.argv[1], 'w'))
PY
python3 - "$NEWPAY/payload.json" "$W/new.env" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
app = {f['dest']: f['sha256'] for f in m['files'] if f['kind'] == 'app'}
open(sys.argv[2], 'w').write('NEWL=%s\nNEWU=%s\nNEWDW=%s\n' % (app['DRBR Launcher.exe'], app['DRBR Updater.exe'], m['drbr_data_win']['sha256']))
PY
. "$W/new.env"

echo "== 3. the player's way: the launcher window finds the update, UPDATE NOW"
N=60; while [ -e /tmp/.X11-unix/X$N ] || [ -e /tmp/.X$N-lock ]; do N=$((N + 1)); done; DISP=:$N   # (a free screen)
Xvfb $DISP -screen 0 1280x800x24 > /dev/null 2>&1 & XV=$!
export DISPLAY=$DISP
sleep 2
shot() { import -window root "$SHOTS/$1.png" 2>/dev/null; }
win()  { xdotool search --name "$1" 2>/dev/null | head -1; }
waitwin() { for i in $(seq 1 ${2:-120}); do w=$(win "$1"); [ -n "$w" ] && { echo "$w"; return 0; }; sleep 0.5; done; return 1; }
click_rel() { eval "$(xdotool getwindowgeometry --shell "$1")"; xdotool mousemove $((X + $2)) $((Y + $3)) click 1; }
"$WINE" "$L" > "$W/gui1.out" 2>&1 &
UW=$(waitwin "DRBR UPDATE AVAILABLE" 240)
sleep 3; shot 01_update_available
chk "the launcher ($OLDVER) offers DRBR $NEWVER" [ -n "$UW" ]
: > "$W/http.update.log"; cp "$W/http.log" "$W/http.check.log"; : > "$W/http.log"
[ -n "$UW" ] && click_rel "$UW" 110 170
# the update, then the launcher closes; DRBR Updater swaps the new launcher in and starts it again
for i in $(seq 1 900); do
  grep -q "\"version\": \"$NEWVER\"" "$D/drbr-install.json" 2>/dev/null && [ "$(sha "$D/DRBR Launcher.exe" 2>/dev/null)" = "$NEWL" ] && break
  sleep 1
done
LW=$(waitwin "DRBR Launcher" 120)
sleep 6; shot 02_after_update
chk "DRBR $NEWVER is installed" grep -q "\"version\": \"$NEWVER\"" "$D/drbr-install.json"
chk "DRBR Updater swapped in the new launcher after the old one closed" [ "$(sha "$D/DRBR Launcher.exe")" = "$NEWL" ]
chk "the new launcher is open again (restarted by DRBR Updater)" [ -n "$LW" ]
chk "DRBR Updater is the new one" [ "$(sha "$D/DRBR Updater.exe")" = "$NEWU" ]
chk "nothing left over (staged launcher, .old, .part)" [ ! -f "$D/staging/pending/DRBR Launcher.exe" -a ! -f "$D/DRBR Launcher.exe.old" -a ! -f "$D/DRBR Launcher.exe.part" ]
grep -h "launcher\|Launcher\|Updater\|swap" "$D/logs/"*.log 2>/dev/null | tail -12 > "$W/swap.log"
timeout 30 /usr/lib/wine/wineserver -k 2>/dev/null; sleep 2
kill $XV 2>/dev/null; unset DISPLAY

echo "== 4. what was downloaded"
cp "$W/http.log" "$W/http.update.log"
python3 - "$HERE/packaging" "$SRVD/cdn/r/DRBR.zip" "$W/old-payload.json" "$NEWPAY/payload.json" "$W/http.check.log" "$W/http.update.log" > "$W/bytes.txt" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[1])
import release_tools as rt
mb, sig, at, _ = rt.package_view(sys.argv[2])
old = {f['file']: f['sha256'] for f in json.load(open(sys.argv[3]))['files']}
new = json.load(open(sys.argv[4]))['files']
changed = [f for f in new if old.get(f['file']) != f['sha256']]
def ranges(p):
    out = []
    for l in open(p):
        w = l.split()
        if w and w[0] == 'RANGE':
            a, b = w[-1].split('-'); out.append((int(a), int(b)))
        elif w and w[0] == 'GET':
            out.append((0, 1 << 62))
    return out
chk_, upd = ranges(sys.argv[5]), ranges(sys.argv[6])
def over(rs, o, n):
    return sum(max(0, min(o + n - 1, b) - max(o, a) + 1) for a, b in rs)
total_c = sum(b - a + 1 for a, b in chk_); total_u = sum(b - a + 1 for a, b in upd)
need = sum(f['size'] for f in changed)
# (the launcher reads DRBR.zip's directory from its end - the last 64 KB, once per check: that may cover the end of the file
# stored just before the directories; those reads are counted in the total, not as a download of that file)
import os
zl = os.path.getsize(sys.argv[2])
body = [(a, b) for a, b in upd if b != zl - 1]
unchanged_read = {f['file']: over(body, *at[f['file']]) for f in new if f not in changed and over(body, *at[f['file']]) > 0}
print('TAILREADS %d' % sum(1 for a, b in upd if b == zl - 1))
print('CHECK %d' % total_c)
print('UPDATE %d' % total_u)
print('CHANGED %d %s' % (need, ' '.join('%s(%d)' % (f['file'], f['size']) for f in changed)))
print('UNCHANGED_READ %s' % (json.dumps(unchanged_read)))
print('WHOLE %d' % sum(1 for a, b in upd if b >= 1 << 61))
PY
cat "$W/bytes.txt"
CHK=$(awk '/^CHECK/{print $2}' "$W/bytes.txt"); UPD=$(awk '/^UPDATE/{print $2}' "$W/bytes.txt"); NEED=$(awk '/^CHANGED/{print $2}' "$W/bytes.txt")
chk "the check read only the end of DRBR.zip ($CHK bytes), through GitHub-like redirects ($(grep -c REDIRECT "$W/http.check.log") redirects)" [ "${CHK:-0}" -gt 0 -a "${CHK:-0}" -lt 300000 ]
chk "the update read only the changed files: $UPD bytes for $NEED bytes of changed files ($(awk '/^CHANGED/{$1=$2=""; print}' "$W/bytes.txt"))" [ "${UPD:-0}" -ge "${NEED:-1}" -a "${UPD:-0}" -lt $(( ${NEED:-0} + 1500000 )) ]
chk "no unchanged file (the music, the Steam files) was downloaded again: $(awk '/^UNCHANGED_READ/{print $2}' "$W/bytes.txt")" [ "$(awk '/^UNCHANGED_READ/{print $2}' "$W/bytes.txt")" = "{}" -a "$(awk '/^WHOLE/{print $2}' "$W/bytes.txt")" = 0 ]
kill $SRV 2>/dev/null

echo "== 5. the updated DRBR"
rc=$(run "$L" --verify --result 'C:\r_verify.json')
chk "the install verifies with the new launcher (rc=$rc)" [ "$rc" = 0 ]
chk "DRBR's data.win is the new build" [ "$(sha "$D/game/chapter3_windows/data.win")" = "$NEWDW" ]
chk "the provided starting save is in place" [ "$(sha "$D/game/chapter3_windows/drbr_data/start_filech3")" = "fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082" ]
rc=$(DRBR_STUB_SECONDS=2 run "$L" --play --wait-exit --result 'C:\r_play.json')
chk "PLAY: the game started in the starting room: $(j "$C/r_play.json" "d.get('start'), d.get('room'), d.get('error','')")" [ "$(j "$C/r_play.json" "d['ok'] and d['room']=='room_dw_snow_zone'")" = "True" ]
chk "PLAY: the player's own saves were not touched" [ "$(j "$C/r_play.json" "len(d.get('vanilla_changes',[1]))")" = "0" ]
snap "$G" "$W/steam.after"; chk "Steam's DELTARUNE folder is unchanged" cmp -s "$W/steam.before" "$W/steam.after"
rm -f "$SA/stub_runs.log"; rm -rf "$SA/drbr_profile"; snap "$SA" "$W/saves.after"; chk "the player's saves are unchanged (besides drbr_profile)" cmp -s "$W/saves.before" "$W/saves.after"

echo
echo "real update $OLDVER -> $NEWVER: $PASS passed, $FAIL failed" | tee -a "$RESULTS"
[ $FAIL = 0 ]
