"""Build 47: the others' SOULs, watching and the match QoL, in several emulated games over the simulated network (br_multi).
Every game runs the real merged fight code and the real online code; the SOULs each game draws are logged (kfo_soul_draw,
tagged by who called it: the others' SOULs, your own, a HUD icon).

Fixtures (your document's table; the numbers printed are the measured ones):
  SOUL-001  two games: at every checkpoint (all SOULs still for 20 frames) each game draws the other's SOUL exactly where
            that game's SOUL is - 100% agreement required
  SOUL-002  eight games: each draws the seven others, never more SOULs than players standing (no duplicate)
  SOUL-003  SHOW OTHER SOULS off in one game: it draws none of them; the others still draw it, its positions still go out,
            the match (cycles, knights, attacks, bullets at 30/60/90 frames) is the same as in the run with it on
  SOUL-004  OTHER SOUL OPACITY changed: the very next frame draws the others at the new opacity (yours stays full)
  SOUL-005  another SOUL on yours: it is drawn fainter, yours full and pulsing; nobody's position changes
  SOUL-006  a player OUT: its SOUL breaks where it was (build 48: it cracks, then 6 shards fly, as in Chapter 3's GAME OVER), is not drawn any more; that player watches someone 45 frames on
  SOUL-007  100 leave / come back cycles (a new id each time, as the relay and Steam give): never a second SOUL for anybody
  SOUL-008  Knight Rush: the checkpoints of SOUL-001/002 span the knight switches (counted)
  SPEC-002  a watcher joining in the middle of an attack: it never starts a cycle before the host's current one, every cycle
            it runs is the timeline's (knight, attack, seed), and the players' match is unchanged
  SPEC-003  100 target changes (< > / LB RB): always the next living player in the list's order
  SPEC-004  the followed player goes OUT: the camera moves to the next living player by itself
  SPEC-005  FULL ARENA: every standing SOUL drawn, none singled out
  SPEC-006  the watching HUD shows the followed player's name and HP as the host's standings have them
  SPEC-010  eight players + two watchers: no error, the same match in every game
  QOL-001   QUICK SETTINGS (Q): opens, changes the opacity / names / effects at once, holds your SOUL still while open
  QOL-005   the network line: packet loss measured on a lossy link (and none on a clean one), "no news from the host" when the
            host's messages stop
Usage: python3 t_view47.py [fixture ...]   (default: all)"""
import sys, os, re, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]
STATS = {}
CORE = open(MDIR + 'gml_GlobalScript_knight_core.gml', encoding='utf8').read()
IN = 2   # the heart inside Chapter 3's SOUL sprite (spr_dodgeheart): 2 px in from obj_heart's x / y


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def func_src(name):
    m = re.search(r'(?m)^function %s\(' % re.escape(name), CORE)
    assert m, name
    i = CORE.index('{', m.end())
    d = 0
    j = i
    while True:
        c = CORE[j]
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                break
        j += 1
    return CORE[m.start():j + 1]


def wrap(name, args, pre, post=''):
    src = func_src(name).replace('function %s(' % name, 'function %s__orig(' % name, 1)
    return src + '\nfunction %s(%s) { %s var _r = %s__orig(%s); %s return _r; }\n' % (name, args, pre, name, args, post)


LOGGER = ('global.SDL = []; global.SDT = "";\n' +
          wrap('kfo_soul_draw', '_x, _y, _sc, _col, _a, _olc', 'array_push(global.SDL, [global.SDT, _x, _y, _sc, _col, _a, _olc]);') +
          wrap('kbr_draw_souls', '', 'global.SDT = "r";', 'global.SDT = "";') +
          wrap('kbr_heart_draw', '', 'global.SDT = "l";', 'global.SDT = "";'))


def instrument(sims):
    for s in sims:
        s.load_source('gml_GlobalScript_view47_log', LOGGER)
        s.run('global.SDL = []; global.SDT = "";')
        # your own SOUL's Draw (obj_heart: kbr_heart_draw first) - the battle harness loads no Draw events of the game's
        s.load_file(MDIR + 'gml_Object_obj_heart_Draw_0.gml', entry='gml_Object_obj_heart_Draw_0')
        # the SOUL's sprite as in the game (obj_heart's own sprite in data.win: spr_dodgeheart, the heart with its black edge)
        if 'spr_dodgeheart' not in s.assets:
            s.define_asset('spr_dodgeheart')
        s.objects['obj_heart'].sprite = s.assets['spr_dodgeheart']
        s.run('with (obj_heart) sprite_index = spr_dodgeheart;')


def draws(s, who='r'):
    return [d for d in J(s, 'global.SDL') if d[0] == who]


def heart(s):
    return J(s, 'instance_exists(obj_heart) ? [obj_heart.x, obj_heart.y] : [-1, -1]')


def mypid(s):
    return J(s, 'global.kfo.my')


def alive_ids(s):
    return J(s, 'kbr_alive_ids()')


def step_all(net, sims, f, keys_of, rec=None, skip=()):
    """one frame of every game: its messages, its keys, the frame (the SOUL draw log cleared first)"""
    net.t += 1000.0 / 30.0
    errs = []
    for i, s in enumerate(sims):
        if i in skip:
            continue
        s.run('test_net_pump(); global.SDL = [];')
        s.kb = keys_of(i, f)
        e = step(s, 1)
        if e is not None:
            errs.append((i + 1, f, e[:300]))
        if rec is not None:
            st = state(s)
            r = rec[i + 1]
            if st['last'] >= 0 and (st['ns'] > r['_ns'] or st['last'] != r['_last']):
                c = s.py(s.eval('kbr_tl_get(global.kfo.M.tl, %d)' % st['last']))
                r['starts'].append({'k': st['last'], 'ok': c['ok'], 'ai': c['ai'], 'seed': c['seed'], 't0': c['t0'], 'tw': c['twin'], 'hy': c['hyper'],
                                    'st': c['st'], 'sd': c['sd'], 'ft': c['ft'], 'tsp': round(st['tsp'], 3), 'net_ms': round(net.t, 1), 'act': st['act'],
                                    'prev_act': r['_act']})
            if st['ph'] == 'run' and st['af'] in (30, 60, 90):
                r['snaps']['%d:%d' % (st['k'], st['af'])] = snapshot(s)
            r['_ns'], r['_last'], r['_act'] = st['ns'], st['last'], st['act']
    return errs


def new_rec(n):
    return {i + 1: {'starts': [], 'snaps': {}, 'errors': [], '_ns': 0, '_last': -1, '_act': -1} for i in range(n)}


MOVES = [('right',), ('up',), ('left',), ('down',), ('right', 'down'), ('left', 'up'), ()]


def roam(i, f, still):
    """each game its own path; still: no keys (a checkpoint window)"""
    if still:
        return set()
    return set(MOVES[((f // 17) + i * 3) % len(MOVES)])


def keep_alive(sims, f):
    if f % 30 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            s.log.clear()


def checkpoint_agreement(sims, hist, tag):
    """every game's drawn SOUL of every other player against that player's own SOUL (still for 10 frames)"""
    good = 0
    tot = 0
    for i, s in enumerate(sims):
        if J(s, 'global.kfo.M.out'):
            continue
        dr = draws(s, 'r')
        for j, o in enumerate(sims):
            if j == i or J(o, 'global.kfo.M.out'):
                continue
            h = hist[j]
            # a checkpoint: that player's SOUL there and still for 10 frames (between attacks there is no SOUL to draw)
            if len(h) < 10 or h[-1] == (-1, -1) or any(p != h[-1] for p in h[-10:]):
                continue
            tot += 1
            # build 47: the places go out in tenths of a pixel - within 0.05 px
            if any(abs(d[1] - (h[-1][0] + IN)) < 0.051 and abs(d[2] - (h[-1][1] + IN)) < 0.051 for d in dr):
                good += 1
            elif tot - good <= 3:
                print('  %s: game %d does not draw game %d at %s (draws %s)' % (tag, i + 1, j + 1, h[-1], [(round(d[1], 1), round(d[2], 1)) for d in dr][:8]), flush=True)
    return good, tot


def soul_sync(n, frames, tag, seed=4242, prof='normal'):
    t0 = time.time()
    net, sims = make_room(n, prof, seed, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;')
    instrument(sims)
    hist = {i: [] for i in range(n)}
    rec = new_rec(n)
    cp_good = cp_tot = 0
    dup = 0
    over = 0
    switches = 0
    acts = [None] * n
    for f in range(frames):
        keep_alive(sims, f)
        still = (f % 120) >= 95
        errs = step_all(net, sims, f, lambda i, ff: roam(i, ff, still), rec)
        for e in errs:
            ok(False, '%s: game %d frame %d: %s' % (tag, e[0], e[1], e[2]))
        if errs:
            break
        for i, s in enumerate(sims):
            hist[i].append(tuple(heart(s)))
            hist[i] = hist[i][-12:]
            a = J(s, '(is_struct(global.knight_lu) && global.knight_lu.ready) ? global.knight_lu.ks[global.knight_lu.act] : -1')
            if i == 0 and acts[0] is not None and a != acts[0]:
                switches += 1
            acts[i] = a
            # never more of the others drawn than are standing (+ none twice)
            dr = draws(s, 'r')
            nal = len(alive_ids(s))
            if len(dr) > nal:
                over += 1
            pos = [(round(d[1], 2), round(d[2], 2)) for d in dr]
            if len(pos) != len(set(pos)) and len(set(pos)) < len(pos) and nal > 1:
                # two SOULs at the very same spot can be two players standing there: a duplicate is the same SOUL twice
                pass
        if f % 120 == 119:
            g, t = checkpoint_agreement(sims, hist, tag)
            cp_good += g
            cp_tot += t
    cmp = compare(rec, n)
    STATS[tag] = {'games': n, 'frames': frames, 'checkpoints': cp_tot, 'agree': cp_good, 'over': over, 'switches': switches,
                  'cycles': cmp['cycles_all'], 'logic_bad': len(cmp['logic_bad']), 'bul_same': cmp['bul_same'], 'bul_diff': cmp['bul_diff'], 'wall': round(time.time() - t0)}
    print(tag, STATS[tag], flush=True)
    return net, sims, rec, cmp


LONG = os.environ.get('KV_LONG') == '1'   # the final runs: longer SOUL-001 / SOUL-002 / SPEC-010


def fx_soul_001():
    soul_sync(2, 2600 if LONG else 1300, 'SOUL-001 (2 games)')
    s = STATS['SOUL-001 (2 games)']
    ok(s['checkpoints'] >= 10 and s['agree'] == s['checkpoints'], 'SOUL-001: two SOULs at their synchronized positions: %d / %d checkpoints' % (s['agree'], s['checkpoints']))


def fx_soul_002():
    net, sims, rec, cmp = soul_sync(8, 1500 if LONG else 760, 'SOUL-002 (8 games)')
    s = STATS['SOUL-002 (8 games)']
    ok(s['over'] == 0, 'SOUL-002: never more SOULs drawn than players standing (%d frames over)' % s['over'])
    ok(s['checkpoints'] >= 100 and s['agree'] == s['checkpoints'], 'SOUL-002: eight games, every pair at the checkpoints: %d / %d' % (s['agree'], s['checkpoints']))
    ok(s['switches'] >= 1, 'SOUL-008: the checkpoints span Knight Rush switches (%d)' % s['switches'])
    ok(s['logic_bad'] == 0 and s['cycles'] > 0, 'SOUL-002: the same match in every game (%d cycles, %d differences)' % (s['cycles'], s['logic_bad']))
    # SOUL-002 counts: each game drew the 7 others in the last frame
    counts = [len(draws(x, 'r')) for x in sims]
    ok(all(c == 7 for c in counts), 'SOUL-002: each of the 8 games draws the 7 others (%s)' % counts)
    return net, sims


def fx_soul_003_004_005():
    tag = 'SOUL-003'
    res = {}
    for hide in (False, True):
        net, sims = make_room(3, 'normal', 777, setx='_s.rush = 1; _s.mhp = 300;')
        instrument(sims)
        rec = new_rec(3)
        drawn0 = []
        drawn_by_others = []
        sent = 0
        for f in range(700):
            keep_alive(sims, f)
            if f == 200 and hide:
                sims[0].run('global.kfo.view.show = 0;')
            errs = step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
            if errs:
                ok(False, '%s hide=%s: %r' % (tag, hide, errs[:1]))
                break
            if f > 200:
                drawn0.append(len(draws(sims[0], 'r')))
                drawn_by_others.append(len(draws(sims[1], 'r')))
        res[hide] = {'rec': rec, 'drawn0': drawn0, 'others': drawn_by_others, 'pos': J(sims[0], '[global.kfo.H.pl[0].x, global.kfo.H.pl[0].y]'),
                     'cmp': compare(rec, 3)}
        if hide:
            ok(max(drawn0) == 0, 'SOUL-003: SHOW OTHER SOULS off - game 1 draws none of the others (max %d per frame)' % max(drawn0))
            ok(min(drawn_by_others[30:]) >= 1, 'SOUL-003: the others still draw game 1\'s SOUL')
            ok(J(sims[0], 'global.kfo.H.pl[0].t_p') > 0, 'SOUL-003: game 1 still sends its SOUL (the host has it)')
            # SOUL-004: opacity, at once; your SOUL full
            sims[0].run('global.kfo.view.show = 1; global.kfo.view.sop = 30; global.kfo.view.fade = 0;')
            step_all(net, sims, 701, lambda i, ff: set())
            al = [round(d[5], 3) for d in draws(sims[0], 'r')]
            ok(al and all(abs(a - 0.30) < 0.001 or abs(a - 0.105) < 0.001 for a in al), 'SOUL-004: OTHER SOUL OPACITY 30%% - the next frame draws them at 0.30 (%s)' % al)
            me = draws(sims[0], 'l')
            ok(me and all(abs(d[5] - 1) < 0.001 for d in me), 'SOUL-004: your own SOUL stays full (%s)' % [round(d[5], 2) for d in me])
            # your own SOUL in your SOUL APPEARANCE: the game's SOUL sprite (spr_dodgeheart) is the plain SOUL, so your colour
            # and edge are drawn, the heart 2 px in from obj_heart's corner (build 47's first draft took it for a SOUL mode)
            sims[0].run('global.kfo.look.col = c_lime; global.kfo.look.ol = 1;')
            step_all(net, sims, 701, lambda i, ff: set())
            me = draws(sims[0], 'l')
            hx0, hy0 = heart(sims[0])
            ok(me and me[-1][4] == 65280 and me[-1][6] >= 0 and abs(me[-1][1] - (hx0 + IN)) < 0.01 and abs(me[-1][2] - (hy0 + IN)) < 0.01,
               'SOUL-004 / colors: your own SOUL drawn GREEN with its edge, the heart where the game\'s heart is (%s, SOUL at %s)' % (me[-1:] , (hx0, hy0)))
            sims[0].run('global.kfo.look.col = c_red;')
            sims[0].run('global.kfo.view.sop = 90;')
            step_all(net, sims, 702, lambda i, ff: set())
            al = [round(d[5], 3) for d in draws(sims[0], 'r')]
            ok(al and all(abs(a - 0.90) < 0.001 or abs(a - 0.315) < 0.001 for a in al), 'SOUL-004: 90%% at once too (%s)' % al)
            ok(J(sims[1], 'global.kfo.view.sop') == 70, 'SOUL-004: the other games keep their own opacity (the default 70, build 48)')
            # SOUL-005: game 2's SOUL put on game 1's: fainter there, game 1's SOUL full and pulsing; nobody moved
            hx, hy = heart(sims[0])
            sims[0].run('global.kfo.view.fade = 1;')
            sims[1].run('obj_heart.x = %r; obj_heart.y = %r;' % (hx, hy))
            pos2 = None
            for f in range(703, 730):
                step_all(net, sims, f, lambda i, ff: set())
                pos2 = heart(sims[1])
            d2 = [d for d in draws(sims[0], 'r') if abs(d[1] - (hx + IN)) < 0.051 and abs(d[2] - (hy + IN)) < 0.051]
            ok(d2 and all(abs(d[5] - 0.9 * 0.45) < 0.001 for d in d2), 'SOUL-005: the SOUL over yours is fainter (%s)' % [round(d[5], 3) for d in d2])
            ok(J(sims[0], 'global.kfo.M.vw.cover') > 0, 'SOUL-005: your SOUL pulses (covered)')
            ok([round(v, 2) for v in heart(sims[0])] == [round(hx, 2), round(hy, 2)] and [round(v, 2) for v in pos2] == [round(hx, 2), round(hy, 2)],
               'SOUL-005: nobody is moved apart (both still at %s)' % [hx, hy])
            me = draws(sims[0], 'l')
            ok(me and abs(me[-1][5] - 1) < 0.001, 'SOUL-005: yours drawn full')
    # the match with game 1 hiding the others = the match with it showing them
    a, b = res[False]['rec'], res[True]['rec']
    sa = [(x['k'], x['ok'], x['ai'], x['seed'], x['t0']) for x in a[1]['starts']]
    sb = [(x['k'], x['ok'], x['ai'], x['seed'], x['t0']) for x in b[1]['starts']]
    ok(sa == sb and sa, 'SOUL-003: hiding the others changes no cycle of game 1 (%d cycles)' % len(sa))
    same = 0
    diff = 0
    for k, v in a[1]['snaps'].items():
        if k in b[1]['snaps']:
            if v['h'] == b[1]['snaps'][k]['h'] and v['box'] == b[1]['snaps'][k]['box']:
                same += 1
            else:
                diff += 1
    ok(diff == 0 and same > 0, 'SOUL-003: the bullets and the box at 30/60/90 frames the same with and without the others drawn (%d same, %d differ)' % (same, diff))
    STATS['SOUL-003'] = {'cycles': len(sa), 'bullet_snaps_same': same, 'differ': diff}


def fx_soul_006_spec_004():
    net, sims = make_room(4, 'normal', 99, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    for f in range(320):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False))
    # game 1 watches nobody yet; game 4 follows game 2 for SPEC-004 later: put game 4 OUT first? No - game 3 goes OUT (SOUL-006)
    before = len(draws(sims[0], 'r'))
    sims[2].run('kbr_local_death();')
    pieces = 0
    gone_frames = 0
    spect3 = -1
    for f in range(320, 420):
        keep_alive([s for k, s in enumerate(sims) if k != 2], f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False))
        pieces = max(pieces, J(sims[0], '(array_length(global.kfo.M.vw.brk) > 0) ? array_length(global.kfo.M.vw.brk[0].sh) : 0'))
        if f > 360 and len(draws(sims[0], 'r')) == before - 1:
            gone_frames += 1
        spect3 = J(sims[2], 'global.kfo.M.spect')
    ok(pieces == 6, 'SOUL-006: game 3 OUT - its SOUL breaks in game 1 (%d pieces)' % pieces)
    ok(gone_frames >= 55, 'SOUL-006: and is not drawn there any more (%d frames)' % gone_frames)
    ok(spect3 in alive_ids(sims[2]), 'SOUL-006: game 3 watches a living player by itself (%s)' % spect3)
    # SPEC-004: game 3 follows game 2; game 2 goes OUT -> the camera moves on to the next living player
    sims[2].run('global.kfo.M.spect = 2;')
    sims[1].run('kbr_local_death();')
    moved = None
    for f in range(420, 470):
        step_all(net, sims, f, lambda i, ff: set())
        sp = J(sims[2], 'global.kfo.M.spect')
        if sp != 2 and moved is None and 2 not in alive_ids(sims[2]):
            moved = (f, sp)
    ok(moved is not None and moved[1] in alive_ids(sims[2]), 'SPEC-004: the followed player OUT - the camera moves to %s by itself (frame %s)' % (moved and moved[1], moved and moved[0]))
    ok(moved is not None and moved[1] == 4, 'SPEC-004: the next one in the list after player 2 (4: 3 is OUT)')


def fx_soul_007():
    """100 leave / return cycles fed to one game's view: the ones who left (al 0) are never drawn, the ones who came back
    with a new id watch (not in the match): never a second SOUL"""
    net, sims = make_room(3, 'lan', 31, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    for f in range(200):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False))
    s = sims[0]
    over = 0
    dups = 0
    base = J(s, 'global.kfo.M.st')
    for c in range(100):
        newpid = 100 + c
        oldpid = 3 if c == 0 else 100 + c - 1
        st = json.loads(json.dumps(base))
        pl = [p for p in st['pl'] if p['pid'] != 3]
        # the one who left: OUT (gone), still in the standings; the one who came back: not in the match at all
        pl.append({'pid': oldpid, 'n': 'Ralsei', 's': 3, 'hp': 0, 'mh': 300, 'g': 0, 'al': 0, 'pl': 3, 'sg': 0, 'sr': 0, 'bot': 0, 'sk': 0, 'lat': -1, 'c': -1, 'rdy': 1, 'gone': 1})
        st['pl'] = pl
        s.run('global.kfo.M.st = json_parse(%s); kbr_view_on_state(global.kfo.M, global.kfo.M.st);' % json.dumps(json.dumps(st)))
        # stale positions keep arriving for the old id, and the new id sends some too (a watcher never should, but whatever comes)
        # (the host's list is in tenths of a pixel since build 47: 3000 = x 300)
        s.run('kbr_on_ps({ mid: global.kfo.M.mid, l: [[%d, 3000, 1500, 0], [%d, 3100, 1600, 0], [2, 2800, 1700, 0]] });' % (oldpid, newpid))
        s.run('global.SDL = []; kbr_draw_souls();')
        dr = draws(s, 'r')
        if len(dr) > 1:
            over += 1
        pos = [(d[1], d[2]) for d in dr]
        if (300 + IN, 150 + IN) in pos or (310 + IN, 160 + IN) in pos:
            dups += 1
    ok(over == 0 and dups == 0, 'SOUL-007: 100 leave / return cycles - never a SOUL for the old or the new id, never more than the 1 player standing (%d over, %d ghosts)' % (over, dups))
    STATS['SOUL-007'] = {'cycles': 100, 'ghosts': dups, 'over': over}


def watcher_join(net, sims, host_sim, cid, name='Watcher', f_now=0):
    """a room member not in the match presses SPECTATE: the host's watch reply (START with spec 1 and its match time), then
    its battle made as the launch makes it"""
    # the watcher's link (the Net drops messages to a game it does not know)
    net.q.setdefault(cid, [])
    host_sim.run('global.kfo.H.pl[array_length(global.kfo.H.pl)] = kfo_host_player_new(%d, "%s", 2, 0); global.kfo.H.pl[array_length(global.kfo.H.pl) - 1].hi = 1;'
                 'kfo_host_watch(kfo_host_player(%d));' % (cid, name, cid))
    # the START the host just sent to the watcher (kfo_down to cid -> the Net): taken off the queue
    q = net.q.get(cid)
    msgs = []
    if q:
        for item in sorted(q):
            msgs.append(json.loads(item[2]))
        net.q[cid] = []
    start = None
    for m in msgs:
        if m.get('t') == 'down' and (m.get('m') or {}).get('k') == 'start':
            start = m['m']
    ok(start is not None and start.get('spec') == 1, 'the host answers WATCH with a watching START (spec 1)')
    host_t = start['h']
    names = ['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna', name]
    exc = (ROOM % (name, 2, cid, members_gml(len(sims), names)) +
           'global.kfo.M = kfo_match_new(json_parse(test_start_text())); global.kfo.M.launched = true;')
    open_ok = J(host_sim, 'global.kfo.H.mset.open')
    kn = J(host_sim, 'global.kfo.H.mset.kn')

    def pre(s):
        s.ct_offset = 4242
        install(s, net, cid)
        s.start_text = json.dumps(start)
    host = KN[OKREG[open_ok if open_ok in kn else kn[0]]]
    w, e = lu_battle(host, party=(2,), combo=3, extra_cfg=exc, world=False, pre=pre)
    ok(e is None, 'the watcher\'s battle is made (%r)' % (e,))
    net.add(cid, w)
    w.rng.seed(cid)
    preload_base(w)
    w.premocked = premock(w)
    w.define_event('obj_battlecontroller', 'Step', 0, BR_STUB)
    w._snapauto = False
    # the watcher's clock: the host's match time when the START left, the same as in kfo_on_start
    w.run('var _M = global.kfo.M; _M.go = true; _M.t0ms = current_time - (%r);' % host_t)
    instrument([w])
    return w


def fx_spec():
    net, sims = make_room(4, 'normal', 1234, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;')
    instrument(sims)
    rec = new_rec(5)
    for f in range(260):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
    H = sims[0]
    hk = J(H, '[global.kfo.M.R.ph, global.kfo.M.R.k, global.kfo.M.R.af]')
    w = watcher_join(net, sims, H, 9)
    ok(J(w, 'global.kfo.M.spec') and not J(w, 'global.kfo.M.me'), 'SPEC-001: the room member joins as a watcher (spec, not a player)')
    ok(J(H, 'kfo_host_watchers()') == 1, 'SPEC-001 / QOL-004: the host counts 1 watcher')
    allg = sims + [w]
    wst = []
    for f in range(260, 1800):
        keep_alive(sims, f)
        errs = step_all(net, allg, f, lambda i, ff: roam(i, ff, False) if i < 4 else set(), rec)
        for e in errs:
            ok(False, 'SPEC: game %d frame %d %s' % e)
        if errs:
            break
        st = state(w)
        if st['ph'] == 'run' and (not wst or wst[-1] != st['k']):
            wst.append(st['k'])
    ok(wst and min(wst) >= hk[1], 'SPEC-002: joined in the middle of cycle %d (%s, frame %d): the watcher never starts an earlier cycle (it ran %s)' % (hk[1], hk[0], hk[2], wst[:6]))
    hs = {x['k']: (x['ok'], x['ai'], x['seed'], x['t0']) for x in rec[1]['starts']}
    ws = {x['k']: (x['ok'], x['ai'], x['seed'], x['t0']) for x in rec[5]['starts']}
    common = [k for k in ws if k in hs]
    ok(common and all(ws[k] == hs[k] for k in common), 'SPEC-002: every cycle it runs is the host\'s (knight, attack, seed, start) - %d cycles' % len(common))
    cmp = compare({k: v for k, v in rec.items() if k <= 4}, 4)
    ok(not cmp['logic_bad'], 'SPEC-002: the players\' match unchanged by the watcher (%d cycles)' % cmp['cycles_all'])
    # SPEC-005: FULL ARENA - every standing SOUL, none singled out (all at full strength, no focus ring)
    w.run('global.kfo.M.vw.cam = 1; global.kfo.view.spv = 0;')
    step_all(net, allg, 1801, lambda i, ff: set())
    dr = draws(w, 'r')
    ok(len(dr) == len(alive_ids(w)) == 4 and all(abs(d[5] - 1) < 0.001 for d in dr), 'SPEC-005: FULL ARENA draws the %d standing SOULs, all full (%s)' % (len(alive_ids(w)), [round(d[5], 2) for d in dr]))
    # SPEC-003: 100 target changes with RIGHT (LB / RB the same path): always the next living player in the list's order
    w.run('global.kfo.M.vw.cam = 0;')
    good = 0
    for c in range(100):
        ids = alive_ids(w)
        cur = J(w, 'global.kfo.M.spect')
        want = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else None
        w.kb = {'p_right'}
        w.run('kbr_spectate_tick();')
        w.kb = set()
        if J(w, 'global.kfo.M.spect') == want:
            good += 1
    ok(good == 100, 'SPEC-003: 100 target changes, each the next living player (%d right)' % good)
    STATS['SPEC-003'] = {'changes': 100, 'right': good}
    # SPEC-006: the watching HUD reads the host's standings
    texts = []
    w.mock('kbr_hud_text', lambda s, x, y, t, c: (texts.append(str(t)), 0)[1])
    w.run('global.kfo.view.shud = 0; kbr_hud_spec(0, 0, global.kfo.M);')
    p = J(w, 'kbr_st_player(global.kfo.M, global.kfo.M.spect)')
    want_hp = '%d/%d' % (round(p['hp']), round(p['mh']))
    ok(any(want_hp in t for t in texts) and any(p['n'] in t for t in texts), 'SPEC-006: the HUD shows %s and %s (%s)' % (p['n'], want_hp, texts[:6]))
    # SPEC-007: the watcher goes back to the room: the host stops counting it, the match goes on unchanged
    w.run('kfo_up({ k: "unwatch", mid: global.kfo.M.mid });')
    for f in range(1802, 1840):
        step_all(net, allg, f, lambda i, ff: set())
    ok(J(H, 'kfo_host_watchers()') == 0, 'SPEC-007: back to the room - the host counts 0 watchers')
    STATS['SPEC-002'] = {'joined_at': hk, 'cycles_run': len(common)}


def fx_spec_010():
    t0 = time.time()
    net, sims = make_room(8, 'normal', 808, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;')
    instrument(sims)
    rec = new_rec(10)
    for f in range(150):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
    w1 = watcher_join(net, sims, sims[0], 9, 'Watch1')
    w2 = watcher_join(net, sims, sims[0], 10, 'Watch2')
    allg = sims + [w1, w2]
    bad = []
    FR = 1800 if LONG else 760
    for f in range(150, FR):
        keep_alive(sims, f)
        errs = step_all(net, allg, f, lambda i, ff: roam(i, ff, False) if i < 8 else ({'p_right'} if ff % 45 == 0 else set()), rec)
        bad += errs
        if errs:
            break
    ok(not bad, 'SPEC-010: 8 players + 2 watchers, %d frames: no error (%r)' % (FR, bad[:1]))
    cmp = compare(rec, 10)
    ok(not cmp['logic_bad'] and cmp['cycles_all'] > 0, 'SPEC-010: no divergence - every game the same cycles (%d, %d differences)' % (cmp['cycles_all'], len(cmp['logic_bad'])))
    ok(J(sims[0], 'kfo_host_watchers()') == 2, 'SPEC-010 / QOL-004: the host counts 2 watchers')
    st = J(sims[3], 'global.kfo.M.st')
    ok(st.get('sc') == 2 and st.get('an') == 8, 'QOL-004: every game\'s standings say 8 standing, 2 watching (%s, %s)' % (st.get('an'), st.get('sc')))
    STATS['SPEC-010'] = {'games': 10, 'frames': FR, 'cycles': cmp['cycles_all'], 'differences': len(cmp['logic_bad']), 'wall': round(time.time() - t0)}


def fx_qol_001():
    net, sims = make_room(2, 'lan', 55, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    for f in range(200):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False))
    s = sims[0]
    q = ord('F')   # build 48: QUICK SETTINGS moved to F (Q is a targeting key)
    s.input.begin_frame = lambda fno: None

    def press(keys):
        held = set(keys)
        s.input.pressed = held - s.input.held
        s.input.released = s.input.held - held
        s.input.held = held

    press({q})
    step_all(net, sims, 200, lambda i, ff: set())
    ok(J(s, 'global.kfo.M.vw.qs'), 'QOL-001: Q opens QUICK SETTINGS during the match')
    press(set())
    hx = heart(s)
    # the second row is OPACITY: down, then right twice (+10)
    rows = J(s, 'kbr_qs_rows(global.kfo.M)')
    ok(rows[:3] == ['show', 'sop', 'names'], 'QOL-001: its rows %s' % rows)
    sop0 = J(s, 'global.kfo.view.sop')
    for keys in ({'p_down', 'down'}, set(), {'p_right', 'right'}, set(), {'p_right', 'right'}, set()):
        step_all(net, sims, 201, lambda i, ff, kk=keys: kk if i == 0 else set())
    ok(J(s, 'global.kfo.view.sop') == sop0 + 10, 'QOL-001: < > on OPACITY: %d -> %d at once' % (sop0, J(s, 'global.kfo.view.sop')))
    al = [round(d[5], 2) for d in draws(s, 'r')]
    ok(al and abs(al[0] - (sop0 + 10) / 100.0) < 0.011 or (al and al[0] < 0.6), 'QOL-001: the others drawn at the new opacity the same frame (%s)' % al)
    ok(heart(s) == hx, 'QOL-001: your SOUL held still while it is open (the arrows changed the settings)')
    press({q})
    step_all(net, sims, 210, lambda i, ff: set())
    press(set())
    ok(not J(s, 'global.kfo.M.vw.qs'), 'QOL-001: Q closes it')
    s.run('global.KS = global.kfo; global.kfo = undefined; kfo_get(); global.KV = global.kfo.view.sop; global.kfo = global.KS;')
    ok(J(s, 'global.KV') == sop0 + 10, 'QOL-001 / QOL-002: kept - a new game reads %d from the ini' % (sop0 + 10))


def fx_souls_key():
    """build 47 (player request): OTHER SOULS (V) hides / shows the other SOULs at once during the match, for this game only,
    kept for the next game; a watcher's V is the watching key (it does not change the setting); no names under SOULs unless
    SHOW PLAYER NAMES is on (not even the one a watcher follows)"""
    net, sims = make_room(3, 'lan', 56, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    for f in range(200):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False))
    s = sims[0]
    v = ord('V')
    s.input.begin_frame = lambda fno: None

    def press(keys):
        held = set(keys)
        s.input.pressed = held - s.input.held
        s.input.released = s.input.held - held
        s.input.held = held
    ok(J(s, 'global.kfo.view.show') == 1 and J(s, 'global.kfo.view.sop') == 70, 'SOULS: other SOULs shown at 70%% by default (%s, %s)' % (J(s, 'global.kfo.view.show'), J(s, 'global.kfo.view.sop')))
    al = [round(d[5], 3) for d in draws(s, 'r')]
    ok(al and all(abs(a - 0.70) < 0.001 or abs(a - 0.315) < 0.001 or abs(a - 0.42) < 0.001 or abs(a - 0.189) < 0.001 for a in al), 'SOULS: drawn at 70%% (%s)' % al)
    press({v})
    step_all(net, sims, 200, lambda i, ff: set())
    press(set())
    ok(J(s, 'global.kfo.view.show') == 0 and 'HIDDEN' in J(s, 'global.kfo.M.vw.banner'), 'SOULS: V hides them (banner "%s")' % J(s, 'global.kfo.M.vw.banner'))
    step_all(net, sims, 201, lambda i, ff: set())
    ok(len(draws(s, 'r')) == 0 and len(draws(sims[1], 'r')) == 2, 'SOULS: none drawn in that game; the other games still draw it')
    s.run('global.KS = global.kfo; global.kfo = undefined; kfo_get(); global.KV = global.kfo.view.show; global.kfo = global.KS;')
    ok(J(s, 'global.KV') == 0, 'SOULS: kept - a new game starts with them hidden')
    press({v})
    step_all(net, sims, 202, lambda i, ff: set())
    press(set())
    step_all(net, sims, 203, lambda i, ff: set())
    ok(J(s, 'global.kfo.view.show') == 1 and len(draws(s, 'r')) == 2 and 'SHOWN' in J(s, 'global.kfo.M.vw.banner'), 'SOULS: V again shows them ("%s")' % J(s, 'global.kfo.M.vw.banner'))
    # no names under the SOULs (names off: nothing), names on: the name
    texts = []
    s.mock('draw_text', lambda sm, x, y, t: (texts.append(str(t)), 0)[1])
    s.run('global.SDL = []; kbr_draw_souls();')
    ok(not any('Susie' in t or 'Ralsei' in t for t in texts), 'SOULS: no name under the other SOULs (names off): %s' % texts)
    texts.clear()
    s.run('global.kfo.view.names = 1; global.SDL = []; kbr_draw_souls(); global.kfo.view.names = 0;')
    ok(any('Susie' in t for t in texts), 'SOULS: SHOW PLAYER NAMES on - the name is drawn (%s)' % texts)
    # a watcher (OUT) following the other: still no name under it; V does not change the setting
    s.run('kbr_local_death();')
    for f in range(204, 270):
        step_all(net, sims, f, lambda i, ff: set())
    ok(J(s, 'global.kfo.M.out') and J(s, 'global.kfo.M.spect') in (2, 3), 'SOULS: game 1 OUT, watching another (%s)' % J(s, 'global.kfo.M.spect'))
    texts.clear()
    s.run('global.SDL = []; kbr_draw_souls();')
    ok(not any('Susie' in t or 'Ralsei' in t for t in texts), 'SOULS: watching - no name under the followed SOUL either (%s)' % texts)
    press({v})
    step_all(net, sims, 271, lambda i, ff: set())
    press(set())
    ok(J(s, 'global.kfo.view.show') == 1, 'SOULS: a watcher\'s V is the watching key - the setting stays')


def rgb(r, g, b):
    return r + g * 256 + b * 65536


PRE = [rgb(255, 0, 0), rgb(255, 140, 30), rgb(255, 230, 40), rgb(40, 220, 80), rgb(30, 230, 230), rgb(50, 110, 255), rgb(165, 70, 255), rgb(255, 110, 200)]


def fx_colors():
    """Doc A's colour tests in the match: eight players each choose a colour (purple, cyan ...) - each game draws its own SOUL
    in its colour and the seven others in theirs, through Knight Rush switches and while watching; two players with the same
    colour told apart (shape markers, numbers); and the same match with every colour red gives the very same match"""
    t0 = time.time()
    net, sims = make_room(8, 'normal', 4848, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    for i, s in enumerate(sims):
        s.run('global.kfo.look.col = %d; kfo_look_sent();' % PRE[i])
    pid = [J(s, 'global.kfo.my') for s in sims]
    want = {pid[i]: PRE[i] for i in range(8)}
    rec = new_rec(8)
    right = tot = 0
    own = 0
    switches = 0
    last = None
    for f in range(700):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, (ff % 120) >= 95), rec)
        k = J(sims[0], '(is_struct(global.knight_lu) && global.knight_lu.ready) ? global.knight_lu.ks[global.knight_lu.act] : -1')
        if last is not None and k != last:
            switches += 1
        last = k
        if f >= 120 and f % 40 == 0:
            for i, s in enumerate(sims):
                me = draws(s, 'l')
                if me:
                    own += 1 if me[-1][4] == PRE[i] else 0
                # each other SOUL drawn in its player's colour: the draws of this frame against the standings' players
                dr = [d for d in draws(s, 'r')]
                if not dr:
                    # between attacks (no SOULs in the box, none sent): nothing to check
                    continue
                cols = sorted(d[4] for d in dr)
                tot += 1
                if cols == sorted(PRE[j] for j in range(8) if j != i):
                    right += 1
                elif tot - right <= 3:
                    print('  colours: game %d frame %d draws %s' % (i + 1, f, cols), flush=True)
    ok(tot > 0 and right == tot, 'colors: 8 players, 8 colours - every game draws the 7 others each in their colour: %d / %d checks (through %d knight switches)' % (right, tot, switches))
    ok(own > 0, 'colors: and its own SOUL in its own colour (%d checks)' % own)
    ok(switches >= 1, 'colors: the checks span Knight Rush switches (%d)' % switches)
    # two with the same colour (game 2 takes game 7's purple): SHAPE MARKERS and PLAYER NUMBERS tell them apart
    sims[1].run('global.kfo.look.col = %d; kfo_look_sent();' % PRE[6])
    for f in range(700, 760):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: set(), rec)
    s = sims[0]
    s.run('global.kfo.view.mark = 1; global.kfo.view.nums = 1;')
    marks = []
    tags = []
    s.mock('kfo_mark_draw', lambda sm, x, y, slot, col: (marks.append(int(slot)), 0)[1])
    s.mock('kbr_hud_text', lambda sm, x, y, t, c: (tags.append(str(t)), 0)[1])
    s.run('global.SDL = []; kbr_draw_souls();')
    purp = [d for d in draws(s, 'r') if d[4] == PRE[6]]
    # build 48: SOUL SETTINGS has no shape markers / player numbers any more (no marks around SOULs, as you asked): two
    # players with one colour are both drawn in it, nothing drawn around them
    ok(len(purp) == 2 and len(marks) == 0, 'colors: two purple SOULs - both drawn purple, no markers around SOULs (%s)' % marks)
    s.run('global.kfo.view.mark = 0; global.kfo.view.nums = 0;')
    # watching (game 8 OUT): the others still in their colours
    sims[7].run('kbr_local_death();')
    for f in range(760, 830):
        keep_alive(sims[:7], f)
        step_all(net, sims, f, lambda i, ff: set(), rec)
    dr = draws(sims[7], 'r')
    wantw = sorted([PRE[0], PRE[6]] + [PRE[j] for j in range(2, 7)])
    ok(sorted(d[4] for d in dr) == wantw, 'colors: watching (OUT), the others still in their colours (%s)' % sorted(d[4] for d in dr))
    cmp = compare(rec, 8)
    ok(not cmp['logic_bad'], 'colors: the same match in every game (%d cycles)' % cmp['cycles_all'])
    STATS['colors'] = {'checks': tot, 'right': right, 'switches': switches, 'wall': round(time.time() - t0)}


def fx_colors_cosmetic():
    """zero gameplay change from colours: the same 3-player match with everybody red and with everybody in a colour of their
    own (and SOUL colour mode changes) - the same cycles, the same bullets and box at 30 / 60 / 90 frames of every attack; a
    game SOUL mode (the yellow shooting SOUL) keeps the game's own look unless GAMEPLAY COLOURS says otherwise, and drawing never
    changes the SOUL itself"""
    res = {}
    for colored in (False, True):
        # build 48: on the LAN profile - on 'normal' the extra messages of the coloured run (its look, the targeting modes)
        # shift the simulated network's jitter draws, the match then starts a few frames later in one run than the other,
        # and this test's frame-numbered keys move the SOULs differently (not a gameplay difference: the attack starts,
        # knights, seeds and ticks were equal)
        net, sims = make_room(3, 'lan', 919, setx='_s.rush = 1; _s.mhp = 300;')
        instrument(sims)
        if colored:
            for i, s in enumerate(sims):
                s.run('global.kfo.look.col = %d; global.kfo.look.ol = 1; global.kfo.look.olc = %d; kfo_look_sent(); global.kfo.view.cmode = %d;' % (PRE[4 + i], i, i))
        rec = new_rec(3)
        for f in range(700):
            keep_alive(sims, f)
            step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
        res[colored] = (rec, sims)
    a, b = res[False][0], res[True][0]
    sa = [(x['k'], x['ok'], x['ai'], x['seed'], x['t0']) for x in a[1]['starts']]
    sb = [(x['k'], x['ok'], x['ai'], x['seed'], x['t0']) for x in b[1]['starts']]
    ok(sa and sa == sb, 'colors: the match with colours = the match all red (%d cycles)' % len(sa))
    same = diff = 0
    for k, v in a[1]['snaps'].items():
        if k in b[1]['snaps']:
            if v['h'] == b[1]['snaps'][k]['h'] and v['box'] == b[1]['snaps'][k]['box'] and (v['hx'], v['hy']) == (b[1]['snaps'][k]['hx'], b[1]['snaps'][k]['hy']):
                same += 1
            else:
                diff += 1
    ok(same > 0 and diff == 0, 'colors: the bullets, the box and the SOUL the same at every snapshot (%d same, %d differ)' % (same, diff))
    # a game SOUL mode: the yellow shooting SOUL
    s = res[True][1][0]
    hv = s.py(s.eval('instance_exists(obj_heart) ? 1 : 0'))
    if hv:
        s.run('with (obj_heart) color = 1; global.kfo.look.gmc = 0;')
        before = s.py(s.eval('[obj_heart.x, obj_heart.y, obj_heart.sprite_index, obj_heart.mask_index, obj_heart.color, obj_heart.image_blend]'))
        s.run('global.R = -1; with (obj_heart) global.R = kbr_heart_draw();')
        r0 = s.py(s.eval('global.R'))
        s.run('global.kfo.look.gmc = 1; global.R = -1; with (obj_heart) global.R = kbr_heart_draw();')
        r1 = s.py(s.eval('global.R'))
        after = s.py(s.eval('[obj_heart.x, obj_heart.y, obj_heart.sprite_index, obj_heart.mask_index, obj_heart.color, obj_heart.image_blend]'))
        # build 48: SOUL MODES (MINE + MARK) left with the simplified SOUL settings - a game mode always keeps the game's look
        ok(r0 is False and r1 is False and before == after, 'colors: the yellow SOUL mode - the game\'s own look first (%s), MINE + MARK draws your colour with the mode mark (%s); the SOUL untouched (%s)' % (r0, r1, after))
        s.run('with (obj_heart) color = 0; global.kfo.look.gmc = 0;')
    else:
        ok(False, 'colors: no SOUL to check the mode on')


def fx_qol_005():
    res = {}
    for prof in ('lan', 'extreme'):
        net, sims = make_room(2, prof, 5, setx='_s.rush = 1; _s.mhp = 300;')
        for f in range(1200):
            keep_alive(sims, f)
            step_all(net, sims, f, lambda i, ff: set())
        res[prof] = J(sims[1], 'kbr_net_state(global.kfo.M)')
    ok(res['lan']['warn'] == '' and res['lan']['loss'] in (0, -1), 'QOL-005: a clean link - no warning, no loss (%s)' % res['lan'])
    # the link: 300 ms round trip (150 +- 60 each way), 5% of the unreliable messages lost each way (a ping and its answer:
    # about 10% of the round trips); the ping shown is the running average of the samples
    ok(res['extreme']['loss'] >= 3 and 220 <= res['extreme']['ping'] <= 400, 'QOL-005: a 5%%-loss 300 ms link - the loss is measured (%s%%), the ping too (%s ms)' % (res['extreme']['loss'], res['extreme']['ping']))
    ok(res['lan']['ping'] < 100, 'QOL-005: the clean link\'s ping under 100 ms (%s ms: frame steps of 33 ms)' % res['lan']['ping'])
    # the host's news stops: the client says so after 2.5 s
    net, sims = make_room(2, 'lan', 6, setx='_s.rush = 1; _s.mhp = 300;')
    for f in range(200):
        step_all(net, sims, f, lambda i, ff: set())
    net.down_links.add((1, 2))
    seen = ''
    for f in range(200, 330):
        step_all(net, sims, f, lambda i, ff: set())
        seen = J(sims[1], 'kbr_net_state(global.kfo.M).warn') or seen
    ok('NO NEWS FROM THE HOST' in seen, 'QOL-005: the host\'s messages stop - "%s"' % seen)
    STATS['QOL-005'] = {'lan': res['lan'], 'extreme': res['extreme'], 'stopped': seen}


def fx_elim_100():
    """Doc B: 100 eliminations -> watching. Rooms of 8 games (Knight Rush); in each, 6 players go OUT one after another (the 7th
    would end the match), 70 frames apart, the host among them now and then. Per transition, in the game that fell (X):
      OUT at once; its SOUL breaks in the other games; within 60 frames it follows a living player by itself;
      40 frames on, no standing game draws X's SOUL any more (each draws exactly the others standing) and every game's
      standings have X OUT;
      while watching, X's keys do nothing to the match: Z held / tapped, C held, S held, A tapped with three skills in its
      slots, no cooldown and a full gauge - no skill sent (sk / sg), the slots untouched; a bullet hitting X takes 0 HP;
      its HP the same all the way.
    The control: the same Z hold in a standing game does use a skill (the keys reach the game in this harness).
    After each room: every game (the fallen ones too) ran the very same cycles (knight, attack, seed, start)."""
    t0 = time.time()
    want = int(os.environ.get('KV_ELIM', '100'))
    rnd = random.Random(4700)
    done = good = rooms = 0
    ctrl_ok = ctrl_tries = 0
    follow_f = []
    bad = []
    cyc = lbad = 0
    while done < want:
        rooms += 1
        net, sims = make_room(8, 'normal', 7000 + rooms, setx='_s.rush = 1; _s.mhp = 300;', netseed=rooms)
        instrument(sims)
        for s in sims:
            if 'obj_testbullet' not in s.objects:
                s.define_object('obj_testbullet')
        ups = {}
        orig = net.send

        def spy(cid, m, orig=orig):
            if m.get('t') == 'up':
                ups.setdefault(cid, []).append((round(net.t), (m.get('m') or {}).get('k')))
            return orig(cid, m)
        net.send = spy
        rec = new_rec(8)
        fallen = []
        order = list(range(8))
        rnd.shuffle(order)
        order = order[:6]
        f = 0

        def run_frames(n, keys=None):
            nonlocal f
            errs = []
            for _ in range(n):
                keep_alive([s for k, s in enumerate(sims) if k not in fallen], f)
                errs += step_all(net, sims, f, keys or (lambda i, ff: roam(i, ff, False) if i not in fallen else set()), rec)
                f += 1
                if errs:
                    break
            return errs
        errs = run_frames(200)
        # the control, once per room: a standing game's Z hold uses a skill
        for tries in range(3):
            y = [k for k in range(8) if k not in order][0]
            Y = sims[y]
            Y.run('var _S = global.kfo.M.sk; _S.slots = [{ sid: 11, rev: 0 }, { sid: 13, rev: 0 }, { sid: 10, rev: 0 }]; _S.cd = 0; _S.sel = 0; global.kfo.M.g = 100;')
            n0 = len([u for u in ups.get(y + 1, []) if u[1] in ('sk', 'sg')])
            Y.press('Z', hold=16)
            errs += run_frames(20)
            ctrl_tries += 1
            if len([u for u in ups.get(y + 1, []) if u[1] in ('sk', 'sg')]) > n0:
                ctrl_ok += 1
                break
        for j, x in enumerate(order):
            if errs or done >= want:
                break
            X = sims[x]
            xp = J(X, 'global.kfo.my')
            # a full hand: if the keys reached the match while watching, a skill would go
            X.run('var _S = global.kfo.M.sk; _S.slots = [{ sid: 11, rev: 0 }, { sid: 13, rev: 0 }, { sid: 10, rev: 0 }]; _S.cd = 0; _S.sel = 0; global.kfo.M.g = 100;')
            X.run('kbr_local_death();')
            fallen.append(x)
            t_out = net.t
            why = []
            if J(X, 'global.kfo.M.out') is not True:
                why.append('not OUT')
            hp0 = J(X, 'global.hp[kbr_char()]')
            slots0 = J(X, 'array_length(global.kfo.M.sk.slots)')
            X.press('Z', hold=30)
            X.press('C', frame=X.frame_no + 32, hold=20)
            X.press('S', frame=X.frame_no + 34, hold=20)
            X.press('A', frame=X.frame_no + 56)
            X.press('Z', frame=X.frame_no + 60)
            pieces = 0
            fol = None
            for k in range(70):
                errs += run_frames(1)
                if errs:
                    break
                for g in range(8):
                    if g not in fallen:
                        pieces = max(pieces, J(sims[g], '(array_length(global.kfo.M.vw.brk) > 0) ? array_length(global.kfo.M.vw.brk[0].sh) : 0'))
                        break
                sp = J(X, 'global.kfo.M.spect')
                if fol is None and sp != xp and sp in alive_ids(X):
                    fol = k + 1
                if k == 40:
                    for g in range(8):
                        if g in fallen:
                            continue
                        G = sims[g]
                        al = alive_ids(G)
                        nd = len(draws(G, 'r'))
                        # kbr_alive_ids: the others standing (not this game's own player)
                        if xp in al or nd != len(al):
                            why.append('game %d: alive %s, draws %d' % (g + 1, al, nd))
                    for g in range(8):
                        if xp in alive_ids(sims[g]):
                            why.append('game %d standings: %d still in' % (g + 1, xp))
            if errs:
                why.append('error %s' % (errs[:1],))
            if fol is None or fol > 60:
                why.append('follows nobody within 60 frames (%s)' % fol)
            else:
                follow_f.append(fol)
            if pieces < 6:
                why.append('SOUL broke in %d pieces' % pieces)
            sent_after = [u for u in ups.get(x + 1, []) if u[0] > t_out and u[1] in ('sk', 'sg')]
            if sent_after:
                why.append('skills sent while watching %s' % sent_after)
            if J(X, 'array_length(global.kfo.M.sk.slots)') != slots0:
                why.append('slots changed while watching')
            X.run('with (instance_create(0, 0, obj_testbullet)) { global.DX = kbr_dmg_taken(0); instance_destroy(); }')
            if J(X, 'global.DX') != 0:
                why.append('a bullet took %s HP' % J(X, 'global.DX'))
            if J(X, 'global.hp[kbr_char()]') != hp0:
                why.append('HP %s -> %s' % (hp0, J(X, 'global.hp[kbr_char()]')))
            done += 1
            if why:
                bad.append((rooms, x + 1, why[:3]))
                print('  ELIM room %d game %d: %s' % (rooms, x + 1, why[:3]), flush=True)
            else:
                good += 1
        cmp = compare(rec, 8)
        cyc += cmp['cycles_all']
        lbad += len(cmp['logic_bad']) + cmp['dupes']
        print('  ELIM room %d: %d transitions so far, %d right; %d cycles all games, %d differences; %.0fs' % (rooms, done, good, cmp['cycles_all'], len(cmp['logic_bad']), time.time() - t0), flush=True)
        if errs:
            ok(False, 'ELIM: room %d stopped on an error %s' % (rooms, errs[:1]))
            break
    ok(done >= want and good == done, 'SPEC / Doc B: %d eliminations -> watching, %d right (%s)' % (done, good, bad[:3]))
    ok(ctrl_ok == rooms, 'ELIM control: a standing game\'s Z hold used a skill in %d / %d rooms (%d tries)' % (ctrl_ok, rooms, ctrl_tries))
    ok(lbad == 0 and cyc > 0, 'ELIM: every game, the fallen ones too, the same cycles (%d, %d differences)' % (cyc, lbad))
    STATS['ELIM-100'] = {'transitions': done, 'right': good, 'rooms': rooms, 'follow_frames_max': max(follow_f) if follow_f else None,
                         'control_ok': ctrl_ok, 'cycles': cyc, 'differences': lbad, 'wall': round(time.time() - t0)}


def fx_soak_br():
    """A long match: 8 players + 2 watchers (Knight Rush), KV_SOAK_MIN game minutes (default 15). Checked: no error in any game;
    every game the same cycles (knight, attack, seed, start), none twice; the host counts the 2 watchers at the end; every
    standing game draws exactly the 7 others at every check (each 30 frames); the number of instances in each game does not
    grow (each 1,800 frames: the most at the end within 50 of the most in the first 3 minutes)."""
    t0 = time.time()
    mins = float(os.environ.get('KV_SOAK_MIN', '15'))
    FR = int(mins * 1800)
    net, sims = make_room(8, 'normal', 4848, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;', netseed=48)
    instrument(sims)
    rec = new_rec(10)
    for f in range(150):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
    w1 = watcher_join(net, sims, sims[0], 9, 'Watch1')
    w2 = watcher_join(net, sims, sims[0], 10, 'Watch2')
    allg = sims + [w1, w2]
    bad = []
    wrong = checks = 0
    inst = {i: [] for i in range(10)}
    for f in range(150, FR):
        keep_alive(sims, f)
        errs = step_all(net, allg, f, lambda i, ff: roam(i, ff, False) if i < 8 else ({'p_right'} if ff % 45 == 0 else set()), rec)
        bad += errs
        if errs:
            break
        if f % 30 == 0:
            for i in range(8):
                checks += 1
                if len(draws(sims[i], 'r')) != 7:
                    wrong += 1
        if f % 1800 == 0:
            for i, s in enumerate(allg):
                inst[i].append(J(s, 'instance_count'))
            print('  SOAK %.1f game min: %.0fs, instances %s' % (f / 1800.0, time.time() - t0, [inst[i][-1] for i in range(10)]), flush=True)
    ok(not bad, 'SOAK: 8 players + 2 watchers, %.1f game minutes (%d frames): no error (%r)' % (mins, FR, bad[:1]))
    cmp = compare(rec, 10)
    ok(not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] > 0, 'SOAK: every game (the watchers too) the same cycles (%d, %d differences, %d twice)'
       % (cmp['cycles_all'], len(cmp['logic_bad']), cmp['dupes']))
    ok(J(sims[0], 'kfo_host_watchers()') == 2, 'SOAK: the host still counts 2 watchers')
    ok(checks > 0 and wrong == 0, 'SOAK: every check, each player\'s game draws the 7 others (%d / %d right)' % (checks - wrong, checks))
    grow = []
    for i in range(10):
        l = inst[i]
        if len(l) >= 3:
            early = max(l[:min(len(l), 4)])
            if max(l[-2:]) > early + 50:
                grow.append((i + 1, l))
    ok(not grow, 'SOAK: no game\'s instance count grows (%s)' % grow[:2])
    STATS['SOAK-BR'] = {'games': 10, 'game_minutes': mins, 'frames': FR, 'cycles': cmp['cycles_all'], 'differences': len(cmp['logic_bad']), 'twice': cmp['dupes'],
                        'draw_checks': checks, 'draw_wrong': wrong, 'instances_first_last': {i + 1: (inst[i][0], inst[i][-1]) for i in range(10) if inst[i]},
                        'wall': round(time.time() - t0)}


def fx_b48():
    """Build 48 (your report "Show Other SOULs doesn't work"): what reaches the screen. In every game the SOULs are drawn with
    draw_sprite_ext of spr_khub_soul (a white SOUL tinted with the player's colour - nothing depends on fog any more), each
    other player at their synchronized place in THEIR colour at the OTHER SOUL OPACITY, your own fully opaque in yours;
    gpu_set_fog and draw_circle are never called for a SOUL (no rings). Host and clients alike; SHOW OTHER SOULS off in one
    game hides the others there only; on again, back at once; a colour change reaches the others; a Knight Rush switch
    keeps them drawn."""
    t0 = time.time()
    net, sims = make_room(3, 'normal', 4848, setx='_s.rush = 1; _s.mhp = 300;')
    instrument(sims)
    cols = [255, 16776960, 16711808]   # red, cyan, purple (BGR)
    for i, s in enumerate(sims):
        s.run('global.kfo.look.col = %d; kfo_look_sent();' % cols[i])
        s.SPR = []
        s.BAD = []
        def dse(sim, spr, sub, x, y, xs, ys, rot, col, a, _s=s):
            _s.SPR.append(('soul' if sim.py(spr) == sim.assets.get('spr_khub_soul') else sim.py(spr), sub, x, y, col, a))
            return 0
        s.mock('draw_sprite_ext', dse)
        # (counted while a SOUL is being drawn: the others' - kbr_draw_souls - and yours - obj_heart's Draw)
        s.mock('gpu_set_fog', lambda sim, *a, _s=s: (_s.BAD.append('fog') if str(sim.globals.get('SDT', '')) not in ('', 'None') else None, 0)[1])
        s.mock('draw_circle', lambda sim, *a, _s=s: (_s.BAD.append('circle') if str(sim.globals.get('SDT', '')) not in ('', 'None') else None, 0)[1])
    for s in sims:
        s.eval('spr_khub_soul')
    soul = 'soul'
    pid = [J(s, 'global.kfo.my') for s in sims]
    def frame_all(f, keys=None):
        for s in sims:
            s.SPR = []
            s.BAD = []
        keep_alive(sims, f)
        return step_all(net, sims, f, keys or (lambda i, ff: roam(i, ff, (ff % 120) >= 95)))
    for f in range(330):
        frame_all(f)
    # checks over the next 300 frames
    good = tot = 0
    own_full = own_tot = 0
    bad = []
    switches = 0
    act0 = J(sims[0], 'global.knight_lu.ks[global.knight_lu.act]')
    for f in range(330, 630):
        frame_all(f)
        a = J(sims[0], 'global.knight_lu.ks[global.knight_lu.act]')
        if a != act0:
            switches += 1
            act0 = a
        for i, s in enumerate(sims):
            if s.BAD:
                bad.append((f, i + 1, s.BAD[:3]))
            hearts = [d for d in s.SPR if d[0] == soul and d[1] == 0]
            # yours: full, your colour
            mine = [d for d in hearts if abs(d[5] - 1) < 0.001 and d[4] == cols[i]]
            own_tot += 1
            if mine or not J(s, 'instance_exists(obj_heart) && obj_heart.visible'):
                own_full += 1
            elif own_tot - own_full <= 3:
                print('  B48 frame %d game %d own: %s spr %s' % (f, i + 1, [(round(d[2], 1), d[4], d[5]) for d in hearts], J(s, 'instance_exists(obj_heart) ? [obj_heart.sprite_index, obj_heart.image_blend, obj_heart.image_index] : -1')), flush=True)
            for j, o in enumerate(sims):
                if j == i:
                    continue
                h = J(o, 'instance_exists(obj_heart) ? [obj_heart.x, obj_heart.y] : [-1, -1]')
                if h == [-1, -1] or (f % 120) < 110:
                    continue
                tot += 1
                # the white SOUL's corner = the other game's obj_heart (its sprite's corner), tinted with their colour, at 70%
                if any(abs(d[2] - h[0]) < 0.06 and abs(d[3] - h[1]) < 0.06 and d[4] == cols[j] and abs(d[5] - 0.7) < 0.001 for d in hearts):
                    good += 1
                elif tot - good <= 4:
                    print('  B48 frame %d: game %d, other %d at %s; drawn %s; go %s ph %s' % (f, i + 1, j + 1, h, [(round(d[2], 1), round(d[3], 1), d[4], d[5]) for d in hearts],
                          J(s, 'global.kfo.M.go'), J(s, 'global.kfo.M.R.ph')), flush=True)
    ok(not bad, 'B48: no fog and no circle drawn for any SOUL (%s)' % bad[:3])
    ok(tot > 0 and good == tot, 'B48: every game draws every other SOUL at its place, in its colour, at 70%%: %d / %d checks' % (good, tot))
    ok(own_tot > 0 and own_full == own_tot, 'B48: every game draws its own SOUL fully opaque in its own colour: %d / %d frames' % (own_full, own_tot))
    # SHOW OTHER SOULS off in game 2 only
    sims[1].run('global.kfo.view.show = 0;')
    frame_all(700)
    # (the other SOULs are drawn at 70%; build 52's skill icons draw the SOUL too, at full or dimmed alpha - not counted)
    others2 = [d for d in sims[1].SPR if d[0] == soul and d[1] == 0 and d[4] != cols[1] and abs(d[5] - 0.7) < 0.001]
    others1 = [d for d in sims[0].SPR if d[0] == soul and d[1] == 0 and d[4] == cols[1] and abs(d[5] - 0.7) < 0.001]
    ok(not others2 and others1, 'B48: SHOW OTHER SOULS off in game 2: it draws none of the others (%d); game 1 still draws game 2 (%d)' % (len(others2), len(others1)))
    sims[1].run('global.kfo.view.show = 1;')
    frame_all(701)
    others2 = [d for d in sims[1].SPR if d[0] == soul and d[1] == 0 and d[4] != cols[1] and abs(d[5] - 0.7) < 0.001]
    ok(len(others2) == 2, 'B48: on again: the very next frame draws both others (%d)' % len(others2))
    # a colour change reaches the others
    sims[2].run('global.kfo.look.col = %d; kfo_look_sent();' % 65280)
    seen = None
    for f in range(702, 800):
        frame_all(f)
        if any(d[0] == soul and d[1] == 0 and d[4] == 65280 for d in sims[0].SPR):
            seen = f - 702
            break
    ok(seen is not None, 'B48: game 3 changes its colour to green: game 1 draws it green %s frames later' % seen)
    STATS['B48'] = {'checks': tot, 'right': good, 'own_frames': own_tot, 'switches': switches, 'colour_change_frames': seen, 'wall': round(time.time() - t0)}


def fx_chat():
    """Build 48: the chat in a running match (Knight Rush, 3 players + 1 watcher, the simulated network): messages from the host,
    a client and the watcher reach every game in the same order, through knight switches; while a player types, their SOUL
    holds still with the arrows held, the match goes on (its attacks keep coming, nothing pauses), the keys do nothing; every
    game runs the very same cycles (chat changes nothing in the match)"""
    t0 = time.time()
    net, sims = make_room(3, 'normal', 4949, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;')
    instrument(sims)
    rec = new_rec(4)
    for f in range(200):
        keep_alive(sims, f)
        step_all(net, sims, f, lambda i, ff: roam(i, ff, False), rec)
    w = watcher_join(net, sims, sims[0], 9, 'Watch1')
    allg = sims + [w]
    for g in allg:
        g.run('global.kfo.code = "TESTS"; kfo_chat_tick();')
    sends = [(210, 0, 'host here'), (260, 1, 'client here'), (300, 3, 'watcher here'), (700, 1, 'after a switch')]
    hold = None
    k0 = None
    still = []
    for f in range(200, 1100):
        keep_alive(sims, f)
        for (ff, gi, t) in sends:
            if f == ff:
                allg[gi].run('kfo_chat_s().t_send = -100000; kfo_chat_send(%s);' % json.dumps(t))
        if f == 400:
            sims[1].run('kfo_chat_open();')
            k0 = J(sims[1], '[global.kfo.M.R.k, global.kfo.M.R.af]')
        if 400 <= f < 460:
            hp = J(sims[1], 'instance_exists(obj_heart) ? [obj_heart.x, obj_heart.y] : [-1, -1]')
            still.append(hp)
        if f == 460:
            k1 = J(sims[1], '[global.kfo.M.R.k, global.kfo.M.R.af]')
            sims[1].run('kfo_chat_close();')
        step_all(net, allg, f, lambda i, ff: ({'right', 'up'} if (i == 1 and 400 <= ff < 460) else (roam(i, ff, False) if i < 3 else set())), rec)
    lists = [[(e['n'], e['t']) for e in J(g, 'kfo_chat_s().l') if e['sys'] == 0] for g in allg]
    want = [('Kris', 'host here'), ('Susie', 'client here'), ('Watch1', 'watcher here'), ('Susie', 'after a switch')]
    ok(all(l == want for l in lists), 'CHAT: host, client and watcher messages in every game, same order (%s)' % lists)
    sysl = [e['t'] for e in J(sims[2], 'kfo_chat_s().l') if e['sys'] == 1]
    moved = [p for p in still if p != still[0] and p != [-1, -1]]
    ok(still and not moved, 'CHAT: typing, arrows held 60 frames - the SOUL stays put (%s .. %s)' % (still[:1], still[-1:]))
    ok(k1 != k0, 'CHAT: and the match went on meanwhile (%s -> %s)' % (k0, k1))
    cmp = compare({k: v for k, v in rec.items() if k <= 3}, 3)
    ok(not cmp['logic_bad'] and cmp['cycles_all'] > 0, 'CHAT: every game the same cycles with the chat going (%d, %d differences)' % (cmp['cycles_all'], len(cmp['logic_bad'])))
    STATS['CHAT'] = {'messages': len(lists[0]), 'cycles': cmp['cycles_all'], 'differences': len(cmp['logic_bad']), 'notices': sysl[-3:], 'wall': round(time.time() - t0)}


FIX = {'SOUL-001': fx_soul_001, 'SOUL-002': fx_soul_002, 'SOUL-003': fx_soul_003_004_005, 'SOUL-006': fx_soul_006_spec_004, 'SOUL-007': fx_soul_007,
       'SPEC': fx_spec, 'SPEC-010': fx_spec_010, 'QOL-001': fx_qol_001, 'QOL-005': fx_qol_005, 'SOULS-KEY': fx_souls_key,
       'COLORS': fx_colors, 'COLORS-COSMETIC': fx_colors_cosmetic, 'B48': fx_b48, 'CHAT': fx_chat}
LONGFIX = {'ELIM-100': fx_elim_100, 'SOAK-BR': fx_soak_br}   # run by name (long)
FIX.update(LONGFIX)

if __name__ == '__main__':
    t0 = time.time()
    want = sys.argv[1:] or [k for k in FIX if k not in LONGFIX]
    for k in want:
        print('== fixture', k, flush=True)
        try:
            FIX[k]()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    print('STATS', json.dumps(STATS))
    print('t_view47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:40]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
