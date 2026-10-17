"""Build 45 (P2 / P3): whole networked matches WITH the battle running. N emulated games (the real fight code, the real
online code) in one room over the simulated network play a match from START to the results. The engine's collisions are
not emulated here, so the SOULs that fall are made to fall (kbr_local_death - what a lethal hit calls) at chosen frames,
now and then two within 5 frames (the tie rule). The winner is a random game (the host or not).
Checked: no error in any game; every game sees the match end and its result box; every game has the very same results
as the host decided them (winner, places, who was alive); the winner is the game that did not fall; places follow the
falls (a later fall never gets a worse place; falls within 10 frames may share a place); the logical agreement of every
cycle all games ran (knight, attack, seed, start tick, the knight before and after - as t_br_multi); no cycle twice.
Usage: python3 t_br_match45.py [games (2)] [profile (normal)] [seed (8001)] [frame cap (9000)]"""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2
PROF = sys.argv[2] if len(sys.argv) > 2 else 'normal'
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 8001
CAP = int(sys.argv[4]) if len(sys.argv) > 4 else 9000
WALL = float(os.environ.get('WALL', '1500'))
t0 = time.time()
R = random.Random(SEED)
net, sims = make_room(N, PROF, SEED, setx='_s.mhp = 200; _s.rush = %d;' % R.choice([0, 1, 2, 3]), netseed=SEED % 97)
winner = R.randint(1, N)
order = [c for c in range(1, N + 1) if c != winner]
R.shuffle(order)
deaths = {}
fd = R.randint(700, 1500)
ties = 0
for j, c in enumerate(order):
    if j > 0:
        if R.random() < 0.25:
            fd += R.randint(1, 5)
            ties += 1
        else:
            fd += R.randint(200, 900)
    deaths[c] = fd
print('room up %.1fs; winner game %d; falls %s' % (time.time() - t0, winner, deaths), flush=True)

rec = {i + 1: {'starts': [], 'snaps': {}, 'errors': []} for i in range(N)}
prev = [state(s) for s in sims]
ended = {}
f = 0
for f in range(CAP):
    net.t += 1000.0 / 30.0
    for i, s in enumerate(sims):
        cid = i + 1
        if rec[cid]['errors']:
            continue
        try:
            s.run('test_net_pump();')
        except Exception as ex:
            rec[cid]['errors'].append([f, 'net', str(ex)[:300]])
            continue
        inputs(s, 'diff', i, prev[i]['af'], prev[i]['ph'])
        err = step(s, 1)
        if err is not None:
            rec[cid]['errors'].append([f, prev[i]['ph'], err[:400]])
            continue
        st = state(s)
        if st['last'] >= 0 and (st['ns'] > prev[i]['ns'] or st['last'] != prev[i]['last']):  # the game keeps only its last 64 starts
            c = s.py(s.eval('kbr_tl_get(global.kfo.M.tl, %d)' % st['last']))
            rec[cid]['starts'].append({'k': st['last'], 'ok': c['ok'], 'ai': c['ai'], 'seed': c['seed'], 't0': c['t0'], 'tw': c['twin'], 'hy': c['hyper'],
                                       'st': c['st'], 'sd': c['sd'], 'ft': c['ft'], 'tsp': round(st['tsp'], 3), 'net_ms': round(net.t, 1), 'act': st['act'],
                                       'prev_act': prev[i]['act']})
        prev[i] = st
        if st['ended'] and cid not in ended:
            ended[cid] = f
    # nobody falls by a hit here (no collisions): HP back to full every second; the planned falls
    if f % 30 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    for c, fr in deaths.items():
        if f == fr and not rec[c]['errors']:
            sims[c - 1].run('kbr_local_death();')
    if len(ended) == N and f > max(ended.values()) + 45:
        break
    if time.time() - t0 > WALL:
        break
rec['frames'] = f + 1
rec['net'] = {'sent': net.sent, 'dropped': net.dropped, 'retrans': net.retrans}
cmp = compare(rec, N)
errs = {c: rec[c]['errors'] for c in range(1, N + 1) if rec[c]['errors']}
res = []
for s in sims:
    res.append(s.py(s.eval('(is_struct(global.kfo.M) && is_struct(global.kfo.M.res)) ? { wn: global.kfo.M.res.wn, wid: global.kfo.M.res.wid, pl: global.kfo.M.res.pl } : undefined')))
box = [bool(s.eval('instance_number(obj_knight_prompt) > 0')) for s in sims]
FAILS = []


def ok(c, m):
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


ok(not errs, 'no error in any game %s' % json.dumps({c: e[:1] for c, e in errs.items()})[:300])
ok(len(ended) == N, 'every game saw the match end (%s)' % ended)
ok(all(box), 'every game shows its result box (%s)' % box)
ok(all(r is not None for r in res) and all(json.dumps(r, sort_keys=True) == json.dumps(res[0], sort_keys=True) for r in res), 'every game has the very same results')
r0 = res[0] or {'pl': [], 'wid': -1}
ok(r0.get('wid') in ([winner], winner), 'the winner is the game that did not fall (wid %s, game %d)' % (r0.get('wid'), winner))
pl = {p['pid']: p['pl'] for p in r0.get('pl', [])}
ok(pl.get(winner) == 1 and len(pl) == N, 'the winner is 1st, everyone placed (%s)' % pl)
bad_order = []
for a in order:
    for b in order:
        if deaths[b] > deaths[a] + 10 and not pl.get(b, 99) < pl.get(a, 0):
            bad_order.append((a, b))
ok(not bad_order, 'places follow the falls (later falls never worse; %s)' % bad_order[:3])
ok(not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] > 0, 'every cycle the same in every game (%d cycles, %s)' % (cmp['cycles_all'], cmp['logic_bad'][:2]))
out = {'args': sys.argv[1:], 'winner': winner, 'deaths': deaths, 'near_ties': ties, 'ended': ended, 'results': res[0], 'cycles_all': cmp['cycles_all'],
       'logic_bad': cmp['logic_bad'], 'dupes': cmp['dupes'], 'onset_ms': cmp['onset_ms'], 'errors': errs, 'net': rec['net'], 'frames': rec['frames'],
       'wall': round(time.time() - t0, 1), 'fails': FAILS, 'pass': not FAILS}
json.dump(out, open('/tmp/claude-0/br45/match_%d_%s_%d.json' % (N, PROF, SEED), 'w'), indent=1)
print('RESULT', 'PASS' if not FAILS else 'FAIL', json.dumps({k: out[k] for k in ('winner', 'deaths', 'near_ties', 'ended', 'cycles_all', 'dupes', 'frames', 'wall', 'net')}),
      'places', pl, flush=True)
sys.exit(1 if FAILS else 0)
