"""Build 50: why a player went out - kept on the match, shown on the results, sent to the host, written to knightfights_debug.log."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *
FAILS = []
def ok(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: FAILS.append(m)
sim, e = br_match(seed=99, bots=1, skin=4, kn=[0], setx='_s.mhp = 300;', rng_seed=3)
ok(e is None, 'match set up')
for _ in range(400):
    step(sim, 1)
logs = []
sim.mock('kh_dbg_write', lambda s, l: logs.append(s.py(l)) or 1)
sent = []
sim.mock('kfo_up', lambda s, m: sent.append(s.py(m)) or 1)
sim.run('knight_battle_won();')
M = sim.py(sim.eval('{ out: global.kfo.M.out, why: global.kfo.M.out_why }'))
ok(M['out'], 'the battle ending on its own puts you OUT (as before)')
ok('win check' in M['why'], 'and says why: %r' % M['why'])
outs = [m for m in sent if isinstance(m, dict) and m.get('k') == 'out']
ok(outs and 'win check' in outs[-1].get('why', ''), 'the host is told why %r' % outs[-1:])
ok(logs and any('OUT:' in l for l in logs[-1]), 'the log gets the OUT block %r' % (logs[-1][:2] if logs else None))
ok(logs and any('party:' in l for l in logs[-1]) and any('battlecontroller' in l or 'no battlecontroller' in l for l in logs[-1]), 'with the party HP and the battle state')
sim.run('global.kfo.M.res = { pl: [ { pl: 1, n: "Lancer", al: 1, sg: 7, pid: 2 }, { pl: 2, n: "Imperfect", al: 0, ft: 3690, sg: 11, pid: global.kfo.my } ], wid: [2], wn: "Lancer", sn: 2 };')
L = sim.py(sim.eval('kfo_result_lines()'))
ok(any(isinstance(x, list) and x[0] == '~' and 'You went out' in x[1] for x in L), 'the results show it %r' % L[-1:])
print('%d failed' % len(FAILS))
sys.exit(1 if FAILS else 0)
