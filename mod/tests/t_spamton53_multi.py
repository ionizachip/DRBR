"""DRBR: SPAMTON NEO in a room of three games (br_multi: the real code in every game, the simulated network, SOUL / bullet and
shot collisions on). Game 1 plays the yellow SOUL like a person (the shooter of t_spamton53: lines up with his pieces, taps,
then holds for a BIG SHOT), games 2 and 3 never touch a key; the host has one bot. Spamton alone, every phase from the start.
Checked:
  - every game has the same cycles (attack, seed, start tick, stage), no errors, no frame run twice;
  - games 2 and 3 (nobody shoots) see the same attacks: the same bullets at 30 / 60 / 90 frames into every cycle, and each
    attack ends on the same frame of it in both (Chapter 2's own turn timer);
  - game 1's shots are its own: what it breaks never reaches games 2 and 3 (their pieces are the same as each other's), and
    an attack that Chapter 2 lets a good shot end early (the big heart, the face, the pipis) ends earlier in game 1 at least
    once - while games 2 and 3 run it to its end; game 1 then waits for the next shared attack, which starts on the same
    tick in every game;
  - the yellow SOUL in every game during his attacks; the other players' SOULs are drawn yellow (kbr_soul_mode) there;
  - the bot survives his attacks by the odds as well as its dodging (no error in the host's bot code; its walls by the odds).
Usage: python3 t_spamton53_multi.py [frames]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_multi import *
from br_harness import live_input, keys_set
import t_spamton53 as TS

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
net, sims = make_room(3, 'lan', 5363, setx='_s.mhp = 999; _s.hard = 1; _s.ramp = 3;', kn=(9,), open_ok=9, bots=1)
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
        z = 0
        if p['ph'] == 'run':
            RUNF[cid] += 1
            if J(s, 'kbr_sn_yellow_on() && kbr_soul_mode() == "yellow"'):
                YEL[cid] += 1
            if p['k'] not in START[cid]:
                START[cid][p['k']] = f
            if cid == 1:
                TS.aim(s)
                ph = (f - START[cid][p['k']]) % 90
                z = 1 if (ph < 60 and ph % 6 < 2) or (60 <= ph < 89) else 0
        keys_set(s, ok=z)
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
ok(same > 0 and diff == 0, 'games 2 and 3 (nobody shoots) have the same bullets in every cycle (%d same, %d different %r)' % (same, diff, dl[:3]))
print('ends', json.dumps(ENDS), flush=True)
k23 = [k for k in ENDS[2] if k in ENDS[3]]
ok(k23 and all(ENDS[2][k][0] == ENDS[3][k][0] for k in k23), 'games 2 and 3 end every attack on the same frame of it %r' % ([(k, ENDS[2][k], ENDS[3][k]) for k in k23][:6],))
early = [k for k in ENDS[1] if k in ENDS[2] and ENDS[1][k][1] == 'end' and ENDS[1][k][0] + 20 < ENDS[2][k][0]]
ok(len(early) > 0, 'game 1 (shooting) ended at least one attack early, in its own game only %r' % ([(k, ENDS[1][k], ENDS[2][k]) for k in early][:4],))
# the next attack after an early end still starts on the shared tick in every game (the cycles above: t0 the same)
st = {c: {s['k']: s for s in rec[c]['starts']} for c in (1, 2, 3)}
nxt = [k + 1 for k in early if (k + 1) in st[1] and (k + 1) in st[2]]
ok(all(st[1][k]['t0'] == st[2][k]['t0'] for k in nxt) and nxt, 'after its early end game 1 starts the next attack on the same tick (%r)' % (nxt[:4],))
ok(all(YEL[c] >= RUNF[c] * 0.9 for c in (1, 2, 3)), 'the SOUL was yellow in his attacks in every game %r of %r' % (YEL, RUNF))
bot = J(sims[0], '(function(){ var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _p = _h.pl[_i]; if (_p.bot) return [_p.al, _p.hits, _p.hp]; } return []; })()')
ok(bot != [] , 'the host\'s bot played (alive, hits, HP): %r' % (bot,))
print('spamton53 multi: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
