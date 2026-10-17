"""DRBR: every encounter in one KNIGHT RUSH (a new one every attack): the Normal Knight, Jevil, Gerson, Flowery, Spamton NEO and
Pink in a practice match (the emulator: the real merged code, a mocked engine, SOUL / bullet collisions on), the SOUL standing.
At the start of every attack, checked:
  - the stage: the lineup's active entry is the cycle's encounter (a knight: its index; a boss: its lineup id 1000 + n), its
    battle object on stage and NO other boss's battle object;
  - nothing of another encounter left: no piece of another boss (obj_jv_ / obj_hj_ / obj_fl_ / obj_sn_ / obj_pk_, their
    backgrounds aside), no knight while a boss is out;
  - the battle names the boss while it is out;
and over each attack: the SOUL in the boss's own mode at some point (Gerson green, Flowery orange, Spamton yellow, Pink purple or
her concert's red) and red again after the cut; no error, no frame run twice. Usage: python3 t_mixed53.py [frames]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *

FAILS = []
N = [0]
FR = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
OKS = (0, 6, 7, 8, 9, 10)
BOSS = {6: ('obj_jv_joker', 'obj_jv_', 1000, 'Jevil', None), 7: ('obj_hj_gerson', 'obj_hj_', 1001, 'Gerson', 'green'),
        8: ('obj_fl_flowery', 'obj_fl_', 1002, 'Flowery', 'orange'), 9: ('obj_sn_neo', 'obj_sn_', 1003, 'Spamton NEO', 'yellow'),
        10: ('obj_pk_pink', 'obj_pk_', 1004, 'Pink', 'purple')}


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


t0 = time.time()
sim, e = br_match(open_ok=0, kn=OKS, seed=6300, bots=0, setx='_s.mhp = 999; _s.rush = 1; _s.ramp = 3; _s.hard = 1;')
ok(e is None, 'mixed: practice with the Knight and the five bosses, a new one every attack (%s)' % (e,))
sim.run('global.knight_mus_ok_force = true;')
# every instance's object name, grouped by prefix (the bosses' backgrounds aside: they fade out after their boss)
STAGE = ('(function(){ var _M = global.kfo.M; var _c = kbr_tl_get(_M.tl, _M.R.k); var _lu = global.knight_lu; var _o = {};'
         'var _p = ["obj_jv_", "obj_hj_", "obj_fl_", "obj_sn_", "obj_pk_"];'
         'with (all) { var _n = object_get_name(object_index); for (var _i = 0; _i < 5; _i++) { if (string_pos(_p[_i], _n) == 1 && string_pos("_bg", _n) == 0) { variable_struct_set(_o, _n, (variable_struct_exists(_o, _n) ? variable_struct_get(_o, _n) : 0) + 1); } } }'
         'var _kn = 0; with (obj_knight_enemy) _kn++;'
         'return { k: _c.k, ok: _c.ok, ai: _c.ai, act: _lu.ks[_lu.act], kn: _kn, pre: _o, name: global.monstername[0],'
         ' objs: [instance_number(obj_jv_joker), instance_number(obj_hj_gerson), instance_number(obj_fl_flowery), instance_number(obj_sn_neo), instance_number(obj_pk_pink)] }; })()')
rows = []
modes = {}
last_k = -1
err = None
for f in range(FR):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    err = step(sim, 1)
    if err:
        break
    if f % 30 == 0:
        sim.log.clear()
    sim.run(BR_CHK)
    b = J(sim, 'global.BRS')
    if b['ph'] == 'run' and b['k'] != last_k:
        last_k = b['k']
        rows.append(J(sim, STAGE))
    if b['ph'] == 'run' and rows:
        modes.setdefault(rows[-1]['k'], set()).add(J(sim, 'kbr_soul_mode()'))
ok(err is None, 'mixed: no error in %d frames %s' % (FR, (err or '')[:300]))
ok(not getattr(sim, 'retrylog', []), 'mixed: no frame run twice %r' % (getattr(sim, 'retrylog', [])[:2],))
print('cycles', json.dumps(rows), flush=True)
print('modes', {k: sorted(v) for k, v in modes.items()}, flush=True)
seen = sorted(set(r['ok'] for r in rows))
ok(len(seen) >= 4, 'mixed: at least four encounters took turns %r (%d cycles)' % (seen, len(rows)))
for r in rows:
    o = r['ok']
    if o in BOSS:
        obj, pre, lu, name, mode = BOSS[o]
        oi = sorted(BOSS).index(o)
        ok(r['act'] == lu and r['kn'] == 0 and r['objs'][oi] == 1 and sum(r['objs']) == 1,
           'cycle %d (%s, attack %d): %s on stage alone, no knight %r' % (r['k'], name, r['ai'], name, [r['act'], r['kn'], r['objs']]))
        ok(all(n.startswith(pre) for n in r['pre']), 'cycle %d (%s): nothing of another boss left %r' % (r['k'], name, {n: v for n, v in r['pre'].items() if not n.startswith(pre)}))
        ok(r['name'] == name, 'cycle %d: the battle names %s (%r)' % (r['k'], name, r['name']))
        if mode is not None:
            ms = modes.get(r['k'], set())
            ok(mode in ms or (o == 10 and 'red' in ms), 'cycle %d (%s, attack %d): the SOUL in his / her mode (%s) %r' % (r['k'], name, r['ai'], mode, sorted(ms)))
    else:
        ok(r['act'] == o and r['kn'] == 1 and sum(r['objs']) == 0 and r['pre'] == {}, 'cycle %d (knight %d): the knight on stage, no boss and nothing of one left %r' % (r['k'], o, [r['act'], r['kn'], r['objs'], r['pre']]))
        ok(modes.get(r['k'], {'red'}) == {'red'}, 'cycle %d (knight %d): the SOUL red all the attack %r' % (r['k'], o, sorted(modes.get(r['k'], []))))
print('mixed53: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
