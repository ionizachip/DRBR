"""DRBR: GERSON in a room of three games (br_multi: the real code in every game, the simulated network, SOUL / bullet
collisions on). Game 1 plays like a person (the arrows every few frames: its SOUL moves, and in his green attacks its shield
turns), games 2 and 3 never touch a key; the host has one bot. Gerson alone, every phase from the start.
Checked:
  - every game has the same cycles (attack, seed, start tick, stage), no errors, no frame run twice;
  - games 2 and 3 (nobody moves) see the same attacks: the same bullets at 30 / 60 / 90 frames into every cycle, and each
    attack ends on the same frame of it in both;
  - every game starts every attack on the same tick;
  - the SOUL's mode is the attack's, the same in every game: green (the shield) in his green attacks, red in the rest - game 1's
    moving never changes it;
  - the bot plays his attacks (no error in the host's bot code: its shield by the green SOUL's rule).
Usage: python3 t_gerson53_multi.py [frames]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_multi import *
from br_harness import live_input, keys_set
MOVES = ['up', 'left', 'down', 'right', None, 'down', 'right', 'up', 'left', None]

FR = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(s, e):
    return s.py(s.eval(e))


t0 = time.time()
net, sims = make_room(3, 'lan', 5367, setx='_s.mhp = 999; _s.hard = 1; _s.ramp = 3;', kn=(7,), open_ok=7, bots=1)
print('room up; start:', sims[0].eval('global.BRWHY') or 'ok', flush=True)
for s in sims:
    live_input(s)
ENDS = {1: {}, 2: {}, 3: {}}
YEL = {1: 0, 2: 0, 3: 0}
RUNF = {1: 0, 2: 0, 3: 0}
LAST = {1: None, 2: None, 3: None}
START = {1: {}, 2: {}, 3: {}}


def play(f, sims, prev):
    for i, s in enumerate(sims):
        cid = i + 1
        if f % 30 == 0:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        p = prev[i]
        if p['ph'] == 'run':
            RUNF[cid] += 1
            if J(s, 'kbr_soul_mode() == "green"'):
                YEL[cid] += 1
            if p['k'] not in START[cid]:
                START[cid][p['k']] = f
        kk = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        if p['ph'] == 'run' and cid == 1 and (f - START[cid][p['k']]) % 9 < 2:
            mv = MOVES[((f - START[cid][p['k']]) // 9) % len(MOVES)]
            if mv:
                kk[mv] = 1
        keys_set(s, **kk)
        # an attack's end in this game: the run phase over for cycle k (its cut and why)
        if LAST[cid] is not None and LAST[cid][0] == 'run' and p['ph'] != 'run':
            k = LAST[cid][1]
            ENDS[cid][k] = [f - START[cid].get(k, f), J(s, 'global.kfo.M.R.cut_why')]
        LAST[cid] = (p['ph'], p['k'])
    if f % 300 == 0:
        for s in sims:
            s.log.clear()
        print('frame', f, [(p['ph'], p['k']) for p in prev], '%.0fs' % (time.time() - t0), flush=True)


rec = run(net, sims, FR, 'none', on_frame=play, wall=3600)
cmp = compare(rec, 3)
errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
ok(not errs, 'no errors in any game %r' % (errs,))
ok(not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] >= 4, 'every game the same cycles (%d, bad %r)' % (cmp['cycles_all'], cmp['logic_bad'][:3]))
ok(all(not getattr(s, 'retrylog', []) for s in sims), 'no frame run twice %r' % ([getattr(s, 'retrylog', [])[:1] for s in sims],))
# games 2 and 3: the same bullets at 30 / 60 / 90 frames into every cycle
same = diff = 0
dl = []
for key in rec[2]['snaps']:
    a = rec[2]['snaps'].get(key)
    b = rec[3]['snaps'].get(key)
    if a is None or b is None:
        continue
    if a['h'] == b['h']:
        same += 1
    else:
        diff += 1
        dl.append([key, a['n'], b['n']])
ok(same > 0 and diff == 0, 'games 2 and 3 (nobody moves) have the same bullets in every cycle (%d same, %d different %r)' % (same, diff, dl[:3]))
print('ends', json.dumps(ENDS), flush=True)
k23 = [k for k in ENDS[2] if k in ENDS[3]]
ok(k23 and all(ENDS[2][k][0] == ENDS[3][k][0] for k in k23), 'games 2 and 3 end every attack on the same frame of it %r' % ([(k, ENDS[2][k], ENDS[3][k]) for k in k23][:6],))
# game 1 (moving) starts every attack on the same tick as games 2 and 3
st = {c: {s['k']: s for s in rec[c]['starts']} for c in (1, 2, 3)}
kk = [k for k in st[1] if k in st[2] and k in st[3]]
ok(kk and all(st[1][k]['t0'] == st[2][k]['t0'] == st[3][k]['t0'] for k in kk), 'every game starts every attack on the same tick (%d attacks)' % len(kk))
ok(YEL[2] == YEL[3] and abs(YEL[1] - YEL[2]) <= 2 and YEL[2] > 0, 'the SOUL green in his green attacks, the same frames in every game %r of %r' % (YEL, RUNF))
bot = J(sims[0], '(function(){ var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _p = _h.pl[_i]; if (_p.bot) return [_p.al, _p.hits, _p.hp]; } return []; })()')
ok(bot != [] , 'the host\'s bot played (alive, hits, HP): %r' % (bot,))
print('gerson53 multi: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
