"""Build 45 (P2): malformed and hostile messages. Every message the online code can receive goes through the real handlers:
relay lines (kfo_line), the relay's own events, Steam packets (kfo_steam_packet), the player's game (kfo_client_on, in a
running match) and the host (kfo_host_on, from members and from strangers). A corpus of broken JSON, wrong types, missing
fields, huge / negative / fractional numbers, long strings, deep nesting, unknown kinds and known kinds with one field
wrong. Passes when nothing crashes (in GameMaker a runtime error ends the game) and the state stays sane afterwards.
Usage: python3 t_online_fuzz45.py [messages per side (6000)] [seed]"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

NMSG = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 99
R = random.Random(SEED)
FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        print('FAIL', msg, flush=True)


def J(sim, e):
    return sim.py(sim.eval(e))


CLIENT_K = ['lobby', 'start', 'go', 'po', 'ps', 'st', 'ska', 'ft', 'rs', 'fix', 'end', 'ows', 'kick']
HOST_K = ['hi', 'ready', 'skin', 'ow', 'pi', 'rdy', 'watch', 'p', 's', 'sk', 'rf', 'sg', 'out', 'quit']
RELAY_T = ['welcome', 'joined', 'refused', 'member', 'promote', 'up', 'down']
FIELDS = ['mid', 'seed', 'set', 'players', 'h', 'in', 'c', 'x', 'y', 'l', 'pl', 'sid', 'seq', 'from', 'to', 'ck', 'why', 'hp', 'mhp', 'g',
          'wid', 'wn', 'sn', 'dur', 'an', 't', 'fd', 'ft', 'go', 'sig', 'sig2', 'bc', 'sk', 'lat', 'on', 'skin', 'name', 'ver', 'r', 'f', 'm',
          'code', 'host', 'st', 'res', 'prac', 'spec', 'id', 'members', 'ev', 'you', 'max', 'rd', 'inm', 'bot', 'n', 's', 'sd', 'fname', 'rf', 'k']


def junk(depth=0):
    r = R.random()
    if depth > 3 or r < 0.25:
        return R.choice([0, 1, -1, 2, 7, 999999999, -999999999, 1e300, -1e300, 0.5, 3.75, 1e-9, 2147483647, 2 ** 53, True, False, None])
    if r < 0.45:
        return R.choice(['', 'x', 'lobby', 'ABCDEFG', 'KF45:', 'éè中', '"quoted"', 'a' * R.choice([10, 300, 5000]), '-1', '1e9', 'null'])
    if r < 0.7:
        return [junk(depth + 1) for _ in range(R.randint(0, 6))]
    return {R.choice(FIELDS): junk(depth + 1) for _ in range(R.randint(0, 6))}


def msg(kinds):
    m = {'k': R.choice(kinds + ['', 'zz', 5, None]) if R.random() < 0.95 else junk()}
    for _ in range(R.randint(0, 8)):
        m[R.choice(FIELDS)] = junk()
    if R.random() < 0.6:
        m['mid'] = R.choice([0, 1, 1, 1, 2, -1, 'x'])
    return m


def raw_line():
    r = R.random()
    if r < 0.2:
        return R.choice(['', '{', '}', '[]', 'null', '42', '"text"', '{"t":', '{"t":"down","m":', 'NaN', '{"t":"down","m":{"k":"st","pl":[1,2,3' + ']' * 3,
                         '\x00\x01\x02', '{' * 3000 + '}' * 3000, '[' * 40000 + ']' * 40000, '{"t":"down","m":' + '[' * 1600 + ']' * 1600 + '}'])
    m = {'t': R.choice(RELAY_T + ['zz', 3])}
    if m['t'] == 'down':
        m['m'] = msg(CLIENT_K)
    elif m['t'] == 'up':
        m['from'] = R.choice([1, 2, 3, 4, 99, -1, 'x', None])
        m['m'] = msg(HOST_K)
    else:
        for _ in range(R.randint(0, 5)):
            m[R.choice(FIELDS)] = junk()
    t = json.dumps(m)
    if R.random() < 0.1:
        t = t[:R.randint(0, len(t))]
    return t


def client_sim():
    s = make_sim()
    s.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl(); kfo_get(); global.kfo.name = "Susie";')
    s.mock('kfo_launch', lambda sim: 0)
    s.mock('knight_launch_go', lambda sim: 0)
    s.mock('kfo_raw', lambda sim, m: True)
    # in a relay room as player 2, a match running
    s.run('var _o = global.kfo; _o.st = "room"; _o.mode = "direct"; _o.my = 2; _o.hostid = 1; _o.code = "ABCDE";'
          '_o.members = [{ pid: 1, name: "Kris" }, { pid: 2, name: "Susie" }, { pid: 3, name: "Ralsei" }];'
          'kfo_client_on({ k: "lobby", code: "ABCDE", host: 1, st: "match", mid: 1, prac: 0, set: kfo_set_default(), players: [{ pid: 1, n: "Kris", s: 1, rd: 1, inm: 1, bot: 0 },'
          ' { pid: 2, n: "Susie", s: 2, rd: 1, inm: 1, bot: 0 }, { pid: 3, n: "Ralsei", s: 3, rd: 1, inm: 1, bot: 0 }], res: 0 });'
          'kfo_client_on({ k: "start", mid: 1, seed: 4242, set: kfo_set_default(), players: [{ pid: 1, n: "Kris", s: 1 }, { pid: 2, n: "Susie", s: 2 }, { pid: 3, n: "Ralsei", s: 3 }], prac: 0, ver: kfo_version() });'
          'kfo_client_on({ k: "go", mid: 1, in: 100, h: -100 });')
    return s


def host_sim():
    s = make_sim()
    s.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl(); kfo_get(); global.kfo.name = "Kris";')
    s.mock('kfo_launch', lambda sim: 0)
    s.mock('knight_launch_go', lambda sim: 0)
    s.mock('kfo_raw', lambda sim, m: True)
    s.run('var _o = global.kfo; _o.st = "room"; _o.mode = "direct"; _o.my = 1; _o.hostid = 1; _o.code = "ABCDE";'
          '_o.members = [{ pid: 1, name: "Kris" }, { pid: 2, name: "Susie" }, { pid: 3, name: "Ralsei" }];'
          'kfo_host_begin("ABCDE", false); kfo_host_member("join", 2, "Susie"); kfo_host_member("join", 3, "Ralsei");'
          'var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { _h.pl[_i].rd = 1; _h.pl[_i].hi = 1; }'
          'global.kfo_test_seed = 77; global.WHY = kfo_host_start(); kfo_local_run(); _h.go = true; _h.t0ms = current_time - 3000;')
    return s


def sane(s, who):
    st = J(s, 'global.kfo.st')
    ok(st in ('room', 'idle', 'failed', 'joining', 'hello', 'connecting'), '%s: state %r' % (who, st))
    if J(s, 'is_struct(global.kfo.H)'):
        bad = J(s, '(function() { var _b = 0; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _p = _h.pl[_i];'
                   ' if (!is_numeric(_p.pid) || !is_string(_p.n) || !is_numeric(_p.hp) || !is_numeric(_p.mh) || _p.hp > _p.mh || _p.hp < 0 || !is_numeric(_p.g) || _p.g < 0 || _p.g > 100) _b++; } return _b; })()')
        ok(bad == 0, '%s: the host\'s players stay sane (%d bad)' % (who, bad))


t0 = time.time()
crashes = []
# ---------------- the player's game: messages from the host
c = client_sim()
for i in range(NMSG):
    m = msg(CLIENT_K)
    try:
        c.run('kfo_client_on(json_parse(%s));' % json.dumps(json.dumps(m)))
        if i % 50 == 0:
            c.frame_no += 1
            c.run('kfo_tick();')
    except Exception as ex:
        crashes.append(('client', m, str(ex)[:200]))
        c = client_sim()
sane(c, 'client')
# ---------------- the host: messages from members and strangers
h = host_sim()
for i in range(NMSG):
    m = msg(HOST_K)
    frm = R.choice([2, 3, 2, 3, 99, -1, 1])
    try:
        h.run('kfo_host_on(%d, json_parse(%s));' % (frm, json.dumps(json.dumps(m))))
        if i % 50 == 0:
            h.frame_no += 1
            h.run('kfo_tick();')
    except Exception as ex:
        crashes.append(('host', frm, m, str(ex)[:200]))
        h = host_sim()
sane(h, 'host')
# ---------------- raw relay lines (both games)
for i in range(NMSG):
    t = raw_line()
    for nm, s in (('client', c), ('host', h)):
        try:
            s.run('kfo_line(%s);' % json.dumps(t))
        except Exception as ex:
            crashes.append(('line ' + nm, t[:200], str(ex)[:200]))
            if nm == 'client':
                c = client_sim()
            else:
                h = host_sim()
sane(c, 'client after lines')
sane(h, 'host after lines')
# ---------------- Steam packets (the same game, as a Steam room)
for s, nm in ((client_sim(), 'client'), (host_sim(), 'host')):
    s.run('global.kfo.mode = "steam";')
    for i in range(NMSG // 2):
        t = raw_line() if R.random() < 0.5 else json.dumps({'t': R.choice(['up', 'down', 'x']), 'm': msg(CLIENT_K if R.random() < 0.5 else HOST_K)})
        frm = R.choice([1, 2, 3, 99, 0, -5])
        try:
            s.run('kfo_steam_packet(%d, %s);' % (frm, json.dumps(t)))
        except Exception as ex:
            crashes.append(('steam ' + nm, t[:200], str(ex)[:200]))
            break
    sane(s, 'steam ' + nm)
# ---------------- Steam events from the DLL (event text)
s = client_sim()
s.run('global.kfo.mode = "steam"; global.kfo_stm = { ok: true, init: 1, why: "", fns: {}, dll: "" };')
# the DLL's functions answer with their declared types (a number or a text), as external_call does
FN_T = {e[0]: e[1] for e in J(s, 'kfo_steam_fn_list()')}
SXM = lambda sim, name, *a: ('' if FN_T.get(str(name), 0) == 1 else 0.0)
s.mock('kfo_sx', SXM)
for i in range(NMSG // 2):
    ev = R.choice(['joined', 'create_failed:', 'join_failed:', 'found:', 'notfound', 'join_request:', 'member_in:', 'member_out:', 'owner:', 'left', 'browse:', 'p2p_fail:', 'zz:', ''])
    ev += R.choice(['', '1', '-1', 'x', '2001', '|||||', '9|45|8|8|lobby|Kris', '12345678901234567890', 'a' * 300, '0|44|1|8|match|' + 'N' * 50])
    try:
        s.run('kfo_steam_event(%s);' % json.dumps(ev))
    except Exception as ex:
        crashes.append(('steam event', ev[:100], str(ex)[:200]))
        s = client_sim()
        s.run('global.kfo.mode = "steam"; global.kfo_stm = { ok: true, init: 1, why: "", fns: {}, dll: "" };')
        s.mock('kfo_sx', SXM)
ok(not crashes, '%d malformed messages per side, %d raw lines, %d Steam packets / events: no crash (%d: %r)' % (NMSG, NMSG, NMSG, len(crashes), crashes[:3]))
# the deep-nesting guard
s = client_sim()
ok(J(s, 'is_undefined(kfo_json_in(string_repeat("[", 5000) + string_repeat("]", 5000)))'), 'deep nesting is not parsed')
ok(J(s, 'is_struct(kfo_json_in("{\\"k\\":\\"st\\",\\"pl\\":[[1,2],[3,4]]}"))'), 'a normal message is parsed')
print('online fuzz: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS[:10]:
    print('  -', f)
sys.exit(1 if FAILS else 0)
