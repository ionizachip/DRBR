"""Build 48: the Roaring in the online battle royale. Part A (timeline): the first cycle of the final two, and the first cycle
that starts 3 minutes into the match, use the cycle knight's own Roaring - any knight; the same cycles in every game; no Twin
layer. Part B (emulator, the real merged fight code): each knight's Roaring runs as a cycle - starts, ends, no error; with
MEASURE=1 it writes /home/claude/work/online/roar48.json (frames to the end of its turn, the objects it made).
Usage: python3 t_roar48.py [A|B|AB]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
import br_harness
from br_harness import br_match, br_state

PARTS = sys.argv[1] if len(sys.argv) > 1 else 'AB'
MEASURE = os.environ.get('MEASURE') == '1'
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg); print('FAIL', msg, flush=True)
    else:
        print('ok  ', msg, flush=True)

if 'A' in PARTS:
    sim = make_sim()
    sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
    J = lambda e: sim.py(sim.eval(e))
    names = {r: J('knight_reg(%d).atk[kbr_roar_ai(%d)][2]' % (r, r)) for r in range(5)}
    ok(all('Roaring' in n for n in names.values()), 'every hub knight has a Roaring: %r' % names)
    seen = set(); roar_t = 0; roar_ft = 0; twin_bad = 0; sigs_same = True
    for seed in range(1, 121):
        for ftk in (-1, 3, 7, 12):
            # half the seeds with RANDOM RUSH (any knight at any cycle), half CLASSIC
            sim.run('global.TL = kbr_tl_new(%d, kfo_set_clean({ kn: [0,1,2,3,4,5], rush: %d })); if (%d >= 0) kbr_tl_set_ft(global.TL, %d);' % (seed, 3 if seed % 2 else 0, ftk, ftk))
            cyc = [J('(function(){ var _c = kbr_tl_get(global.TL, %d); return [_c.roar, _c.ok, _c.b0, _c.twin, _c.ai, _c.reg, kbr_tl_sig(_c)]; })()' % k) for k in range(30)]
            intro = J('global.TL.intro')
            th = intro + 5400
            for k, c in enumerate(cyc):
                should = (ftk >= 0 and k == ftk) or (c[2] >= th and (k == 0 or cyc[k - 1][2] < th))
                if bool(c[0]) != should:
                    ok(False, 'seed %d ft %d cycle %d roar %r expected %r' % (seed, ftk, k, c[0], should)); break
                if c[0]:
                    seen.add(c[1])
                    if c[4] != J('kbr_roar_ai(%d)' % c[5]): ok(False, 'roar cycle uses the Roaring')
                    if c[3]: twin_bad += 1
                    if ftk == k: roar_ft += 1
                    else: roar_t += 1
            # a game that hears of the final two late works out the same cycles
            if ftk >= 0:
                sim.run('global.TL2 = kbr_tl_new(%d, kfo_set_clean({ kn: [0,1,2,3,4,5], rush: %d })); kbr_tl_get(global.TL2, 20); kbr_tl_set_ft(global.TL2, %d);' % (seed, 3 if seed % 2 else 0, ftk))
                c2 = [J('kbr_tl_sig(kbr_tl_get(global.TL2, %d))' % k) for k in range(30)]
                if c2 != [c[6] for c in cyc]: sigs_same = False
    ok(roar_ft == 120 * 3, 'the first final-two cycle is always a Roaring (%d)' % roar_ft)
    ok(roar_t >= 120 * 3, 'the first cycle after 3 minutes is a Roaring (%d)' % roar_t)
    ok(seen >= {0, 1, 2, 3, 4}, 'any knight can roar (online knights seen %r)' % sorted(seen))
    ok(twin_bad == 0, 'no Twin layer over a Roaring (%d)' % twin_bad)
    ok(sigs_same, 'late final-two news gives the same cycles')
    # with FINAL TWO off the Roaring still opens the final two, without the showdown
    sim.run('global.TL = kbr_tl_new(5, kfo_set_clean({ kn: [0,1,2,3,4,5], ft: 0 })); kbr_tl_set_ft(global.TL, 4);')
    ok(J('kbr_tl_get(global.TL, 4).roar') and not J('kbr_tl_get(global.TL, 4).ft'), 'FINAL TWO off: Roaring, no showdown')

if 'B' in PARTS:
    res = {}
    for ok_k in (0, 1, 2, 3, 4):
        t0 = time.time()
        sim, e = br_match(open_ok=ok_k, kn=(ok_k,), seed=900 + ok_k)
        if e is not None:
            ok(False, 'knight %d match setup: %s' % (ok_k, e)); continue
        sim.run('kbr_tl_set_ft(global.kfo.M.tl, 1); kbr_tl_set_ft(global.kfo.H.tl, 1);')
        made = []
        old = sim.create_hook
        def hook(name, _old=old):
            made.append(name); _old(name)
        sim.create_hook = hook
        err = None; roar_seen = False; start_f = None; end_f = None; why = None; f = 0; ph_prev = None; c1 = None
        while f < 4000:
            err = br_harness.step(sim, 1)
            f += 1
            if err: break
            if f % 3: continue
            s = br_state(sim)
            sim.run('for (var _i = 1; _i <= 4; _i++) global.hp[_i] = max(global.hp[_i], 60);')
            if s['k'] == 1 and s['ph'] == 'run' and start_f is None:
                start_f = f; made.clear()
            if start_f is not None and sim.eval('instance_exists(obj_knight_roaring2) || instance_exists(obj_knight_roaring3)'):
                roar_seen = True
            if start_f is not None and s['k'] >= 2:
                end_f = f; why = s['cut']; break
        c1 = sim.py(sim.eval('kbr_tl_get(global.kfo.M.tl, 1)'))
        left = sim.eval('instance_exists(obj_knight_roaring2) || instance_exists(obj_knight_roaring3)')
        reg = c1['reg']
        ok(err is None, 'knight %d: no error (%s)' % (ok_k, err))
        ok(c1['roar'], 'knight %d: cycle 1 is its Roaring (%s)' % (ok_k, sim.eval('kbr_atk_name(%d, %d)' % (ok_k, c1['ai']))))
        ok(start_f is not None and end_f is not None, 'knight %d: the Roaring started and ended (frames %r..%r, %s)' % (ok_k, start_f, end_f, why))
        ok(roar_seen, 'knight %d: a Roaring object was on screen' % ok_k)
        ok(not left, 'knight %d: nothing of the Roaring is left after it' % ok_k)
        res[str(reg)] = [{'ok': ok_k, 'dur': (end_f - start_f) if (start_f and end_f and why == 'end') else None, 'why': why, 'err': err, 'objs': sorted(set(made))}]
        print('  knight', ok_k, 'run', start_f, end_f, why, 'objs', sorted(set(made)), round(time.time() - t0, 1), 's', flush=True)
    if MEASURE:
        json.dump(res, open('/home/claude/work/online/roar48.json', 'w'), indent=1)
print('PASS' if not FAILS else 'FAIL', N[0] - len(FAILS), '/', len(FAILS))
