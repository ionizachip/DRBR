"""Build 50: SOLO in a hub fight - the member is made at the encounter's middle place (level with the knight), not the top one;
parties of 2 and 3 keep their places."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lu_harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
for host, party in (('base', (1, 0, 0)), ('kaizo', (2, 0, 0)), ('violet', (4, 0, 0)), ('base', (1, 2, 0)), ('base', (1, 2, 3))):
    sim, e = lu_battle(host, party=party, combo=0, world=True)
    ok(e is None, '%s %s: battle set up (%s)' % (host, party, e))
    if e:
        continue
    sim.run('global.HMX = [100, 80, 58]; global.HMY = [104, 142, 190]; global.heromakex = [100, 80, 58]; global.heromakey = [104, 142, 190];'
            'global.char = [%d, %d, %d]; global.LU = knight_solo_lineup();' % party)
    hx = [sim.eval('global.heromakex[%d]' % i) for i in range(3)]
    hy = [sim.eval('global.heromakey[%d]' % i) for i in range(3)]
    if sum(1 for c in party if c) == 1:
        ok((hx[0], hy[0]) == (80, 142), '%s %s: solo - made at the middle place, level with the knight %r' % (host, party, (hx[0], hy[0])))
    else:
        ok(hx == [100, 80, 58] and hy == [104, 142, 190], '%s %s: a party keeps its places %r' % (host, party, (hx, hy)))
# the hook sits in obj_battlecontroller's Create just before the heroes are made (every variant's copy)
src = open('/home/claude/work/build/merged/gml_Object_obj_battlecontroller_Create_0.gml').read()
ok(src.count('knight_solo_lineup();') >= 2 and all(src.index('knight_solo_lineup();', p) < src.index('obj_herokris', p) for p in [0]), 'the battle calls it before it makes the heroes')
print('solo50 tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
