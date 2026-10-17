"""DRBR: PINK's sends leave a way out (the "dodgeable and fair" rule for outgoing attacks): each of her sends (ids 51-56) at
player 2 of a room of three games (br_multi: the real code in every game, the simulated network, SOUL / bullet collisions on),
player 2's SOUL red (a knight's attack running in its game), and player 2 a CAREFUL player - it moves its SOUL the way the send
tells it to (by the send's own telegraphs: where the rows / columns are, where the bombs fly to), as a person would:
  51 KITTY PARADE   half a row (28 px) off its row: between the cat rows
  52 KITTY RAIN     60 px to the side of its column (past the falling cats either side)
  53 HEART SHOTS    after each volley is fired (12 frames on, once the volley before has passed), 26 px across it: between
                    the middle bullet and the lanes beside it
  54 FUSE BOMBS     the box corner away from the bombs' rows and columns
  55 MEGA BOMB      the box corner (its warning bands leave the corners)
  56 ENCORE         keeps moving round the box's middle (the hearts turn to aim before they fly; a moving SOUL leaves them
                    behind): no fixed spot is safe, so this one is checked for being dodged LESS than it is hit by a careless
                    player (t_pink53_send.py) - it must not be unavoidable
Checked for 51-55: the careful SOUL takes NO hit from the send (and the send ran: it made its pieces). 56: fewer hits than
t_pink53_send.py's careless player took (34 at seed 5351) and at least one heart / bar it was aimed by missed.
Usage: python3 t_pink53_fair.py [sid ...]"""
import sys, os, json, time, math
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_multi import *
import collide
import bbox_model as BM
import t_view47

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)


def J(s, e):
    return s.py(s.eval(e))


NAMES = {51: 'Kitty Parade', 52: 'Kitty Rain', 53: 'Heart Shots', 54: 'Fuse Bombs', 55: 'Mega Bomb', 56: 'Encore'}
want = [int(a) for a in sys.argv[1:]] or sorted(NAMES)
t0 = time.time()
net, sims = make_room(3, 'lan', 5352, setx='_s.mhp = 999; _s.skfam = 6; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25;', kn=(0,), open_ok=0)
H, C2, C3 = sims
src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
for s in sims:
    s.load_source('gml_GlobalScript_pkfair_wrap', src + '''
function kbr_dmg_taken(_d) { var _f = (variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrf")) ? kbrf : -1;
  var _sid = -1; if (variable_instance_exists(id, "kbrx")) { var _G = kbr_sa_find(kbrx); if (is_struct(_G)) _sid = _G.sid; }
  if (!variable_global_exists("JVH") || !is_array(global.JVH)) global.JVH = [];
  array_push(global.JVH, [_f, _sid, object_get_name(object_index)]); return kbr_dmg_taken__orig(_d); }
''')
    s.run('global.JVH = [];')


def go(n, on=None):
    def on_frame(f, sims_, prev):
        if on is not None:
            on()
    rec = run(net, sims, n, 'none', on_frame=on_frame, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


def keep_hp():
    for s in sims:
        s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')


def heart(sim):
    hs = [i for i in (sim.instances_of('obj_heart') if 'obj_heart' in sim.objects else []) if not i.dead]
    return hs[0] if hs else None


def place(sim, cx, cy):
    """the SOUL's mask's middle at (cx, cy)"""
    h = heart(sim)
    if h is None:
        return
    hb = BM.box_of(sim, h)
    if hb is None:
        return
    hx, hy = (hb[0] + hb[2]) / 2.0, (hb[1] + hb[3]) / 2.0
    h.vars['x'] = float(h.vars.get('x', 0)) + (cx - hx)
    h.vars['y'] = float(h.vars.get('y', 0)) + (cy - hy)


def soul_mid(sim):
    h = heart(sim)
    hb = BM.box_of(sim, h) if h is not None else None
    return ((hb[0] + hb[2]) / 2.0, (hb[1] + hb[3]) / 2.0) if hb else None


go(300)
ok(J(H, 'global.M.go') if False else J(H, 'global.kfo.M.go'), 'the match runs')
p2 = J(C2, 'global.kfo.my')
hostp = J(H, 'global.kfo.my')
for sid in want:
    for s in sims:
        s.run('global.JVH = [];')
    # a knight's attack running in player 2's game (its SOUL red, free to move)
    for _ in range(80):
        if J(C2, 'global.kfo.M.R.ph') == 'run' and J(C2, 'instance_exists(obj_growtangle) && obj_growtangle.x > -1000 && !kbr_pk_purple_on()') and J(C2, 'global.kfo.M.R.af') < 20:
            break
        go(5)
    B0 = J(C2, 'kbr_sa_box()')
    S0 = soul_mid(C2)
    H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
    go(2)
    H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
    st = {'tgt': None, 'moves': 0, 'last': -99, 'axis': None, 'g': None, 'made': 0, 'seen': set(), 'enc_t': 0}
    lx, hx = B0[0] - B0[2] + 12, B0[0] + B0[2] - 12
    ly, hy = B0[1] - B0[3] + 12, B0[1] + B0[3] - 12

    def towards_mid(v, lo, hi, d):
        return d if (v + d <= hi and (v + d - (lo + hi) / 2.0) ** 2 <= (v - d - (lo + hi) / 2.0) ** 2) or v - d < lo else -d

    def careful():
        C2.run('global.inv = 0;')
        g = J(C2, '(function(){ for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch) return [_G.t, _G.made, variable_struct_get_names(_G.seen), _G.gx]; } return []; })()' % sid)
        if g:
            st['g'] = g
            st['made'] = max(st['made'], g[1])
            st['seen'] |= set(g[2])
        t = g[0] if g else None
        s0x, s0y = S0
        if st['tgt'] is None:
            if sid == 51:
                st['tgt'] = (s0x, s0y + (28 if s0y + 28 <= hy else -28))
            elif sid == 52:
                st['tgt'] = (s0x + (60 if s0x + 60 <= hx else -60), s0y)
            elif sid in (54, 55):
                st['tgt'] = (lx + 2, ly + 2)
            else:
                st['tgt'] = (s0x, s0y)
        if sid in (54, 55) and g:
            # the corner farthest from every bomb's row and column (they are shown as they fly)
            dl = J(C2, '(function(){ var _o = []; with (%s) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_o, [dest_x, dest_y]); } return _o; })()' % ('obj_pk_bomb' if sid == 54 else 'obj_pk_bigbomb'))
            if dl:
                best = None
                for cx in (lx + 2, hx - 2):
                    for cy in (ly + 2, hy - 2):
                        m = min([abs(cx - d[0]) for d in dl] + [abs(cy - d[1]) for d in dl])
                        if best is None or m > best[0]:
                            best = (m, (cx, cy))
                st['tgt'] = best[1]
        if sid == 53 and t is not None:
            # each volley fires at t = 10, 30, 50, 70, 90 along 180, 270, 0, 90, 180: 12 frames after, 26 px across it
            for k, d in enumerate((180, 270, 0, 90, 180)):
                if t == 10 + 20 * k + 12 and st['last'] != k:
                    st['last'] = k
                    cx, cy = soul_mid(C2)
                    if d in (0, 180):
                        cy += towards_mid(cy, ly, hy, 26)
                    else:
                        cx += towards_mid(cx, lx, hx, 26)
                    st['tgt'] = (cx, cy)
        if sid == 56:
            # round the box's middle, 40 px out, a turn every 48 frames
            st['n'] = st.get('n', 0) + 1
            a = (st['n'] % 48) / 48.0 * 2 * math.pi
            st['tgt'] = (B0[0] + 40 * math.cos(a), B0[1] + 40 * math.sin(a))
        # (the send fixes its rows / columns / landing spots at its start, round where the SOUL is then: a careful player only
        # moves once it has - the telegraphs show them)
        if t is None or t < {51: 1, 52: 1, 53: 0, 54: 7, 55: 11, 56: 0}[sid]:
            place(C2, s0x, s0y)
            return
        place(C2, st['tgt'][0], st['tgt'][1])
    t_end = None
    for f in range(0, 680, 4):
        go(4, careful)
        keep_hp()
        gg = J(C2, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch) _n++; } return _n; })()' % sid)
        if st['g'] is not None and gg == 0 and t_end is None:
            t_end = f
        if t_end is not None and f > t_end + 12:
            break
    hits = [h for h in J(C2, 'global.JVH') if h[1] == sid and h[0] == hostp]
    ok(J(H, 'global.U') == 1 and st['made'] > 0, '%s: sent, and player 2\'s game made it (%d pieces: %s)' % (NAMES[sid], st['made'], sorted(st['seen'])))
    ok(t_end is not None, '%s: it ended (~%s frames)' % (NAMES[sid], t_end))
    if sid in (54, 55):
        ok('obj_pk_boom' in st['seen'], '%s: its bombs went off (%s)' % (NAMES[sid], sorted(st['seen'])))
    if sid == 56:
        ok(len(hits) < 34, '%s: a SOUL that keeps moving is hit less than a careless one (%d hits < 34: %s)' % (NAMES[sid], len(hits), sorted(set(h[2] for h in hits))))
    else:
        ok(hits == [], '%s: a careful SOUL (%s) is never hit by it %r' % (NAMES[sid], 'box %r, SOUL %r -> %r' % (B0, [round(v) for v in S0], [round(v) for v in st['tgt']]), hits[:4]))
    for c, s in ((1, H), (2, C2), (3, C3)):
        rl = getattr(s, 'retrylog', [])
        if rl:
            ok(False, '%s: game %d ran every frame once %r' % (NAMES[sid], c, rl[:2]))
    go(30)
print('pink53 fair: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
