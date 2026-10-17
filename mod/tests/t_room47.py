"""Build 47: the room over the RELAY (real sockets, the real relay.js, the real GML of every game): SOUL colours in the room,
watching from the room's page, the room's counts, the rematch, the host leaving while someone watches, and the settings
kept across restarts. (The match itself runs in t_br_* / t_view47; here the games run the room's code: kfo_tick.)

Parts (the documents' tests; the numbers printed are the measured ones):
  colors   eight players with their own colours: every room list has every colour right; 100 colour changes in the room
           reach every game; a player who leaves and comes back has their colour again; a rematch keeps them; two players
           with the same colour keep their own names and places; a bad colour code is refused
  watch    SPEC-001: 100 SPECTATE MATCH from the room's page (each: the watching START, counted by the host, back to the room,
           counted off); SPEC-008: a watcher gets the match's results; zero damage / skills / knight changes from a watcher
           (forged messages too); QOL-004: the counts (players, watching) in every game's room list; QOL-003: the rematch
           (watchers back, READY = rematch vote, the next match clean); SPEC-009: the host leaves during the match with a
           watcher in it - the room goes on under the next host, the watcher is told and goes back safely
  persist  QOL-002: 100 save / reload of every SOUL VISIBILITY / SOUL APPEARANCE / VIEW setting (random values each time):
           a restarted game reads exactly what was saved
Usage: python3 t_room47.py [part ...]   (default: all)"""
import sys, os, json, time, random, socket, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_net_common import *

RELAY = '/home/claude/work/online/server/relay.js'
NODE = '/opt/node22/bin/node'
STATS = {}
PRESETS = [255, 4235519, 65535, 65280, 16776960, 16711680, 16711808, 16744703, 16777215]  # red .. white (BGR)


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_relay():
    port = free_port()
    p = subprocess.Popen([NODE, RELAY, '--port', str(port), '--host', '127.0.0.1', '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            return p, port
        except OSError:
            time.sleep(0.05)
    raise RuntimeError('relay did not start')


def mk(port, name, skin, col=None):
    s = game(name, skin)
    s.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % port)
    if col is not None:
        s.run('global.kfo.look.col = %d;' % col)
    return s


def room(port, specs):
    """specs: [(name, skin, col)]; the first makes the room, the others join it"""
    sims = [mk(port, *sp) for sp in specs]
    A = sims[0]
    A.run('kfo_create();')
    ok(pump([A], lambda: J(A, 'global.kfo.st') == 'room', 5), 'the room is made')
    code = J(A, 'global.kfo.code')
    for s in sims[1:]:
        s.run('kfo_join("%s");' % code)
    n = len(sims)
    ok(pump(sims, lambda: all(J(s, 'global.kfo.st') == 'room' and len(J(s, 'kfo_lobby_players()')) == n for s in sims), 10),
       '%d games in the room' % n)
    for s in sims:
        s.code = code
    return sims


def cols_of(s):
    return {p['n']: p.get('cl', -1) for p in J(s, 'kfo_lobby_players()')}


def leave_all(sims):
    for s in sims:
        try:
            s.run('kfo_leave();')
        except Exception:
            pass
    pump(sims, None, 0.3)


# ---------- colours in the room ----------
def part_colors(port):
    names = ['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna']
    want = {names[i]: PRESETS[i] for i in range(8)}
    sims = room(port, [(names[i], 1 + i % 4, PRESETS[i]) for i in range(8)])
    pump(sims, lambda: all(cols_of(s) == want for s in sims), 5)
    right = sum(1 for s in sims for n, c in cols_of(s).items() if want.get(n) == c)
    ok(right == 64, 'colors: 8 players with their own colors - every room list has every color right (%d / 64)' % right)
    # 100 changes in the room (the SOUL APPEARANCE page's lines: the colour kept, then sent), random players and colours
    rnd = random.Random(47)
    synced = 0
    worst = 0.0
    for c in range(100):
        i = rnd.randrange(8)
        col = rnd.choice(PRESETS + [rnd.randrange(0, 0xFFFFFF)])
        sims[i].run('global.kfo.look.col = %d; kfo_ini_save(); kfo_look_sent();' % col)
        want[names[i]] = col
        t0 = time.time()
        if pump(sims, lambda: all(cols_of(s).get(names[i]) == col for s in sims), 5):
            synced += 1
            worst = max(worst, time.time() - t0)
    ok(synced == 100, 'colors: 100 color changes in the room - every game shows the new color %d / 100 times (slowest %.2fs)' % (synced, worst))
    STATS['colors: changes'] = {'changes': 100, 'synced': synced, 'slowest_s': round(worst, 2)}
    # two players with the same colour: still told apart (their own names, their own places in the list, own SOUL markers)
    sims[1].run('global.kfo.look.col = %d; kfo_look_sent();' % want['Kris'])
    want['Susie'] = want['Kris']
    pump(sims, lambda: cols_of(sims[5]).get('Susie') == want['Kris'], 5)
    pl = J(sims[5], 'kfo_lobby_players()')
    same = [p for p in pl if p.get('cl') == want['Kris']]
    ok(len(same) >= 2 and len(set(p['n'] for p in same)) == len(same) and len(set(p['pid'] for p in same)) == len(same),
       'colors: two players with the same color keep their own names and ids in the list (%s)' % [(p['n'], p['pid']) for p in same])
    # a player leaves and comes back: their colour again (kept on their computer, sent with their hello)
    keep = J(sims[2], 'global.kfo.look.col')
    sims[2].run('kfo_leave();')
    pump(sims, lambda: all(len(J(s, 'kfo_lobby_players()')) == 7 for s in sims if s is not sims[2]), 5)
    sims[2].run('global.kfo = undefined; kfo_get(); global.kfo.srv = "127.0.0.1"; global.kfo.port = %d; kfo_join("%s");' % (port, sims[0].code))
    back = pump(sims, lambda: all(cols_of(s).get('Ralsei') == keep for s in sims), 8)
    ok(back and J(sims[2], 'global.kfo.look.col') == keep, 'colors: Ralsei leaves, restarts the game, comes back - their color %06X again in every game' % keep)
    # a bad colour code is refused (the code entry: #RRGGBB or #RGB, nothing else)
    tests = [('#A040FF', 0xFF40A0), ('A040FF', 0xFF40A0), ('#fff', 0xFFFFFF), ('#000000', 0), ('#GG0000', -1), ('#12345', -1), ('', -1), ('#', -1),
             ('#1234567', -1), ('red', -1), ('#-10000', -1), ('#12 456', -1)]
    bad = [(t, J(sims[0], 'kfo_hex_col("%s", -1)' % t), w) for t, w in tests if J(sims[0], 'kfo_hex_col("%s", -1)' % t) != w]
    ok(not bad, 'colors: color codes - %d checked, the valid ones read right, every bad one refused (%s)' % (len(tests), bad))
    # the rematch keeps every colour: a match (bots fill in), its end, back to the room
    A = sims[0]
    for s in sims[1:]:
        s.run('kfo_up({ k: "ready", on: 1 });')
    pump(sims, lambda: all(p['rd'] == 1 for p in J(A, 'kfo_lobby_players()')[1:]), 5)
    eq(J(A, 'kfo_host_start()'), '', 'colors: the host starts a match')
    pump(sims, lambda: all(J(s, 'is_struct(global.kfo.M) && global.kfo.M.launched') for s in sims), 8)
    stc = {p['n']: p.get('cl') for p in J(sims[4], 'global.kfo.M.players')}
    ok(all(stc.get(n) == want[n] for n in names if n != 'Ralsei') and stc.get('Ralsei') == keep, 'colors: the match\'s START carries every color (%s)' % stc)
    for s in sims[1:]:
        s.run('kfo_act("kfo_quit");')
    pump(sims, lambda: J(A, 'is_struct(global.kfo.M) && global.kfo.M.ended'), 8)
    for s in sims:
        s.run('kfo_act("kfo_lobby");')
    pump(sims, None, 0.5)
    want['Ralsei'] = keep
    pump(sims, lambda: all(cols_of(s) == want for s in sims), 5)
    right = sum(1 for s in sims for n, c in cols_of(s).items() if want.get(n) == c)
    ok(right == 64, 'colors: after the match (rematch) every room list still has every color right (%d / 64)' % right)
    leave_all(sims)


# ---------- watching from the room ----------
def part_watch(port):
    A, B, C, D = room(port, [('Kris', 1, PRESETS[0]), ('Susie', 2, PRESETS[3]), ('Ralsei', 3, PRESETS[5]), ('Noelle', 4, PRESETS[7])])
    ALL = [A, B, C, D]
    A.run('var _s = kfo_set_clean(global.kfo.H.set); _s.spec = 1; _s.sps = 2; kfo_host_set(_s);')
    B.run('kfo_up({ k: "ready", on: 1 });')
    pump(ALL, lambda: J(A, 'kfo_lobby_players()')[1]['rd'] == 1, 5)
    eq(J(A, 'kfo_host_start()'), '', 'watch: the host starts (Kris and Susie play; Ralsei and Noelle stay in the room)')
    pump(ALL, lambda: J(B, 'is_struct(global.kfo.M) && global.kfo.M.launched'), 8)
    pump(ALL, lambda: J(C, 'kfo_lobby_matching()') and J(D, 'kfo_lobby_matching()'), 5)
    ok(J(C, 'array_get_index(kfo_ui_lobby_rows(), "spectate") >= 0') and J(C, 'kfo_ui_lobby_why("spectate")') == '',
       'watch: Ralsei\'s room page offers SPECTATE MATCH (%s)' % J(C, 'kfo_ui_lobby_why("spectate")'))
    tl0 = tl_sigs(A, 30)
    # SPEC-001: 100 joins from the room's page (and back each time)
    good = 0
    t0 = time.time()
    for c in range(100):
        W = C if c % 2 == 0 else D
        if J(W, 'kfo_ui_lobby_why("spectate")') != '':
            continue
        W.run('kfo_up({ k: "watch" });')
        j = pump(ALL, lambda: J(W, 'is_struct(global.kfo.M) && global.kfo.M.launched && global.kfo.M.spec && !global.kfo.M.me') and J(A, 'kfo_host_watchers()') == 1, 5)
        same = j and tl_sigs(W, 30) == tl0
        cnt = j and pump(ALL, lambda: J(B, 'kfo_lobby_set().spec') == 1 and J(D if W is C else C, 'is_struct(global.kfo.lobby) ? kfo_jn(global.kfo.lobby, "sc", -1) : -1') == 1, 3)
        W.run('kfo_back_to_lobby();')
        off = pump(ALL, lambda: J(A, 'kfo_host_watchers()') == 0 and J(W, 'global.knight_run') == 0, 5)
        if j and same and cnt and off:
            good += 1
        elif c - good < 3:
            print('  join %d: joined %s, same timeline %s, counted %s, back %s' % (c, j, same, cnt, off), flush=True)
    ok(good == 100, 'SPEC-001: 100 SPECTATE MATCH from the room page - the watching START, the match\'s own timeline, counted in every game\'s room list, back to the room and counted off: %d / 100 (%.0fs)'
       % (good, time.time() - t0))
    STATS['SPEC-001'] = {'joins': 100, 'right': good}
    # QOL-004: the counts while one watches
    C.run('kfo_up({ k: "watch" });')
    pump(ALL, lambda: J(A, 'kfo_host_watchers()') == 1, 5)
    pump(ALL, lambda: all(J(s, 'is_struct(global.kfo.lobby) ? kfo_jn(global.kfo.lobby, "sc", -1) : -1') == 1 for s in (B, D)), 3)
    pump(ALL, lambda: '1 WATCHING' in J(D, 'kfo_ui_match_line()'), 5)
    ln = J(D, 'kfo_ui_match_line()')
    ok('1 WATCHING' in ln and '2' in ln, 'QOL-004: the room page of the one not in it says who plays and that 1 watches ("%s")' % ln)
    # zero damage / skills / knight changes from a watcher: what the game itself would send and forged messages
    feed0 = len(J(A, 'global.kfo.H.feed'))
    alive0 = J(A, 'kfo_host_alive()')
    C.run('var _M = global.kfo.M; kfo_up({ k: "sk", mid: _M.mid, sid: 1, seq: 99 }); kfo_up({ k: "sk", mid: _M.mid, sid: 3, seq: 100 });'
          'kfo_up({ k: "out", mid: _M.mid, t: 50, ck: 0, hits: 3 }); kfo_up_fast({ k: "p", mid: _M.mid, x: 300, y: 200, c: 0, h: 0 });'
          'kfo_up({ k: "rdy", mid: _M.mid }); kfo_up({ k: "s", mid: _M.mid, hp: 1, mh: 300, g: 0, sk: 0 });')
    pump(ALL, None, 0.6)
    psC = J(B, 'is_struct(global.kfo.M) ? variable_struct_exists(global.kfo.M.ps, string(%d)) : false' % J(C, 'global.kfo.my'))
    ok(len(J(A, 'global.kfo.H.feed')) == feed0 and J(A, 'kfo_host_alive()') == alive0 and not psC and tl_sigs(A, 30) == tl0 and tl_sigs(B, 30) == tl0,
       'watch: a watcher\'s skill / OUT / position / status messages change nothing (feed %d -> %d, standing %d -> %d, its SOUL relayed: %s, the timeline the same)'
       % (feed0, len(J(A, 'global.kfo.H.feed')), alive0, J(A, 'kfo_host_alive()'), psC))
    # SPEC-008: the match ends (Susie gives up): the watcher has the results the players have
    B.run('kfo_act("kfo_quit");')
    pump(ALL, lambda: J(A, 'is_struct(global.kfo.M) && global.kfo.M.ended') and J(C, 'is_struct(global.kfo.M) && global.kfo.M.ended'), 8)
    ra = J(A, 'global.kfo.M.res')
    rc = J(C, 'global.kfo.M.res')
    ok(ra is not None and rc is not None and ra.get('wn') == rc.get('wn') == 'Kris' and [(p['n'], p['pl']) for p in ra['pl']] == [(p['n'], p['pl']) for p in rc['pl']],
       'SPEC-008: the watcher gets the match\'s results (winner %s, places %s)' % (rc and rc.get('wn'), rc and [(p['n'], p['pl']) for p in rc['pl']]))
    # QOL-003: everyone back in the room; READY is the rematch vote; the next match starts clean
    for s in (A, C):
        s.run('kfo_act("kfo_lobby");')
    pump(ALL, lambda: J(A, 'kfo_host_watchers()') == 0 and all(not J(s, 'kfo_lobby_matching()') for s in ALL), 5)
    ok(J(A, 'kfo_host_watchers()') == 0 and all(J(s, 'global.knight_run') == 0 for s in ALL), 'QOL-003: after the match nobody counts as watching, every game back in the room')
    ok(J(B, 'kfo_ui_after_match()') and J(B, 'kfo_ui_lobby_rows()')[0] == 'ready', 'QOL-003: READY is the REMATCH vote now')
    for s in (B, C, D):
        s.run('kfo_up({ k: "ready", on: 1 });')
    pump(ALL, lambda: 'REMATCH: 3 OF 3' in J(A, 'kfo_ui_lobby_status()'), 5)
    ok('REMATCH: 3 OF 3' in J(A, 'kfo_ui_lobby_status()'), 'QOL-003: the votes counted ("%s")' % J(A, 'kfo_ui_lobby_status()'))
    eq(J(A, 'kfo_host_start()'), '', 'QOL-003: the rematch starts')
    pump(ALL, lambda: all(J(s, 'is_struct(global.kfo.M) && global.kfo.M.launched && global.kfo.M.mid == 1') for s in ALL), 8)
    M = [J(s, '[global.kfo.M.out, global.kfo.M.spec, global.kfo.M.me, array_length(global.kfo.M.vw.fx), global.kfo.M.vw.qs, global.kfo.M.spect]') for s in ALL]
    ok(all(m[0] is False and not m[1] and m[2] and m[3] == 0 and not m[4] for m in M), 'QOL-003: the rematch starts clean in every game (out, watching, effects, quick settings: %s)' % M)
    leave_all(ALL)
    # SPEC-009: the host leaves during a match while someone watches. A fresh room (the room's own clock: the games here run
    # no battle, so a match lives only until the host's status timeout): all four play, Ralsei gives up and watches the rest
    # from the room's page, then the host's game goes away
    A, B, C, D = room(port, [('Kris', 1, PRESETS[0]), ('Susie', 2, PRESETS[3]), ('Ralsei', 3, PRESETS[5]), ('Noelle', 4, PRESETS[7])])
    ALL = [A, B, C, D]
    A.run('var _s = kfo_set_clean(global.kfo.H.set); _s.spec = 1; _s.sps = 2; kfo_host_set(_s);')
    for s in (B, C, D):
        s.run('kfo_up({ k: "ready", on: 1 });')
    pump(ALL, lambda: all(p['rd'] == 1 for p in J(A, 'kfo_lobby_players()')[1:]), 5)
    eq(J(A, 'kfo_host_start()'), '', 'SPEC-009: the match starts (4 players)')
    pump(ALL, lambda: all(J(s, 'is_struct(global.kfo.M) && global.kfo.M.launched') for s in ALL), 8)
    C.run('kfo_act("kfo_quit");')
    pump(ALL, lambda: J(A, 'kfo_host_alive()') == 3 and J(C, 'global.knight_run') == 0 and J(C, 'kfo_ui_lobby_why("spectate")') == '', 5)
    ok(J(C, 'kfo_ui_lobby_why("spectate")') == '', 'SPEC-009: out of the match, Ralsei\'s room page lets them SPECTATE at once ("%s")' % J(C, 'kfo_ui_lobby_why("spectate")'))
    C.run('kfo_up({ k: "watch" });')
    pump(ALL, lambda: J(C, 'is_struct(global.kfo.M) && global.kfo.M.launched && global.kfo.M.spec') and J(A, 'kfo_host_watchers()') == 1, 5)
    if not (J(C, 'global.kfo.M.spec') and J(A, 'kfo_host_watchers()') == 1):
        cp = J(A, 'kfo_host_player(%d)' % J(C, 'global.kfo.my'))
        print('  SPEC-009 debug: C why=%r, C M=%s, host rec %s, host st %s' % (J(C, 'kfo_ui_lobby_why("spectate")'), J(C, '[global.knight_run, global.kfo.M.mid, global.kfo.M.spec, global.kfo.M.me, global.kfo.M.out, global.kfo.M.ended, global.kfo.M.launched]'),
              {k: cp.get(k) for k in ('sp', 'inm', 'al', 'pl')} if cp else None, J(A, '[global.kfo.H.st, global.kfo.H.mid, global.kfo.H.eff.spec]')), flush=True)
    ok(J(C, 'global.kfo.M.spec') and J(A, 'kfo_host_watchers()') == 1, 'SPEC-009: Ralsei watches the match')
    lst0 = J(C, 'global.kfo.M.vw.lst_t')
    A.run('kfo_leave();')
    rec = pump([B, C, D], lambda: J(B, 'kfo_is_host()') and all(J(s, 'global.kfo.hostid') == J(B, 'global.kfo.my') for s in (C, D)), 8)
    ok(rec, 'SPEC-009: the host leaves during the match - the next player hosts the room (Susie), everyone knows')
    pump([B, C, D], lambda: J(C, 'global.kfo.M.vw.lst_t') > lst0, 3)
    errs = [J(s, 'global.kfo.err') for s in (B, C, D)]
    stc = J(C, 'global.kfo.st')
    nh = J(C, 'global.kfo.newhost_n')
    lst1 = J(C, 'global.kfo.M.vw.lst_t')
    ok(all(e == '' for e in errs) and stc == 'room' and J(C, 'global.kfo.M.spec') and not J(C, 'global.kfo.M.me'),
       'SPEC-009: the watcher stays a watcher, in the room, no error (state %s, errors %s)' % (stc, errs))
    ok(lst1 > lst0, 'SPEC-009: the new host\'s standings reach the watcher (last at %s -> %s)' % (lst0, lst1))
    ok(nh == 'Susie' and 'NEW HOST' in J(C, 'kbr_net_state(global.kfo.M).warn'), 'SPEC-009: the watcher is told who hosts now ("%s", "%s")' % (nh, J(C, 'kbr_net_state(global.kfo.M).warn')))
    ok(J(B, 'kfo_host_watchers()') == 1, 'SPEC-009: the new host counts the watcher (%d)' % J(B, 'kfo_host_watchers()'))
    C.run('kfo_back_to_lobby();')
    pump([B, C, D], lambda: J(B, 'kfo_host_watchers()') == 0 and J(C, 'global.knight_run') == 0, 5)
    ok(J(B, 'kfo_host_watchers()') == 0 and J(C, 'global.knight_run') == 0, 'SPEC-009: and goes back to the room cleanly, counted off by the new host')
    leave_all([B, C, D])


# ---------- persistence ----------
def part_persist(port):
    s = mk(port, 'Kris', 1)
    rnd = random.Random(1000)
    vspec = J(s, 'kfo_view_spec()')
    lspec = J(s, 'kfo_look_spec()')
    vdef = J(s, 'kfo_view_default()')
    good = 0
    for c in range(100):
        # random values in each setting's own range and step (the settings' own table: [name, min, max, step])
        v = {k: lo + st * rnd.randint(0, (hi - lo) // st) for k, lo, hi, st in vspec}
        # build 49: OTHER SOUL OPACITY never comes back below 15% (kfo_sop_min): a lower saved value is raised
        v['sop'] = max(15, v['sop'])
        l = {k: lo + st * rnd.randint(0, (hi - lo) // st) for k, lo, hi, st in lspec}
        l['col'] = rnd.randrange(0, 0x1000000)
        s.run('global.kfo.view = json_parse(%s); global.kfo.look = json_parse(%s); kfo_ini_save();' % (json.dumps(json.dumps(v)), json.dumps(json.dumps(l))))
        # a restarted game: nothing in memory, everything from the ini
        s.run('global.kfo = undefined; kfo_get();')
        rv = J(s, 'global.kfo.view')
        rl = J(s, 'global.kfo.look')
        # build 48: the settings taken out of SOUL SETTINGS are always their defaults (kfo_view_clean); the rest must come back
        FIXED = {'nop', 'outl', 'cmode', 'dim', 'skfx', 'dmgfx', 'nums', 'fade', 'mark'}
        if all(rv.get(k) == v[k] for k in v if k not in FIXED) and all(rv.get(k) == vdef[k] for k in FIXED if k in vdef) and all(rl.get(k) == l[k] for k in l):
            good += 1
        elif c - good < 3:
            print('  persist %d: view diff %s, look diff %s' % (c, {k: (v[k], rv.get(k)) for k in v if rv.get(k) != v[k]}, {k: (l[k], rl.get(k)) for k in l if rl.get(k) != l[k]}), flush=True)
    ok(good == 100, 'QOL-002: 100 save / reload of every SOUL VISIBILITY / SOUL APPEARANCE / VIEW setting with random values - all restored %d / 100' % good)
    STATS['QOL-002'] = {'cycles': 100, 'restored': good, 'settings': len(vspec) + len(lspec) + 1}


PARTS = {'colors': part_colors, 'watch': part_watch, 'persist': part_persist}

if __name__ == '__main__':
    t0 = time.time()
    want = sys.argv[1:] or list(PARTS)
    relay, port = start_relay()
    try:
        for k in want:
            print('== part', k, flush=True)
            try:
                PARTS[k](port)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    finally:
        relay.kill()
        relay.wait()
    print('STATS', json.dumps(STATS))
    print('t_room47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:40]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
