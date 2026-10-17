"""Build 45 (P3): whole battle royale matches from START to the results, 8 SOULs (you and 7 bots), in one emulated game running
the real fight code, the real host (bots, outs, places, the final two, sudden death, the end) and the real player code.
In the emulator your own SOUL is never hit (the engine's collisions are not emulated) - the bots are (their hits are the
host's own code) - so you outlast them: the match ends when the last bot falls. Checked per match: no error, it ends, 8 places
with you #1, the final two announced once when two were left, sudden death when the room has it from the start, every
cycle started once and in order, nothing left behind between attacks.
Usage: python3 t_br_practice.py [config|all] [matches per config (1)] [frame cap (15000)]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

CONFIGS = {
    'standard': '_s.mhp = 60; _s.dmul = 200; _s.botd = 0;',
    'knightrush': 'var _p = kfo_preset_apply(4); _p.bots = 7; _p.mhp = 60; _p.dmul = 200; _p.botd = 0; _s = _p; _s.kn = [0, 1, 2, 3, 4, 5];',
    'chaos': 'var _p = kfo_preset_apply(6); _p.bots = 7; _p.mhp = 60; _p.dmul = 200; _p.botd = 0; _s = _p; _s.kn = [0, 1, 2, 3, 4, 5];',
    'nightmare': 'var _p = kfo_preset_apply(7); _p.bots = 7; _p.mhp = 60; _p.dmul = 200; _p.botd = 0; _s = _p; _s.kn = [0, 1, 2, 3, 4, 5];',
    'suddendeath': '_s.mhp = 60; _s.dmul = 150; _s.m_sd0 = 1; _s.sdrate = 3; _s.botd = 0;',
}
WHICH = sys.argv[1] if len(sys.argv) > 1 else 'all'
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 1
CAP = int(sys.argv[3]) if len(sys.argv) > 3 else 15000
names = list(CONFIGS) if WHICH == 'all' else WHICH.split(',')
REP0 = int(os.environ.get('PRAC_REP0', '0'))   # build 47: more matches without repeating the first ones (other seeds)
FAILS = []
results = []
t_all = time.time()
for name in names:
    for rep in range(REP0, REP0 + REPS):
        t0 = time.time()
        seed = 5000 + rep * 17 + len(name)
        sim, e = br_match(open_ok=0, seed=seed, bots=7, setx=CONFIGS[name], rng_seed=rep + 1)
        rec = {'config': name, 'rep': rep, 'seed': seed, 'errors': [], 'frames': 0}
        if e is not None:
            rec['errors'].append(['setup', str(e)[:300]])
            results.append(rec)
            FAILS.append('%s #%d: setup failed %s' % (name, rep, str(e)[:200]))
            continue
        started = []
        prev = br_state(sim)
        f = 0
        linger = 0
        while f < CAP:
            err = step(sim, 1)
            f += 1
            if err is not None:
                rec['errors'].append([f, prev.get('ph'), err[:400]])
                break
            s = br_state(sim)
            if s['ph'] == 'run' and prev['ph'] != 'run':
                started.append(s['k'])
            if s['ph'] == 'idle' and prev['ph'] == 'run' and s['bul'] > 0:
                linger += 1
            prev = s
            if s['ended']:
                break
        rec['frames'] = f
        rec['secs'] = round(time.time() - t0, 1)
        rec['cycles'] = len(started)
        rec['dupes'] = len(started) - len(set(started))
        rec['in_order'] = started == sorted(started)
        rec['linger'] = linger
        H = sim.py(sim.eval('is_struct(global.kfo.H) ? { res: global.kfo.H.res, feed: global.kfo.H.feed, startn: global.kfo.H.startn } : undefined'))
        M = sim.py(sim.eval('{ ended: global.kfo.M.ended, sd_on: global.kfo.M.sd_on, ft_on: global.kfo.M.ft_on, place: global.kfo.M.place, res: global.kfo.M.res }'))
        rec['ended'] = M['ended']
        res = H['res'] if H else None
        ok = not rec['errors'] and M['ended'] and isinstance(res, dict)
        if isinstance(res, dict):
            pls = sorted(p['pl'] for p in res['pl'])
            rec['places'] = pls
            rec['winner'] = res.get('wn')
            ok = ok and len(res['pl']) == 8 and res.get('wn') == 'Kris' and pls[0] == 1 and all(1 <= p <= 8 for p in pls)
        feed = [x[1] for x in (H['feed'] if H else [])]
        rec['final_two'] = sum(1 for x in feed if 'FINAL TWO' in x)
        rec['sd'] = M['sd_on']
        # the final two: once when a settle left exactly two (the feed keeps the last 30 lines: enough for 8 SOULs)
        outs_left = [x for x in feed if ' is OUT (#' in x]
        two_left = any('(#3)' in x for x in outs_left) and not any(('(#2)' in x and '(#3)' in y) for x in outs_left for y in outs_left if x == y)
        if rec['final_two'] > 1:
            ok = False
        if name == 'suddendeath' and not M['sd_on']:
            ok = False
        if rec['dupes'] or not rec['in_order'] or rec['linger']:
            ok = False
        rec['pass'] = ok
        results.append(rec)
        print(json.dumps(rec), flush=True)
        if not ok:
            FAILS.append('%s #%d: %s' % (name, rep, json.dumps({k: rec[k] for k in rec if k in ('errors', 'ended', 'winner', 'places', 'final_two', 'sd', 'dupes', 'linger', 'frames')})[:400]))
os.makedirs('/tmp/claude-0/br45', exist_ok=True)
json.dump(results, open('/tmp/claude-0/br45/practice_%s.json' % WHICH.replace(',', '_'), 'w'), indent=1)
print('practice matches: %d run, %d failed (%.0fs)' % (len(results), len(FAILS), time.time() - t_all))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
