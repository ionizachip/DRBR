#!/bin/bash
# DRBR: the windows of DRBR-Setup.exe and DRBR Launcher.exe under Wine on a virtual screen - screenshots to look at, and an
# install / PLAY done by clicking (xdotool). Reuses the prefix of wine_e2e.sh (its Steam-like DELTARUNE).
# Usage: tests/installation/wine_gui.sh <DRBR-Setup.exe with payload> <out dir for screenshots>
set -uo pipefail
SETUP="$(realpath "$1")"; OUT="$(realpath -m "$2")"; mkdir -p "$OUT"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
W="${DRBR_WINE_WORK:-$HERE/build/wine-e2e}"
export WINEPREFIX="$W/prefix" WINEARCH=win64 WINEDEBUG=-all
WINE=/usr/lib/wine/wine64
C="$WINEPREFIX/drive_c"
D="$C/users/root/AppData/Local/DRBR"
DISP=:77
Xvfb $DISP -screen 0 1280x800x24 > /dev/null 2>&1 & XV=$!
export DISPLAY=$DISP
sleep 2
shot() { import -window root "$OUT/$1.png" 2>/dev/null; echo "screenshot $OUT/$1.png"; }
win()  { xdotool search --name "$1" 2>/dev/null | head -1; }
waitwin() { for i in $(seq 1 120); do w=$(win "$1"); [ -n "$w" ] && { echo "$w"; return 0; }; sleep 0.5; done; return 1; }
click_rel() { # window, x, y (client coordinates at 96 dpi)
  eval "$(xdotool getwindowgeometry --shell "$1")"
  xdotool mousemove $((X + $2)) $((Y + $3)) click 1
}

rm -rf "$D"
cp "$SETUP" "$C/DRBR-Setup.exe"
"$WINE" 'C:\DRBR-Setup.exe' > "$W/gui_setup.out" 2>&1 & SP=$!
WID=$(waitwin "DRBR Setup") || { echo "FAIL the Setup window did not open"; kill $XV; exit 1; }
sleep 12
shot 01_setup_start
# INSTALL DRBR (the button's middle: 280, 260)
click_rel "$WID" 280 260
for i in $(seq 1 600); do [ -f "$D/drbr-install.json" ] && [ ! -f "$D/drbr-transaction.json" ] && break; sleep 1; done
sleep 4
shot 02_setup_done
# PLAY DRBR (same place) -> the launcher with --autoplay -> the game (the test stand-in)
click_rel "$WID" 280 260
LW=$(waitwin "DRBR Launcher") && echo "launcher window $LW"
sleep 10
shot 03_launcher_after_play
cat "$C/users/root/AppData/Local/DELTARUNE/drbr_profile/last_start.ini" 2>/dev/null | head -8
sleep 6
shot 04_launcher_after_game
# the update prompt: a newer signed release on a local server (needs the payload and the key: args 3 and 4)
if [ $# -ge 4 ]; then
  timeout 20 /usr/lib/wine/wineserver -k 2>/dev/null; sleep 1
  PAYLOAD="$(realpath "$3")"; KEY="$(realpath "$4")"
  PORT=$((20000 + RANDOM % 20000))
  python3 "$HERE/tests/updates/make_test_releases.py" "$PAYLOAD" "$W/releases-gui" "$KEY" "http://127.0.0.1:$PORT" > /dev/null
  : > "$W/http-gui.log"
  python3 "$HERE/tests/updates/range_server.py" "$W/releases-gui" "$PORT" "$W/http-gui.log" & SRV=$!
  python3 - "$D/drbr-settings.json" "http://127.0.0.1:$PORT/good/DRBR.zip" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8-sig')); d['update_url_override'] = sys.argv[2]; d['check_updates_on_start'] = True; json.dump(d, open(sys.argv[1], 'w'))
PY
  "$WINE" "C:\\users\\root\\AppData\\Local\\DRBR\\DRBR Launcher.exe" > /dev/null 2>&1 &
  UW=$(waitwin "DRBR UPDATE AVAILABLE") && echo "update window $UW"
  sleep 3
  shot 05_update_available
  # UPDATE NOW (the left button of the dialog: 110, 170)
  [ -n "${UW:-}" ] && click_rel "$UW" 110 170
  # (the test release is the payload's version with 1 added to its last number - make_test_releases.py)
  V1=$(python3 -c "import json,sys; v=json.load(open(sys.argv[1]))['version'].split('.'); v[-1]=str(int(v[-1])+1); print('.'.join(v))" "$PAYLOAD/payload.json")
  for i in $(seq 1 300); do grep -q "\"version\": \"$V1\"" "$D/drbr-install.json" 2>/dev/null && break; sleep 1; done
  # the "DRBR <version> is installed." box comes once the update has finished; OK, then the refreshed window
  MB=""; for i in $(seq 1 120); do MB=$(xdotool search --name "^DRBR$" 2>/dev/null | head -1); [ -n "$MB" ] && break; sleep 0.5; done
  sleep 2
  shot 06_update_done
  [ -n "$MB" ] && { xdotool windowactivate --sync "$MB" 2>/dev/null; xdotool key --window "$MB" Return; }
  sleep 3
  shot 07_after_update
  grep -o '"version": "[^"]*"' "$D/drbr-install.json" | head -1
  kill $SRV 2>/dev/null
fi
timeout 20 /usr/lib/wine/wineserver -k 2>/dev/null
kill $XV 2>/dev/null
echo "GUI run done"
