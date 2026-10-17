"""Build 45 (P2): the room life cycle again and again, over the RELAY (real sockets, relay.js) or over STEAM as far as it can
be tested here (the real kf_steam code + a PRETEND Steam: not a test of real Steam):
  - 100 times: a room made, two players join with the code, everyone sees everyone, everyone leaves (the room is gone after);
  - 50 matches in one room (rematches): the host changes the settings first (everyone has the very same settings after every
    change), starts, everyone has the same match and timeline, two players fall, everyone agrees on the winner and places,
    back to the room;
  - 20 times the host's game goes away (it leaves / drops off Steam): one other player takes the room over, the rest follow,
    the old host comes back in as a player.
Usage: python3 t_net_repeat45.py relay|steam [rooms (100)] [matches (50)] [hostdrops (20)]"""
import sys, os, json, time, random, socket, subprocess, shutil, ctypes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_net_common import *

MODE = sys.argv[1] if len(sys.argv) > 1 else 'relay'
NROOM = int(sys.argv[2]) if len(sys.argv) > 2 else 100
NMATCH = int(sys.argv[3]) if len(sys.argv) > 3 else 50
NDROP = int(sys.argv[4]) if len(sys.argv) > 4 else 20
R = random.Random(45)
T0 = time.time()
procs = []
STATS = {}

if MODE == 'relay':
    RELAY = '/home/claude/work/online/server/relay.js'
    NODE = '/opt/node22/bin/node'
    s0 = socket.socket()
    s0.bind(('127.0.0.1', 0))
    PORT = s0.getsockname()[1]
    s0.close()
    rp = subprocess.Popen([NODE, RELAY, '--port', str(PORT), '--host', '127.0.0.1', '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    procs.append(rp)
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', PORT), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)

    def mk(name, skin, idx):
        s = game(name, skin)
        s.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % PORT)
        return s

    def create(s):
        s.run('kfo_create();')

    def join(s, code):
        s.run('kfo_join("%s");' % code)

    def drop(s):
        s.run('kfo_leave();')

    CODELEN = 5
else:
    SB = '/home/claude/work/online/steam/build'
    MOCKBE = '/home/claude/work/online/steam/mock/mock_steam_backend.py'
    TMP = '/tmp/claude-0/kfsteam_rep'
    os.makedirs(TMP, exist_ok=True)
    SOCK = TMP + '/s.sock'
    if os.path.exists(SOCK):
        os.remove(SOCK)
    be = subprocess.Popen([sys.executable, MOCKBE, SOCK], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    procs.append(be)
    be.stdout.readline()
    TY = {0: ctypes.c_double, 1: ctypes.c_char_p}

    def ctl(cmd):
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.connect(SOCK)
        c.sendall((cmd + '\n').encode())
        r = c.makefile().readline().strip()
        c.close()
        return r

    def mk(name, skin, idx):
        kf = '%s/kf_%d.so' % (TMP, idx)
        ms = '%s/ms_%d.so' % (TMP, idx)
        shutil.copy(SB + '/libkf_steam.so', kf)
        shutil.copy(SB + '/libmock_steam_api.so', ms)
        lib = ctypes.CDLL(kf)
        env = {'KF_STEAM_API': ms, 'KF_MOCK_SOCK': SOCK, 'KF_MOCK_ACCT': str(3000 + idx), 'KF_MOCK_NAME': name}
        sim = game(name, skin)
        table = {}

        def ext_define(s, path, fname, calltype, restype, argc, *types):
            f = getattr(lib, str(fname))
            f.restype = TY[int(restype)]
            f.argtypes = [TY[int(t)] for t in types]
            table[len(table) + 1] = (f, str(fname))
            return len(table)

        def ext_call(s, fid, *args):
            f, nm = table[int(fid)]
            if nm == 'kf_init':
                os.environ.update(env)
            a = [x.encode() if isinstance(x, str) else float(x) for x in args]
            r = f(*a)
            return r.decode() if isinstance(r, bytes) else float(r)
        sim.mock('external_define', ext_define)
        sim.mock('external_call', ext_call)
        orig = sim.builtins.get('file_exists')
        sim.mock('file_exists', lambda s, p: True if 'kf_steam' in str(p) else (orig[0](s, p) if orig else False))
        for c, v in (('dll_cdecl', 0), ('dll_stdcall', 1), ('ty_real', 0), ('ty_string', 1)):
            sim.mock_value(c, v)
        sim.run('global.kfo.vis = 1;')
        sim.acct = 3000 + idx
        sim.lib = lib
        ok(J(sim, 'kfo_steam_ready()'), '%s: pretend Steam ready' % name)
        return sim

    def create(s):
        s.run('kfo_steam_host();')

    def join(s, code):
        s.run('kfo_steam_join_code("%s");' % code)

    def drop(s):
        ctl('ctl_drop\t%d' % s.acct)

    CODELEN = 7

try:
    A, B, C, D = mk('Kris', 1, 1), mk('Susie', 2, 2), mk('Ralsei', 3, 3), mk('Noelle', 4, 4)
    G = [A, B, C, D]
    NM = {id(A): 'Kris', id(B): 'Susie', id(C): 'Ralsei', id(D): 'Noelle'}

    # ---------------------------------------------------------------- 100 rooms
    good = 0
    fails = []
    for i in range(NROOM):
        h, p1, p2 = G[i % 3], G[(i + 1) % 3], G[(i + 2) % 3]
        create(h)
        pump([h], lambda: J(h, 'global.kfo.st') == 'room', 8)
        code = J(h, 'global.kfo.code')
        if J(h, 'global.kfo.st') != 'room' or len(code) != CODELEN:
            fails.append((i, 'create', J(h, 'global.kfo.err')))
            continue
        join(p1, code)
        join(p2, code)
        three = lambda: all(J(x, 'global.kfo.st') == 'room' and len(J(x, 'kfo_lobby_players()')) == 3 for x in (h, p1, p2))
        pump([h, p1, p2], three, 8)
        if not three():
            fails.append((i, 'join', [J(x, '[global.kfo.st, global.kfo.err]') for x in (p1, p2)]))
        else:
            good += 1
        for x in (p1, p2, h):
            x.run('kfo_leave();')
        pump([h, p1, p2], None, 0.15)
        if MODE == 'steam' and i % 10 == 9:
            left = ctl('ctl_lobbies')
            ok(left == '', 'room %d: every Steam lobby is gone once everyone left (%r)' % (i, left[:80]))
    STATS['rooms'] = {'tried': NROOM, 'ok': good, 'fails': fails[:5]}
    ok(good >= 0.99 * NROOM, '%d rooms made and joined: %d fine (%r)' % (NROOM, good, fails[:3]))
    if MODE == 'relay':
        # the last room is gone: its code no longer works
        D.run('kfo_join("%s");' % code)
        pump([D], lambda: J(D, 'global.kfo.st') in ('failed', 'room'), 5)
        ok(J(D, 'global.kfo.st') == 'failed', 'a room everyone left is gone (%s)' % J(D, 'global.kfo.err'))
        D.run('kfo_close("");')

    # ---------------------------------------------------------------- 50 matches in one room, settings changed before each
    create(A)
    pump([A], lambda: J(A, 'global.kfo.st') == 'room', 8)
    code = J(A, 'global.kfo.code')
    for x in (B, C):
        join(x, code)
    pump([A, B, C], lambda: all(len(J(x, 'kfo_lobby_players()')) == 3 for x in (A, B, C)), 8)
    opts = [o['oid'] for o in J(A, 'kfo_opts()') if o['kind'] in ('num', 'enum', 'bool', 'kw', 'open') and o['oid'] not in ('maxp', 'minp', 'bots', 'ready', 'spec')]
    m_ok = 0
    set_ok = 0
    set_n = 0
    m_fail = []
    for i in range(NMATCH):
        # the host changes 1-3 settings: everyone has exactly the host's settings after each change
        for _ in range(R.randint(1, 3)):
            oid = R.choice(opts)
            A.run('var _r = kfo_opt_change(global.kfo.H.set, "%s", %d); if (is_struct(_r)) kfo_host_set(_r);' % (oid, R.choice([-1, 1])))
            want = J(A, 'global.kfo.H.set')
            pump([A, B, C], lambda: all(J(x, 'kfo_lobby_set()') == want for x in (B, C)), 4)
            set_n += 1
            if all(J(x, 'kfo_lobby_set()') == want for x in (B, C)):
                set_ok += 1
        for x in (B, C):
            x.run('kfo_up({ k: "ready", on: 1 });')
        pump([A, B, C], lambda: all(p['rd'] == 1 for p in J(A, 'kfo_lobby_players()')[1:]), 4)
        why = J(A, 'kfo_host_start()')
        if why != '':
            m_fail.append((i, 'start', why))
            continue
        pump([A, B, C], lambda: all(J(x, 'is_struct(global.kfo.M) && global.kfo.M.launched && global.kfo.M.mid == %d' % (i + 1)) for x in (A, B, C)), 6)
        sig = [tl_sigs(x, 8) for x in (A, B, C)]
        mids = [J(x, 'is_struct(global.kfo.M) ? global.kfo.M.mid : -1') for x in (A, B, C)]
        if not (sig[0] == sig[1] == sig[2]) or len(set(mids)) != 1:
            m_fail.append((i, 'timeline', mids))
        # two fall: the third wins (who falls changes each match)
        order = [B, C] if i % 2 == 0 else [C, B]
        if i % 3 == 2:
            order = [A, B]
        t = 400
        for x in order:
            x.run('kfo_up({ k: "out", mid: global.kfo.M.mid, t: %d, ck: 2, hits: 3 }); global.kfo.M.out = true;' % t)
            t += 200
            pump([A, B, C], None, 0.6)
        winner = [x for x in (A, B, C) if x not in order][0]
        pump([A, B, C], lambda: all(J(x, 'is_struct(global.kfo.M) && global.kfo.M.ended') for x in (A, B, C)), 6)
        res = [J(x, 'is_struct(global.kfo.M) && is_struct(global.kfo.M.res) ? [global.kfo.M.res.wn, global.kfo.M.res.pl] : undefined') for x in (A, B, C)]
        wn = NM[id(winner)]
        if any(r is None for r in res) or any(r[0] != wn for r in res) or not (res[0][1] == res[1][1] == res[2][1]):
            m_fail.append((i, 'result', wn, [r[0] if r else None for r in res]))
        else:
            m_ok += 1
        for x in (A, B, C):
            x.run('kfo_act("kfo_lobby");')
        pump([A, B, C], lambda: all(J(x, '[global.knight_run, kfo_in_room()]') == [0, True] for x in (A, B, C)), 4)
        if not all(J(x, '[global.knight_run, kfo_in_room()]') == [0, True] for x in (A, B, C)):
            m_fail.append((i, 'back to room', [J(x, '[global.knight_run, kfo_in_room(), global.kfo.st]') for x in (A, B, C)]))
            break
    STATS['matches'] = {'tried': NMATCH, 'ok': m_ok, 'fails': m_fail[:5], 'settings_changes': set_n, 'settings_same': set_ok}
    ok(m_ok >= NMATCH and not m_fail, '%d matches in a row (rematches): same match and timeline, the same winner and places everywhere (%d ok, %r)' % (NMATCH, m_ok, m_fail[:3]))
    ok(set_ok == set_n, '%d settings changes by the host: everyone had exactly the host\'s settings after each (%d)' % (set_n, set_ok))

    # ---------------------------------------------------------------- 20 times the host goes away
    d_ok = 0
    d_fail = []
    members = [A, B, C]
    for i in range(NDROP):
        host = [x for x in members if J(x, 'kfo_is_host()')]
        if len(host) != 1:
            d_fail.append((i, 'hosts', len(host)))
            break
        host = host[0]
        others = [x for x in members if x is not host]
        drop(host)
        if MODE == 'relay':
            pass
        pump(others + [host], lambda: sum(1 for x in others if J(x, 'kfo_is_host()')) == 1 and all(len(J(x, 'kfo_lobby_players()')) == 2 for x in others), 10)
        nh = [x for x in others if J(x, 'kfo_is_host()')]
        if len(nh) != 1:
            d_fail.append((i, 'no new host', [J(x, '[global.kfo.st, global.kfo.hostid, global.kfo.my, global.kfo.err]') for x in others]))
            break
        nh = nh[0]
        fol = [x for x in others if x is not nh][0]
        if J(fol, 'global.kfo.hostid') != J(nh, 'global.kfo.my') or len(J(fol, 'kfo_lobby_players()')) != 2:
            d_fail.append((i, 'follower', J(fol, '[global.kfo.hostid, global.kfo.st]')))
            break
        d_ok += 1
        # the old host comes back as a player (a Steam game that dropped starts Steam again)
        code = J(nh, 'global.kfo.code')
        if MODE == 'steam':
            ctl('ctl_online\t%d' % host.acct)
        host.run('kfo_close("");')
        join(host, code)
        pump(members, lambda: all(len(J(x, 'kfo_lobby_players()')) == 3 for x in members), 10)
        if not all(len(J(x, 'kfo_lobby_players()')) == 3 for x in members):
            d_fail.append((i, 'rejoin', [J(x, '[global.kfo.st, global.kfo.err]') for x in members]))
            break
    STATS['hostdrops'] = {'tried': NDROP, 'ok': d_ok, 'fails': d_fail[:3]}
    ok(d_ok == NDROP, '%d host drops: a new host every time, the rest follow, the old host back in (%d ok, %r)' % (NDROP, d_ok, d_fail[:2]))
finally:
    for p in procs:
        p.kill()
STATS['secs'] = round(time.time() - T0, 1)
json.dump({'mode': MODE, 'checks': N[0], 'fails': FAILS, 'stats': STATS}, open('/tmp/claude-0/br45/repeat_%s.json' % MODE, 'w'), indent=1)
print('net repeat (%s): %d checks, %d failed  %s' % (MODE, N[0], len(FAILS), json.dumps(STATS)[:600]))
for f in FAILS[:8]:
    print('  -', f)
sys.exit(1 if FAILS else 0)
