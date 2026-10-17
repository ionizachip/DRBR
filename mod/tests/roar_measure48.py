"""Build 45: measure every online attack in the emulator (the real merged fight code): how long it runs (frames from its
start to the end of its turn timer), how many bullets it puts up, and every object it makes. Writes
/home/claude/work/online/br_catalogue.json, which gen_hub turns into the timeline's attack durations (global.kbr_cat_dur)
and the determinism rewrite uses as the list of attack objects. Usage: python3 br_measure.py [reg ...]"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
from lu_harness import *

KN = ['base', 'kaizo', 'elec', 'violet', 'thorn']
OUT = "/home/claude/work/online/roar48.json"
regs = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3, 4]

setc = '{ kn: [0,1,2,3,4], open: %d, ramp: 1, maxst: 4, sends: 0, maxp: 8, bots: 0 }'
EXTRA = ('global.is_console = 0; kfo_get(); global.kfo.name = "Kris"; global.kfo.skin = 1; global.kfo.set = kfo_set_clean(%s); global.kfo.set.bots = 0;'
         'kfo_practice_start(); kfo_tick();'
         'var _H = global.kfo.H; _H.st = "match"; _H.mid = 1; _H.seed = 777; _H.mset = kfo_set_clean(global.kfo.set); _H.startn = 1;'
         '_H.pl[0].inm = 1; _H.pl[0].al = 1; _H.eff = kbr_eff(_H.mset);'
         'global.kfo.M = kfo_match_new({ mid: 1, seed: 777, set: global.kfo.set, players: [{ pid: 1, n: "Kris", s: 1, bot: 0 }], prac: 1 });'
         'global.kfo.M.launched = true;')

BR_STUB = '''reset = (variable_instance_exists(id,"reset")) ? reset : 0;
if (global.mnfight == 2) { global.turntimer -= 1; global.TT_active = 1;
 if (global.turntimer <= 0 && reset == 0) { reset = 1; global.TT_end = global.TT_f; } }
global.TT_f += 1;'''

res = json.load(open(OUT)) if os.path.exists(OUT) else {}
for reg in regs:
    t0 = time.time()
    import br_harness
    sim, e = br_harness.br_battle(reg, stub=BR_STUB, extra='global.kfo.H.eff = kbr_eff(global.kfo.H.mset);')
    if e is not None:
        print('setup failed', KN[reg], e, flush=True)
        continue
    made = []
    old_hook = sim.create_hook
    def hook(name, _old=old_hook):
        made.append(name)
        _old(name)
    sim.create_hook = hook
    slot = sim.eval('global.knight_lu.act')
    atk = sim.py(sim.eval('knight_reg(%d).atk' % reg))
    out = []
    for ai, a in enumerate(atk):
        if "Roaring" not in a[2] or a[3] == 0:
            continue
        made.clear()
        r = {'ai': ai, 'name': a[2], 'phase': a[0]}
        sim.run('global.knight_lu.plan_k = %d; global.knight_lu.plan_i = %d; global.knight_lu.want = %d;' % (slot, ai, slot))
        good, err = auto(sim, lambda: sim.run('global.TT_end=-1; global.turntimer=0; global.mnfight=1.5; global.myfight=0; with (obj_battlecontroller) reset = 0;'
                                             'global.TT_f = 0; with (obj_knight_enemy) { talked = 1; attackchosen = false; rtimer = 0; attacked = 0; }'))
        spawn = None; maxb = 0; f = 0; err = None
        while f < 3000:
            good, err2 = auto(sim, lambda: sim.step(1))
            f += 1
            if not good:
                err = err2[:200]
                break
            if f % 5 == 0:
                if spawn is None and sim.eval('obj_knight_enemy.attacked') == 1:
                    spawn = sim.eval('global.TT_f')
                maxb = max(maxb, sim.eval('instance_number(obj_bulletparent)'))
                if sim.eval('global.TT_end') >= 0:
                    break
                sim.run('for (var _i = 1; _i <= 4; _i++) global.hp[_i] = max(global.hp[_i], 60);')
        end = sim.eval('global.TT_end')
        r.update(spawn=spawn, end=end, frames=f, dur=(end - (spawn or 12)) if end >= 0 else None, maxbul=maxb, err=err,
                 objs=sorted(set(made)))
        out.append(r)
        print(KN[reg], ai, a[2], 'spawn', spawn, 'end', end, 'maxbul', maxb, 'objs', len(set(made)), 'err', err, flush=True)
        good, err = auto(sim, lambda: sim.run('with (obj_bulletparent) instance_destroy(); with (obj_bulletgenparent) instance_destroy(); with (obj_dbulletcontroller) instance_destroy();'
                                             'with (obj_growtangle) instance_destroy(); global.mnfight = 0; global.myfight = 0;'
                                             'with (obj_monsterparent) { attacked = 0; talked = 0; acting = 0; }'))
    res[str(reg)] = out
    json.dump(res, open(OUT, 'w'), indent=1)
    print('knight', KN[reg], 'done', round(time.time() - t0, 1), 's', flush=True)
print('ALL DONE')
