"""DRBR: FLOWERY's sendable skills (ids 38-44) in a room of three games (br_multi: the real code in every game, the simulated
network, collisions and the orange SOUL's own on: collide.py). The match is Flowery alone. The host sends each one at player 2
(TARGETING: CHECK on player 2) while one of his attacks runs there; player 2's orange SOUL never dashes (it takes what comes),
player 3 plays with the DASHER. Checked for each:
  - player 2's game builds it from Flowery's real Chapter 5 pieces (obj_fl_*) on its own board: a send group of that skill that
    made instances, every one of them the host's send aimed at player 2 (its colour, damage, credit), scrolled by the board;
  - player 2 is hit by it (through kbr_dmg_taken, as every send's: the host's credit); the host and player 3 build none of it and
    take no hit from it;
  - when it is over (or the attack is), nothing of it is left in player 2's game; LAST JARONA showed its rainbow charge;
  - no error and no frame run twice in any game.
Then one send at player 2 between two of his attacks: it WAITS (the INCOMING list) and lands at his next attack.
Usage: python3 t_flowery53_send.py [sid ...]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_multi import *
from br_harness import live_input, keys_set
from t_flowery53 import DASHER
import collide
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


NAMES = {38: 'Jarona', 39: 'Bamboo Rush', 40: "Aqua's Knives", 41: "Seth's Books", 42: 'Orange & Green', 43: 'Blue & Yellow', 44: 'Last Jarona'}
want = [int(a) for a in sys.argv[1:]] or sorted(NAMES)
t0 = time.time()
net, sims = make_room(3, 'lan', 5380, setx='_s.mhp = 999; _s.skfam = 3; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25; _s.ramp = 0;', kn=(8,), open_ok=8)
H, C2, C3 = sims
src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
for s in sims:
    live_input(s)
    s.load_source('gml_GlobalScript_t_dasher', DASHER)
    s.load_source('gml_GlobalScript_flsend_wrap', src + '''
function kbr_dmg_taken(_d) { var _f = (variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrf")) ? kbrf : -1;
  var _sid = -1; if (variable_instance_exists(id, "kbrx")) { var _G = kbr_sa_find(kbrx); if (is_struct(_G)) _sid = _G.sid; }
  if (!variable_global_exists("JVH") || !is_array(global.JVH)) global.JVH = [];
  array_push(global.JVH, [_f, _sid, object_get_name(object_index)]); return kbr_dmg_taken__orig(_d); }
''')
    s.run('global.JVH = [];')
TEL = {}


def play():
    keys_set(C2, ok=0, up=0, down=0)
    if J(C3, 'global.kfo.M.R.ph') == 'run':
        w = J(C3, 'kbr_t_dasher()')
        keys_set(C3, ok=w[0], up=w[1], down=w[2])
    else:
        keys_set(C3, ok=0, up=0, down=0)
    keys_set(H, ok=0, up=0, down=0)
    for s in sims:
        s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()]; global.inv = 0;')


def go(n):
    def on_frame(f, sims_, prev):
        play()
    rec = run(net, sims, n, 'none', on_frame=on_frame, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


PIECES = '["obj_fl_jarona","obj_fl_wall","obj_fl_bullet","obj_fl_word","obj_fl_pad","obj_fl_bloom","obj_fl_beam","obj_fl_book","obj_fl_wordflower","obj_fl_mfancy","obj_fl_box"]'
LEFT = ('(function(){ var _n = 0; var _l = %s; for (var _i = 0; _i < array_length(_l); _i++) { with (asset_get_index(_l[_i])) '
        '{ if (variable_instance_exists(id, "kbrx") && kbrx > 0) _n++; } } return _n; })()' % PIECES)
GROUPS = '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch) { var _tk = []; for (var _j = 0; _j < array_length(_G.tel); _j++) array_push(_tk, _G.tel[_j].k); array_push(_o, [_G.gx, _G.made, variable_struct_get_names(_G.seen), _G.t, _tk]); } } return _o; })()'


def send(sid):
    H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
    go(2)
    H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)


def follow(sid, frames=420):
    """frames of the send in player 2's game: what it made, its tags, when it ended"""
    made2, seen2, tagged_ok, gx, t_end, tels = 0, set(), True, None, None, set()
    for f in range(0, frames, 4):
        go(4)
        g = J(C2, GROUPS % sid)
        for gxx, m, names, tt, tk in g:
            gx = gxx
            made2 = max(made2, m)
            seen2 |= set(names)
            tels |= set(tk)
        if gx is not None and not g and t_end is None:
            t_end = f
        bad = J(C2, '(function(){ var _n = 0; with (obj_bulletparent) { if (variable_instance_exists(id, "kbrx") && kbrx > 0 && variable_instance_exists(id, "kbr") && kbr != 0 && (kbrf != %d || kbrt != %d)) _n++; } return _n; })()' % (hostp, p2))
        if bad:
            tagged_ok = False
        if t_end is not None and f > t_end + 12:
            break
    return made2, seen2, tagged_ok, gx, t_end, tels


go(240)
ok(J(H, 'global.kfo.M.go'), 'the match runs')
p2 = J(C2, 'global.kfo.my')
hostp = J(H, 'global.kfo.my')
for sid in want:
    for s in sims:
        s.run('global.JVH = [];')
    # one of his attacks running in player 2's game, with time for the send
    for _ in range(200):
        if J(C2, 'kbr_fl_sa_ready()') and J(C2, '(kbr_tl_get(global.kfo.M.tl, global.kfo.M.R.k).t1 - kbr_now()) > 300'):
            break
        go(5)
    send(sid)
    made2, seen2, tagged_ok, gx, t_end, tels = follow(sid)
    left = J(C2, LEFT)
    other = [J(s, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch && !_G.twin) _n++; } return _n; })()' % sid) for s in (H, C3)]
    hits = {c: J(s, 'global.JVH') for c, s in ((1, H), (2, C2), (3, C3))}
    mine2 = [h for h in hits[2] if h[1] == sid and h[0] == hostp]
    from_host = {c: sum(1 for h in hits[c] if h[0] == hostp) for c in hits}
    nm = NAMES[sid]
    ok(J(H, 'global.U') == 1, '%s: the host sent it' % nm)
    ok(made2 > 0 and any(n.startswith('obj_fl_') for n in seen2), "%s: player 2's game built it from Flowery's pieces (%d made: %s)" % (nm, made2, sorted(seen2)))
    ok(tagged_ok, "%s: every piece of it in player 2's game is the host's send aimed at player 2" % nm)
    ok(len(mine2) > 0, "%s: player 2 was hit by it (%d hits: %s)" % (nm, len(mine2), sorted(set(h[2] for h in mine2))))
    ok(other == [0, 0] and from_host[1] == 0 and from_host[3] == 0, '%s: the host and player 3 build none of it and take no hit from it (groups %r, hits %r)' % (nm, other, [from_host[1], from_host[3]]))
    ok(t_end is not None and left == 0, "%s: it ended (after ~%s frames) and nothing of it is left in player 2's game (%s)" % (nm, t_end, left))
    if sid == 44:
        ok('rainbow' in tels, '%s: its rainbow charge showed %r' % (nm, sorted(tels)))
    for c, s in ((1, H), (2, C2), (3, C3)):
        rl = getattr(s, 'retrylog', [])
        if rl:
            ok(False, '%s: game %d ran every frame once %r' % (nm, c, rl[:2]))
    go(20)
# ---- between two of his attacks: it waits for his next one
for _ in range(400):
    if J(C2, 'global.kfo.M.R.ph') != 'run':
        break
    go(3)
ph0 = J(C2, 'global.kfo.M.R.ph')
send(38)
go(6)
waiting = J(C2, '(function(){ var _l = kbr_incoming_list(global.kfo.M); for (var _i = 0; _i < array_length(_l); _i++) { if (_l[_i].sid == 38 && _l[_i].t < 0) return 1; } return 0; })()')
ok(ph0 != 'run' and waiting == 1, 'between his attacks (%s): JARONA waits in player 2\'s INCOMING list' % ph0)
landed = None
for f in range(0, 900, 5):
    go(5)
    if J(C2, GROUPS % 38):
        landed = f
        break
ok(landed is not None and J(C2, 'kbr_fl_sa_ready() || instance_exists(obj_fl_soul)'), 'it landed when his next attack ran (after %s frames)' % landed)
print('flowery53 send: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
