"""Build 45: the shared battle in several games at once (br_multi.py). Usage:
  python3 t_br_multi.py [games] [frames] [profile] [input same|diff|none] [rush] [seed]
Writes /tmp/claude-0/br45/multi_<...>.json and prints PASS / FAIL on the logical agreement (every game: the same knight,
attack, seed, start tick, extras and switch sequence for every cycle; no cycle twice) with the presentation numbers."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
FR = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
PROF = sys.argv[3] if len(sys.argv) > 3 else 'lan'
MODE = sys.argv[4] if len(sys.argv) > 4 else 'same'
RUSH = int(sys.argv[5]) if len(sys.argv) > 5 else 1
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 4242
WALL = float(os.environ.get('WALL', '1500'))

t0 = time.time()
net, sims = make_room(N, PROF, SEED, setx='_s.rush = %d; _s.mhp = 300;' % RUSH)
print('room up', round(time.time() - t0, 1), 's; start:', sims[0].eval('global.BRWHY') or 'ok', flush=True)

# nobody dies in this test: HP back to full every second (the outs have their own test)
def keep(f, sims, prev):
    if f % 30 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    if f % 300 == 0:
        # the emulator's own record of mocked calls (sim.log) is not needed here and grows without end: cleared (long runs)
        for s in sims:
            s.log.clear()
        print('frame', f, [(p['ph'], p['k'], round(p['now'], 1)) for p in prev], '%.0fs' % (time.time() - t0), flush=True)

# lag spikes: STALL="cid:frame:len,..." - that game gets no frame for len frames (its clock runs on)
stalls = []
for s in filter(None, os.environ.get('STALL', '').split(',')):
    c, fr, ln = (int(x) for x in s.split(':'))
    stalls.append((c, fr, ln))
def stall(cid, f):
    return any(c == cid and fr <= f < fr + ln for c, fr, ln in stalls)
# clock rates: DRIFT="cid:rate,..." (1.001 = that computer's clock runs 0.1% fast)
for s in filter(None, os.environ.get('DRIFT', '').split(',')):
    c, r = s.split(':')
    sims[int(c) - 1].ct_rate = float(r)
rec = run(net, sims, FR, MODE, on_frame=keep, wall=WALL, stall=stall if stalls else None)
cmp = compare(rec, N)
errs = {c: rec[c]['errors'] for c in range(1, N + 1) if rec[c]['errors']}
skips = [sims[i].eval('global.kfo.M.R.skipped') for i in range(N)]
resyncs = [sims[i].eval('global.kfo.M.resyncs') for i in range(N)]
H = sims[0]
hostc = {'desyncs': H.eval('global.kfo.H.desyncs'), 'clockfix': H.eval('global.kfo.H.clockfix'), 'fixes': H.eval('global.kfo.H.fixes'),
         'bc_same': H.eval('global.kfo.H.bc_same'), 'bc_diff': H.eval('global.kfo.H.bc_diff')}
res = {'args': sys.argv[1:], 'cmp': cmp, 'errors': errs, 'skipped': skips, 'resyncs': resyncs, 'host': hostc, 'net': rec['net'], 'frames': rec['frames'],
       'wall': round(time.time() - t0, 1), 'starts': {c: rec[c]['starts'] for c in range(1, N + 1)}}
ok = not errs and not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] > 0 and not cmp['arena_bad']
res['pass'] = ok
out = '/tmp/claude-0/br45/multi_%d_%s_%s_%d_%d%s.json' % (N, PROF, MODE, RUSH, SEED, os.environ.get('TAG', ''))
json.dump(res, open(out, 'w'), indent=1)
print('RESULT', 'PASS' if ok else 'FAIL', 'cycles(all games)', cmp['cycles_all'], 'logic_bad', cmp['logic_bad'][:4], 'dupes', cmp['dupes'],
      'onset p95/max ms', cmp['onset_p95'], cmp['onset_max'], 'arena_bad', len(cmp['arena_bad']), 'bullets same/diff', cmp['bul_same'], cmp['bul_diff'],
      'skipped', skips, 'resyncs', resyncs, 'host', hostc, 'errors', {c: e[:1] for c, e in errs.items()}, 'net', rec['net'], 'wall', res['wall'], flush=True)
sys.exit(0 if ok else 1)  # build 46: a FAIL is a failing exit code too (runall)
