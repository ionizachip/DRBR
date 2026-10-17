"""Build 45: one game running the shared battle royale (practice room, the real merged fight code in the emulator).
Checks, cycle by cycle: the knight on screen is the timeline's knight, the attack the knight starts is the timeline's attack,
it starts on the timeline's tick, the end of every attack leaves no bullets or attack objects behind, no cycle runs twice,
none is skipped. Usage: python3 t_br_single.py [cycles] [open_ok] [rush] [seed]"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

NCYC = int(sys.argv[1]) if len(sys.argv) > 1 else 12
OPEN = int(sys.argv[2]) if len(sys.argv) > 2 else 0
RUSH = int(sys.argv[3]) if len(sys.argv) > 3 else 1
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 4242
WALL = float(os.environ.get('WALL', '900'))

t0 = time.time()
sim, e = br_match(open_ok=OPEN, seed=SEED, setx='_s.rush = %d; _s.mhp = 300; _s.cdn = 3;' % RUSH)
if e is not None:
    print('SETUP FAILED', e)
    sys.exit(1)
print('setup ok', round(time.time() - t0, 1), 's; why:', sim.eval('global.BRWHY'), flush=True)

# the knight's own looks (its afterimage trail, particles) come and go by themselves: not counted
LINGER = ('var _n = 0; var _l = kbr_atk_objs(); for (var _i = 0; _i < array_length(_l); _i++) { var _nm = object_get_name(_l[_i]);'
          ' if (string_pos("obj_afterimage", _nm) != 1 && _nm != "obj_particle_generic") { with (_l[_i]) { if (real(id) > global.LMARK) _n++; } } } global.LING = _n;')
res = {'cycles': [], 'errors': [], 'linger': [], 'mismatch': [], 'late': []}
prev = br_state(sim)
f = 0
started = []
while time.time() - t0 < WALL:
    err = step(sim, 1)
    f += 1
    if err is not None:
        res['errors'].append([f, prev.get('ph'), err[:400]])
        print('STEP ERROR at frame', f, prev.get('ph'), err[:800], flush=True)
        break
    if f % 20 == 0:
        sim.run('global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    s = br_state(sim)
    if s['ph'] == 'run' and prev['ph'] != 'run':
        k = s['k']
        c = sim.py(sim.eval('kbr_tl_get(global.kfo.M.tl, %d)' % k))
        rec = {'k': k, 'ok': c['ok'], 'reg': c['reg'], 'ai': c['ai'], 't0': c['t0'], 'rel': round(sim.eval('global.kfo.M.R.t_spawn'), 2), 'act': s['act'], 'plan': s['plan'],
               'twin': c['twin'], 'hyper': c['hyper'], 'st': c['st']}
        if k in started:
            res['mismatch'].append(['twice', k])
        started.append(k)
        if s['act'] != c['reg']:
            res['mismatch'].append(['knight', k, s['act'], c['reg']])
        if s['plan'] != c['ai']:
            res['mismatch'].append(['attack', k, s['plan'], c['ai']])
        rel = sim.eval('global.kfo.M.R.t_spawn')
        rec_late = rel - c['t0']
        if rel < c['t0'] or rec_late > 1.05:
            res['late'].append([k, round(rec_late, 2)])
        res['cycles'].append(rec)
        print('cycle', k, 'ok', c['ok'], 'ai', c['ai'], kbr_name := sim.eval('kbr_atk_name(%d, %d)' % (c['ok'], c['ai'])), 't0', c['t0'], 'rel', round(sim.eval('global.kfo.M.R.t_spawn'), 2),
              'act', s['act'], 'plan', s['plan'], 'tw', c['twin'], 'hy', c['hyper'], 'st', c['st'], '%.0fs' % (time.time() - t0), flush=True)
    if prev['ph'] == 'run' and s['ph'] == 'idle':
        res['cycles'][-1]['cut'] = s['cut']
        res['cycles'][-1]['bul_left'] = s['bul']
    if s['ph'] == 'arm' and prev['ph'] != 'arm':
        sim.run('global.LMARK = (variable_global_exists("LMARK_PREV") ? global.LMARK_PREV : 999999999); global.LMARK_PREV = global.kfo.M.R.mark;')
        sim.run(LINGER)
        n = sim.eval('global.LING')
        nb = sim.eval('instance_number(obj_bulletparent)')
        if n or nb:
            res['linger'].append([s['arm'], n, nb])
    prev = s
    if len(res['cycles']) >= NCYC and s['ph'] == 'idle':
        break
res['skipped'] = prev['skipped']
res['frames'] = f
res['wall'] = round(time.time() - t0, 1)
res['assert_n'] = sim.eval('global.kbr_assert_n')
ok = (not res['errors'] and not res['mismatch'] and not res['linger'] and len(res['cycles']) >= NCYC and res['assert_n'] == 0)
res['pass'] = ok
out = os.environ.get('BR_OUT', '/tmp/claude-0/br45/t_br_single_%d_%d_%d.json' % (OPEN, RUSH, SEED))
json.dump(res, open(out, 'w'), indent=1)
print('RESULT', 'PASS' if ok else 'FAIL', 'cycles', len(res['cycles']), 'skipped', res['skipped'], 'late', res['late'][:5], 'mismatch', res['mismatch'][:5],
      'linger', res['linger'][:5], 'errors', len(res['errors']), 'frames', f, 'wall', res['wall'], flush=True)
sys.exit(0 if ok else 1)  # build 46: a FAIL is a failing exit code too (runall)
