"""Build 45: the room / match messages over a real transport, shared by t_online_net.py (the relay, real sockets) and
t_steam_gml.py (kf_steam + a pretend Steam). The games are emulators running the real online code (no battle stepping: the
battle royale itself has its own tests); this checks rooms, codes, lobby lists, settings, the start, the shared timeline,
outs, places, results, the next match, the host leaving, full rooms."""
import time
from harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        print('FAIL', msg, flush=True)


def eq(a, b, msg):
    N[0] += 1
    if a != b:
        FAILS.append(msg)
        print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)


def J(sim, e):
    return sim.py(sim.eval(e))


def frame(sim):
    sim.frame_no += 1
    for h in getattr(sim, 'async_hooks', []):
        h(sim)
    sim.run('kfo_tick();')


def pump(sims, cond=None, secs=3.0, min_frames=0):
    t0 = time.time()
    n = 0
    while True:
        for s in sims:
            frame(s)
        n += 1
        if cond is not None and n >= min_frames and cond():
            return True
        if time.time() - t0 > secs:
            return cond is None
        time.sleep(0.002)


def game(name, skin):
    sim = make_sim()
    sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
    sim.run('kfo_get(); global.kfo.name = "%s"; global.kfo.skin = %d;' % (name, skin))
    sim.nm = name
    return sim


def tl_sigs(sim, n=40):
    sim.run('global.TS = []; for (var _k = 0; _k < %d; _k++) array_push(global.TS, kbr_tl_sig(kbr_tl_get(global.kfo.M.tl, _k)));' % n)
    return J(sim, 'global.TS')


def scenario(A, B, C, create, join, code_len, host_change_check=True):
    """A hosts, B and C join with the code; settings, the start, the timeline, outs and results, the next match, the host
    leaving. create(sim) / join(sim, code) start the transport's own create / join."""
    ALL = [A, B, C]
    create(A)
    ok(pump([A], lambda: J(A, 'global.kfo.st') == 'room', 5), 'A made a room')
    code = J(A, 'global.kfo.code')
    ok(len(code) == code_len and code.isalpha() and code.isupper(), 'room code %s (%d letters)' % (code, code_len))
    ok(A.eval('kfo_is_host()'), 'A hosts')
    join(B, code.lower())
    pump(ALL, lambda: J(B, 'global.kfo.st') == 'room', 5)
    eq(J(B, 'global.kfo.st'), 'room', 'B joined by code (typed in lower case)')
    join(C, code)
    pump(ALL, lambda: J(C, 'global.kfo.st') == 'room' and all(len(J(x, 'kfo_lobby_players()')) == 3 for x in ALL), 5)
    for s in ALL:
        eq([p['n'] for p in J(s, 'kfo_lobby_players()')], ['Kris', 'Susie', 'Ralsei'], '%s sees the three players' % s.nm)
    eq(J(B, 'global.kfo.lastcode'), code, 'last code remembered')
    # ---- settings: a preset and a change; everyone ends up with the very same settings
    A.run('var _s = kfo_preset_apply(4); _s.mhp = 180; _s.m_storm = 1; _s.kn = [0, 2, 4, 5]; _s.open = 2; kfo_host_set(_s);')
    pump(ALL, lambda: J(C, 'kfo_lobby_set().mhp') == 180, 3)
    sa = J(A, 'global.kfo.H.set')
    for s in (B, C):
        eq(J(s, 'kfo_lobby_set()'), sa, '%s has exactly the host\'s settings' % s.nm)
    eq(J(C, 'kfo_lobby_set().pre'), 'CUSTOM', 'a changed preset is CUSTOM')
    # ---- ready, start
    B.run('kfo_up({ k: "ready", on: 1 });')
    C.run('kfo_up({ k: "ready", on: 1 });')
    pump(ALL, lambda: all(p['rd'] == 1 for p in J(A, 'kfo_lobby_players()')[1:]), 3)
    eq(J(A, 'kfo_host_start()'), '', 'host starts')
    pump(ALL, lambda: all(J(s, 'is_struct(global.kfo.M) && global.kfo.M.launched') for s in ALL), 5)
    for s in ALL:
        ok(J(s, 'knight_active() && kfo_run_on()'), '%s: online fight launched' % s.nm)
        eq(J(s, 'global.kfo.M.set.open'), 2, '%s: opening knight from the settings' % s.nm)
    eq(len(set(J(s, 'global.kfo.M.seed') for s in ALL)), 1, 'everyone has the same seed')
    sig = [tl_sigs(s) for s in ALL]
    ok(sig[0] == sig[1] == sig[2], 'everyone works out the same first 40 cycles (%s ...)' % sig[0][:2])
    ok(all(int(x.split(':')[1]) in (0, 2, 4, 5) for x in sig[0]), 'only the room\'s knights come')
    eq(J(B, 'global.krun.cfg.party'), [2, 0, 0], 'B fights as Susie')
    # ---- outs: C falls at tick 500, B gives up: A wins (the outs reach the host over the transport)
    C.run('kfo_up({ k: "out", mid: global.kfo.M.mid, t: 500, ck: 3, hits: 7 }); global.kfo.M.out = true;')
    pump(ALL, lambda: J(A, 'kfo_host_alive()') == 2, 3)
    ok(any('Ralsei is OUT (#3)' in f[1] for f in J(A, 'global.kfo.H.feed')), 'C out #3, and the feed says so')
    pump(ALL, lambda: any(p['n'] == 'Ralsei' and p['pl'] == 3 for p in J(C, 'global.kfo.M.st.pl')), 3)
    eq(J(C, 'global.kfo.M.place'), 3, 'C knows its place')
    B.run('kfo_act("kfo_quit");')
    pump(ALL, lambda: all(J(s, 'is_struct(global.kfo.M) && global.kfo.M.ended') for s in (A, C)), 5)
    for s in (A, C):
        eq(J(s, 'global.kfo.M.res.wn'), 'Kris', '%s: Kris won' % s.nm)
    eq([(p['n'], p['pl']) for p in J(A, 'global.kfo.M.res.pl')], [('Kris', 1), ('Susie', 2), ('Ralsei', 3)], 'final places')
    eq(J(A, 'kfo_result_title()'), 'YOU WIN!', 'winner title')
    eq(J(B, 'global.knight_run'), 0, 'B (gave up) is back in the cold place')
    for s in (A, C):
        s.run('kfo_act("kfo_lobby");')
    pump(ALL, None, 0.3)
    for s in ALL:
        eq(J(s, '[global.knight_run, kfo_in_room(), kfo_lobby_matching()]'), [0, True, False], '%s back in the room, lobby open' % s.nm)
    # ---- the host leaves: B takes the room over, C stays
    A.run('kfo_leave();')
    pump(ALL, lambda: J(B, 'kfo_is_host()') and len(J(C, 'kfo_lobby_players()')) == 2, 5)
    ok(B.eval('kfo_is_host()'), 'B hosts after A left')
    eq([p['n'] for p in J(C, 'kfo_lobby_players()')], ['Susie', 'Ralsei'], 'C sees the room without A')
    eq(J(C, 'global.kfo.hostid'), J(B, 'global.kfo.my'), 'C knows the new host')
    eq(J(A, 'global.kfo.st'), 'idle', 'A is out of the room')
    # second match: B hosts, C ready; C falls -> B wins
    C.run('kfo_up({ k: "ready", on: 1 });')
    pump(ALL, lambda: len(J(B, 'kfo_lobby_players()')) > 1 and J(B, 'kfo_lobby_players()')[1]['rd'] == 1, 3)
    eq(J(B, 'kfo_host_start()'), '', 'new host starts a match')
    pump(ALL, lambda: J(C, 'is_struct(global.kfo.M) && global.kfo.M.launched && global.kfo.M.mid == 1'), 5)
    eq(J(C, 'global.kfo.M.mid'), 1, 'the new host counts its own matches')
    eq(tl_sigs(B, 20), tl_sigs(C, 20), 'B and C share the new match\'s timeline')
    C.run('kfo_up({ k: "out", mid: global.kfo.M.mid, t: 300, ck: 1, hits: 2 }); global.kfo.M.out = true;')
    pump(ALL, lambda: J(B, 'is_struct(global.kfo.M) && global.kfo.M.ended'), 5)
    eq(J(B, 'kfo_result_title()'), 'YOU WIN!', 'B won the second match')
    for s in (B, C):
        s.run('kfo_act("kfo_lobby");')
    pump(ALL, None, 0.3)
    return code
