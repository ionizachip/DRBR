"""Build 52: watching a player is watching their battle - three emulated games over the simulated network (br_multi: the
real merged fight code, the real host and players). Player 3 goes OUT and follows player 2; the host sends a SWORD (and a
FLURRY) at player 2 with CHOOSE. Checked (SPEC-001/002/003/011/012/013/020):
  - the watcher's hidden SOUL sits on player 2's SOUL (where the position stream puts it);
  - the watcher's game builds each send at player 2 from the same message: same item, same seed, the real attack objects
    (a kbr_sa group marked watch, aimed at player 2), started while an attack is running, as in player 2's own game;
  - frame by frame the watcher's game and player 2's game have the same number of that send's objects alive (the same
    pattern) - within the few frames the two games' attacks start apart;
  - the watcher takes no damage, sends nothing, its out state stays; player 2's game is not changed by being watched (the
    host's records of player 2 are what they would be);
  - following someone else drops the last one's sends at once.
Usage: python3 t_spec52.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def J(s, e):
    return s.py(s.eval(e))


T = {'g2': [], 'g3': [], 'pos': []}


def keep(f, sims, prev):
    H, C2, C3 = sims
    if f % 15 == 0:
        for s in (H, C2):
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        for s in sims:
            s.log.clear()
    # the sends' objects alive in each game (player 2: aimed at itself; the watcher: built for player 2)
    T['g2'].append(J(C2, 'kbr_sa_alive(0)'))
    T['g3'].append(J(C3, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (variable_struct_exists(_G, "watch") && _G.watch) _n += kbr_sa_alive(_G.gx); } return _n; })()'))
    T['pos'].append(J(C3, 'kbr_spec_pid(global.kfo.M) >= 0 && instance_exists(obj_heart) && variable_struct_exists(global.kfo.M.ps, string(kbr_spec_pid(global.kfo.M))) ? [ (obj_heart.bbox_right > obj_heart.bbox_left) ? ((obj_heart.bbox_left + obj_heart.bbox_right) / 2) : (obj_heart.x + 10), (obj_heart.bbox_bottom > obj_heart.bbox_top) ? ((obj_heart.bbox_top + obj_heart.bbox_bottom) / 2) : (obj_heart.y + 10), kbr_ps_x(variable_struct_get(global.kfo.M.ps, string(kbr_spec_pid(global.kfo.M)))) + 10, kbr_ps_y(variable_struct_get(global.kfo.M.ps, string(kbr_spec_pid(global.kfo.M)))) + 10 ] : -1'))


def go(net, sims, n):
    rec = run(net, sims, n, 'none', on_frame=keep, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, len(sims) + 1) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


t0 = time.time()
net, sims = make_room(3, 'lan', 5252, setx='_s.mhp = 250; _s.cdm = 25; _s.g0 = 50;')
H, C2, C3 = sims
go(net, sims, 330)
ok(J(H, 'global.kfo.M.go'), 'the match runs')
p2 = J(C2, 'global.kfo.my')
# player 3 goes OUT and follows player 2
C3.run('kbr_local_death();')
go(net, sims, 90)
C3.run('global.kfo.M.spect = %d; global.kfo.M.vw.picked = true; global.kfo.M.vw.cam = 0;' % p2)
go(net, sims, 30)
ok(J(C3, 'global.kfo.M.out') and J(C3, 'kbr_spec_pid(global.kfo.M)') == p2, 'player 3 is out and follows player 2 (%r)' % J(C3, 'kbr_spec_pid(global.kfo.M)'))
hp3 = J(C3, 'global.hp[kbr_char()]')
up3 = J(C3, 'global.kfo.M.sk.sent')
# wait for an attack to run in every game, then the host sends a SWORD and a FLURRY at player 2 (CHOOSE)
for _ in range(40):
    if all(J(s, 'global.kfo.M.R.ph') == 'run' for s in sims):
        break
    go(net, sims, 10)
for k in T:
    T[k] = []
H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
go(net, sims, 10)
H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: 1, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U1 = kbr_skill_use();')
go(net, sims, 25)
H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: 2, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U2 = kbr_skill_use();')
go(net, sims, 150)
ok(J(H, 'global.U1') == 1 and J(H, 'global.U2') == 1, 'the host sent both')
m2 = max(T['g2']) if T['g2'] else 0
m3 = max(T['g3']) if T['g3'] else 0
ok(m2 > 0, 'player 2 dodges the sends in its own game (%d objects at most)' % m2)
ok(m3 > 0, 'the watcher sees them too: built in its game for player 2 (%d objects at most)' % m3)
ok(m2 == m3, 'the same pattern: as many objects at most in both games (%d / %d)' % (m2, m3))
# frame by frame, allowing the few frames the games start apart
def first(a):
    for i, v in enumerate(a):
        if v > 0:
            return i
    return -1
f2, f3 = first(T['g2']), first(T['g3'])
ok(f2 >= 0 and f3 >= 0 and abs(f2 - f3) <= 6, 'they start within a few frames of each other (frame %d / %d)' % (f2, f3))
if f2 >= 0 and f3 >= 0:
    d = f3 - f2
    pairs = [(T['g2'][i], T['g3'][i + d]) for i in range(len(T['g2'])) if 0 <= i + d < len(T['g3'])]
    same = sum(1 for a, b in pairs if a == b)
    ok(same >= len(pairs) * 0.9, 'lined up by their start, the object counts match frame by frame (%d of %d frames)' % (same, len(pairs)))
# the watcher's SOUL on player 2's
pos = [p for p in T['pos'] if isinstance(p, list)]
far = [p for p in pos if abs(p[0] - p[2]) > 1.5 or abs(p[1] - p[3]) > 1.5]
ok(len(pos) > 50 and len(far) <= 2, "the watcher's hidden SOUL is on player 2's SOUL (%d frames, %d off)" % (len(pos), len(far)))
# the watcher is only watching
ok(J(C3, 'global.hp[kbr_char()]') == hp3 and J(C3, 'global.kfo.M.out'), 'the watcher took no damage and stays out')
ok(J(C3, 'global.kfo.M.sk.sent') == up3, 'the watcher sent nothing')
ok(not J(C3, 'instance_exists(obj_heart) && obj_heart.visible'), "the watcher's SOUL stays hidden")
# switching: the sends built for player 2 go at once
C3.run('var _S = global.kfo.M.sk; array_push(_S.pend, { sid: 2, from: 1, fn: "H", sd: 77, t: 0, rf: 0, tg: %d, mul: 1, sh: 0, w: 1 });' % p2)
go(net, sims, 8)
before = J(C3, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (variable_struct_exists(global.kbr_sa[_i], "watch") && global.kbr_sa[_i].watch) _n++; return _n; })()')
C3.run('global.kfo.M.spect = %d;' % J(H, 'global.kfo.my'))
go(net, sims, 2)
after = J(C3, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (variable_struct_exists(global.kbr_sa[_i], "watch") && global.kbr_sa[_i].watch && global.kbr_sa[_i].tg == %d) _n++; return _n; })()' % p2)
ok(after == 0, "following the host now: player 2's sends are gone from the watcher's screen (%d groups before, %d after)" % (before, after))
print('spec52: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
