"""DRBR 1.0.2 - your report: "devils knife bug, uses wrong voiceline and doesn't play". A practice match against Jevil, each
frame stepped AND drawn (his body turns into the Devilsknife in its Draw, as Chapter 1's does), the sounds played recorded:
  - the Devilsknife (3) and the Devilsknife Swing (11): Chapter 1's "METAMORPHOSIS!" as his body turns, once, and no other
    voice of his at the same time (DRBR used to add a laugh / "HA" / "CHAOS, CHAOS!" over it); his four Devilsknives come
    (snd_spearappear), fade in, swing round the box (they move, the king makes its "swing" sounds) and hurt
  - the finale BYE-BYE (15): "BYE-BYE!" once (it was played twice)
  - the other attacks keep their own voice (a laugh, "HA", "CHAOS, CHAOS!" or "I CAN DO ANYTHING!")
  - the DEVILSKNIFE skill sent at you: it lands with "METAMORPHOSIS!" and the spear sound, and its four Devilsknives swing
Usage: python3 t_jevil102.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.pop('KH_CAM', None)
from br_harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import Recorder

FAILS = []
N = [0]
VOICES = ('snd_joker_laugh0', 'snd_joker_ha0', 'snd_joker_ha1', 'snd_joker_chaos', 'snd_joker_anything', 'snd_joker_byebye',
          'snd_joker_metamorphosis', 'snd_joker_oh', 'snd_joker_neochaos')


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


def game(force, seed=5406):
    sim, e = br_match(open_ok=6, kn=(6,), seed=seed, bots=0, setx='_s.mhp = 999; _s.skills = 1;')
    assert not e, e
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.run('global.BS_FORCE = %d;' % force)
    sim.load_source('gml_GlobalScript_jv102force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.BS_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    # (the scythes' own sprite and mask, as the game's object has them: the emulator's objects have none)
    sim.objects['obj_jv_cscythe'].sprite = sim.asset_index('spr_jv_joker_scythebody')
    sim.played = []
    sim.mock('snd_play', lambda s, a, *r: (s.played.append((s.frame_no, a)), 0)[1])
    rec = Recorder(sim)
    try:
        sim.define_asset('hpfont')
    except Exception:
        pass
    sim.run('if (!variable_global_exists("hpfont")) global.hpfont = hpfont;')
    return sim, rec


def draw_all(sim, rec):
    rec.ops.clear()
    for inst in sorted([i for i in sim.instances.values() if not i.dead], key=lambda i: -i.vars.get('depth', 0)):
        if inst.dead or inst.id not in sim.instances or not inst.vars.get('visible', True):
            continue
        found = sim.find_event(inst.obj, ('Draw', 0))
        if found is not None:
            try:
                sim._run_entry(inst, found[0], ('Draw', 0), found[1], None)
            except Exception:
                pass


def run_attacks(sim, rec, n_attacks, frames=1600, on=None):
    names = {v: k for k, v in sim.assets.items()}
    out = []
    cur = None
    last = ''
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            return out, err
        draw_all(sim, rec)
        ph = sim.eval('global.kfo.M.R.ph')
        if ph == 'run' and last != 'run':
            cur = {'f0': sim.frame_no, 'ai': sim.eval('obj_jv_joker.jattack'), 'sc': [], 'voices': []}
            out.append(cur)
        if ph != 'run' and last == 'run' and len(out) >= n_attacks:
            break
        last = ph
        if cur is not None and ph == 'run':
            sc = sim.py(sim.eval('(function(){ var _o = []; with (obj_jv_cscythe) array_push(_o, [round(x), round(y), image_alpha, active]); return _o; })()'))
            cur['sc'].append(sc)
            if on:
                on(sim, cur)
    for a in out:
        a['voices'] = [names.get(s, s) for (fr, s) in sim.played if a['f0'] - 1 <= fr <= a['f0'] + 3 and names.get(s, '') in VOICES]
        a['all'] = [(fr - a['f0'], names.get(s, s)) for (fr, s) in sim.played if fr >= a['f0'] - 1]
    return out, None


t0 = time.time()
# 1. the Devilsknife attacks and the finale: the first time each, and again (his repeat lines)
for ai, name in ((3, 'Devilsknife'), (11, 'Devilsknife Swing')):
    sim, rec = game(ai)
    res, err = run_attacks(sim, rec, 2)
    ok(not err and len(res) >= 2, '%s: two of it ran (%s)' % (name, err))
    for k, a in enumerate(res[:2]):
        v = a['voices']
        ok(v == ['snd_joker_metamorphosis'], '%s (%s time): Chapter 1\'s voice only - "METAMORPHOSIS!" as his body turns (voices %r)' % (name, 'first' if k == 0 else 'second', v))
        sc = [x for x in a['sc'] if x]
        moved = len(set((s[0][0], s[0][1]) for s in sc))
        alive = max((len(s) for s in sc), default=0)
        vis = max((s[0][2] for s in sc), default=0)
        act = max((s[0][3] for s in sc), default=0)
        ok(alive == 4 and moved > 50 and vis >= 1 and act == 1, '%s (%s time): his four Devilsknives come, fade in, swing round the box and hurt (%d of them, %d places, alpha %s, active %s)'
           % (name, 'first' if k == 0 else 'second', alive, moved, vis, act))
        sw = [s for (fr, s) in a['all'] if s in ('snd_spearappear', 'snd_swing')]
        ok('snd_spearappear' in sw and 'snd_swing' in sw, '%s (%s time): with their sounds (%r)' % (name, 'first' if k == 0 else 'second', sorted(set(sw))))
sim, rec = game(15)
res, err = run_attacks(sim, rec, 1, frames=2600)
ok(not err and len(res) >= 1, 'BYE-BYE: it ran (%s)' % err)
if res:
    bye = [s for (fr, s) in res[0]['all'] if s == 'snd_joker_byebye']
    ok(len(bye) == 1, 'BYE-BYE: "BYE-BYE!" once (%d)' % len(bye))
# 2. the other attacks keep a voice of his
sim, rec = game(1)
res, err = run_attacks(sim, rec, 1)
ok(not err and res and len(res[0]['voices']) == 1 and res[0]['voices'][0] != 'snd_joker_metamorphosis', 'Ring-Around: one voice of his (%r)' % (res[0]['voices'] if res else None))
# 3. the DEVILSKNIFE skill sent at you lands with his voice and its four Devilsknives
sim, rec = game(1, seed=5407)
landed = {}


def send_once(sim, cur):
    if 'sent' not in landed and len(cur['sc']) == 30:
        landed['sent'] = sim.frame_no
        sim.run('var _M = global.kfo.M; array_push(_M.sk.pend, { sid: 30, from: 2, fn: "LANCER", sd: 777, t: 0, rf: 0, sh: 0 });')


res, err = run_attacks(sim, rec, 1, on=send_once)
names = {v: k for k, v in sim.assets.items()}
ok(not err and 'sent' in landed, 'DEVILSKNIFE skill: sent at you during his attack (%s)' % err)
if 'sent' in landed:
    snd = [names.get(s, s) for (fr, s) in sim.played if landed['sent'] <= fr <= landed['sent'] + 3]
    ok('snd_joker_metamorphosis' in snd and 'snd_spearappear' in snd, 'DEVILSKNIFE skill: lands with "METAMORPHOSIS!" and the spear sound (%r)' % snd)
    sc = [x for x in res[0]['sc'][31:] if x] if res else []
    moved = len(set((s[0][0], s[0][1]) for s in sc))
    ok(max((len(s) for s in sc), default=0) == 4 and moved > 30, 'DEVILSKNIFE skill: its four Devilsknives swing (%d places)' % moved)
print('jevil102: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
