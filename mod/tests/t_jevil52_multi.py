"""Build 52: JEVIL in a room of several games (br_multi: the real code in every game, the simulated network). Every game must have
the same cycles (Jevil or a knight, attack, seed, start tick, stage, the switches) and - the players' SOULs moved the same way -
the same bullets of the shared attack in the same places 30, 60 and 90 frames into each attack.
Usage: python3 t_jevil52_multi.py [games] [frames] [kn: jevil | mix]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
FR = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
KIND = sys.argv[3] if len(sys.argv) > 3 else 'jevil'
kn = (6,) if KIND == 'jevil' else (0, 6)
t0 = time.time()
net, sims = make_room(N, 'lan', 5252, setx='_s.rush = 1; _s.mhp = 300; _s.hard = 1;', kn=kn, open_ok=kn[0])
print('room up; start:', sims[0].eval('global.BRWHY') or 'ok', flush=True)


def keep(f, sims, prev):
    if f % 30 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    if f % 300 == 0:
        for s in sims:
            s.log.clear()
        print('frame', f, [(p['ph'], p['k']) for p in prev], '%.0fs' % (time.time() - t0), flush=True)


rec = run(net, sims, FR, 'same', on_frame=keep, wall=3000)
cmp = compare(rec, N)
errs = {c: rec[c]['errors'][:1] for c in range(1, N + 1) if rec[c]['errors']}
jv = sum(1 for s in rec[1]['starts'] if s['ok'] == 6)
ok = not errs and not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] > 0 and not cmp['arena_bad'] and jv > 0 and cmp['bul_diff'] == 0
json.dump({'cmp': cmp, 'errors': errs, 'starts': rec[1]['starts']}, open('/home/claude/work/online/jevil_multi_%d_%s.json' % (N, KIND), 'w'), indent=1)
print('RESULT', 'PASS' if ok else 'FAIL', 'games', N, KIND, 'cycles(all games)', cmp['cycles_all'], 'Jevil cycles', jv, 'logic_bad', cmp['logic_bad'][:4], 'dupes', cmp['dupes'],
      'arena_bad', len(cmp['arena_bad']), 'bullets same/diff', cmp['bul_same'], cmp['bul_diff'], 'onset max ms', cmp['onset_max'], 'errors', errs,
      'wall', round(time.time() - t0), flush=True)
if cmp['bul_diff_list']:
    print('first bullet difference', json.dumps(cmp['bul_diff_list'][0])[:600])
sys.exit(0 if ok else 1)
