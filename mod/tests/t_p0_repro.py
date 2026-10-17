"""DRBR P0: the destroyonhit crash reproduced / checked with the collision pump: Jevil's attack N in a practice match, the SOUL
moved onto his bullets every frame (it stands where they are), collisions on."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

def J(sim, e):
    return sim.py(sim.eval(e))

def run(ai, frames=900, chase=True):
    sim, e = br_match(open_ok=6, kn=(6,), seed=5200 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if e:
        return {'ai': ai, 'err': 'setup ' + str(e)}
    sim.run('global.JV_FORCE = %d;' % ai)
    sim.load_source('gml_GlobalScript_jvforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    err = None
    hits0 = 0
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        if chase:
            # the SOUL steps onto a bullet of his (the first live child of obj_collidebullet), as a careless player would
            sim.run('if (instance_exists(obj_heart)) { var _b = noone; with (obj_collidebullet) { if (_b == noone && object_get_name(object_index) != "obj_collidebullet__none") _b = id; } if (_b != noone) { obj_heart.x = _b.x - 10; obj_heart.y = _b.y - 10; } }')
        err = step(sim, 1)
        if err:
            break
        if f % 30 == 0:
            sim.log.clear()
    bfix = J(sim, 'variable_global_exists("kbr_bfix") ? global.kbr_bfix : {}') if not err else None
    return {'ai': ai, 'err': (err or '')[:300] or None, 'contacts': dict(collide.STATS), 'bfix': bfix}

if __name__ == '__main__':
    ais = [int(a) for a in sys.argv[1:]] or [1]
    for ai in ais:
        collide.STATS.update({'heart': 0, 'graze': 0, 'frames': 0})
        t0 = time.time()
        r = run(ai)
        r['wall'] = round(time.time() - t0)
        print(json.dumps(r), flush=True)
