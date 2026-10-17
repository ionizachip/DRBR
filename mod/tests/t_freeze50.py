"""Build 50: the hub's pause (knight_freeze / knight_unfreeze) in a single fight (no Tag Team): only what was running comes
back - something the game itself had switched off (a cutscene's followers) stays off. (The crash: obj_caterpillarchara woken
by a pause with no obj_mainchara to follow.)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lu_harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
sim, e = lu_battle('base', combo=0, world=True)
ok(e is None, 'battle set up (%s)' % e)
frames(sim, 2)
ok(not sim.eval('global.knight_lu_inroom'), 'a single fight (no lineup in the room)')
sim.run('global.CAT = instance_create(10, 10, obj_marker); global.RUN = instance_create(20, 20, obj_marker); instance_deactivate_object(global.CAT);')
cat = sim.eval('global.CAT'); run = sim.eval('global.RUN')
sim.run('knight_freeze();'); sim.step(1)
ok(sim.eval('instance_exists(global.K)') is False or sim.eval('instance_exists(global.K)') == 0, 'paused: the knight is off')
ok(sim.eval('instance_exists(%d)' % run) in (False, 0), 'paused: what was running is off')
sim.run('knight_unfreeze();'); sim.step(1)
ok(sim.eval('instance_exists(global.K)') in (True, 1), 'after the pause: the knight is back')
ok(sim.eval('instance_exists(%d)' % run) in (True, 1), 'after the pause: what was running is back')
ok(cat in sim.deact, 'after the pause: what the game had switched off itself stays off')
ok(not sim.eval('global.knight_frozen'), 'not frozen any more')
print('freeze50 tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
