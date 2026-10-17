"""Build 52: JEVIL in KNIGHT FIGHTS ONLINE - every one of his 16 attacks (his own Chapter 1 pieces, obj_jv_*) in a practice match
(the emulator: the real merged code, a mocked engine), one match per attack, the attack forced as the first cycle's:
  - it starts at the shared tick (Jevil steps in during the countdown: the Normal Knight never shows), it makes bullets;
  - it ends by itself (its own turn timer: 240-330 frames; BYE-BYE when its white-out is over) or is cut, with no error;
  - nothing of it is left after it (bullets, its controller, BYE-BYE's darkness / white-out / giant scythe / rumble);
  - his body, his background (on) and his battle object stay; the SOUL is there again for the next attack.
Usage: python3 t_jevil52.py [first last]   (attack range, default 0 15)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

FAILS = []
N = [0]
RES = {}


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


FORCE = '''
function kbr_tl_pick_attack__jv(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }
'''


def run_attack(ai):
    sim, e = br_match(open_ok=6, kn=(6,), seed=5200 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, 'attack %d: practice with Jevil only (%s)' % (ai, e)):
        return
    # the attack forced for every cycle (the timeline's own pick replaced; BYE-BYE is the finale - forced the same way)
    sim.run('global.JV_FORCE = %d;' % ai)
    src = 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n'
    sim.load_source('gml_GlobalScript_jvforce', src)
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    t0 = time.time()
    seen_bul = 0
    started = -1
    ended = -1
    why = ''
    err = None
    tt0 = None
    for f in range(1700):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            break
        if f % 30 == 0:
            sim.log.clear()
        sim.run(BR_CHK)
        b = J(sim, 'global.BRS')
        if started < 0 and b['ph'] == 'run' and b['k'] == 0:
            started = f
            tt0 = b['tt']
        if started >= 0:
            seen_bul = max(seen_bul, b['bul'])
        if started >= 0 and b['k'] >= 1:
            ended = f
            why = b['cut']
            break
    left = None
    if ended >= 0:
        left = J(sim, '(function(){ var _o = {}; var _l = ["obj_jv_teleport", "obj_jv_spadering", "obj_jv_suitbomb", "obj_jv_heartblast", "obj_jv_carousel", "obj_jv_cscythe", "obj_jv_lscythe", "obj_jv_bscythe", "obj_jv_clubs", "obj_jv_dvert"]; for (var _i = 0; _i < array_length(_l); _i++) { var _n = instance_number(asset_get_index(_l[_i])); if (_n > 0) variable_struct_set(_o, _l[_i], _n); } var _m = 0; with (obj_marker) { if (sprite_index == spr_jv_tallpx) _m++; } if (_m > 0) _o.tallpx_markers = _m; return _o; })()')
    keep = J(sim, '[instance_number(obj_jv_joker), instance_number(obj_jv_body), instance_number(obj_jv_bg), instance_exists(obj_jv_bg) ? obj_jv_bg.on : -1, instance_number(obj_knight_enemy)]') if err is None else None
    RES[ai] = {'started': started, 'ended': ended, 'frames': (ended - started) if ended >= 0 else -1, 'why': why, 'max_bullets': seen_bul,
               'tt0': tt0, 'left': left, 'keep': keep, 'err': err[:300] if err else None, 'wall': round(time.time() - t0)}
    print('attack', ai, json.dumps(RES[ai]), flush=True)
    ok(err is None, 'attack %d (%s): no error %s' % (ai, NAMES[ai], (err or '')[:200]))
    ok(started >= 0, 'attack %d: it started (frame %d)' % (ai, started))
    ok(seen_bul > 0, 'attack %d: it made bullets (%d at most)' % (ai, seen_bul))
    ok(ended >= 0 and why in ('end', 'next'), 'attack %d: it ended (%s after %d frames)' % (ai, why, ended - started))
    ok(left == {}, 'attack %d: nothing of it left after it %r' % (ai, left))
    ok(keep is not None and keep[0] == 1 and keep[1] == 1 and keep[2] == 1 and keep[3] == 1 and keep[4] == 0,
       'attack %d: Jevil, his body and his background (on) are there, no knight %r' % (ai, keep))


def mixed():
    # KNIGHT RUSH between the Normal Knight and Jevil: a new one every attack
    sim, e = br_match(open_ok=0, kn=(0, 6), seed=6100, bots=0, setx='_s.mhp = 999; _s.rush = 1;')
    if not ok(e is None, 'mixed: practice with the Normal Knight and Jevil, a new one every attack (%s)' % (e,)):
        return
    sim.run('global.knight_mus_ok_force = true;')
    rows = []
    last_k = -1
    err = None
    for f in range(2400):
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
            r = J(sim, '(function(){ var _M = global.kfo.M; var _c = kbr_tl_get(_M.tl, _M.R.k); var _lu = global.knight_lu;'
                       'var _kn = 0; with (obj_knight_enemy) _kn++; var _jv = 0; with (obj_jv_joker) _jv++;'
                       'var _jb = 0; var _l = ["obj_jv_teleport", "obj_jv_spadering", "obj_jv_suitbomb", "obj_jv_heartblast", "obj_jv_carousel", "obj_jv_cscythe", "obj_jv_lscythe", "obj_jv_bscythe", "obj_jv_clubs", "obj_jv_dvert", "obj_jv_dbc"];'
                       'for (var _i = 0; _i < array_length(_l); _i++) _jb += instance_number(asset_get_index(_l[_i]));'
                       'return { k: _c.k, ok: _c.ok, ai: _c.ai, st: _c.st, act: _lu.ks[_lu.act], kn: _kn, jv: _jv, jvb: _jb, bgon: instance_exists(obj_jv_bg) ? obj_jv_bg.on : -1,'
                       ' body: (instance_exists(obj_jv_body) && instance_exists(obj_jv_body.owner)) ? 1 : 0, mus: variable_struct_exists(_M, "jvmus") ? _M.jvmus : -1, twin: _c.twin, name: global.monstername[0] }; })()')
            rows.append(r)
    ok(err is None, 'mixed: no error %s' % (err or '')[:200])
    print('mixed cycles', json.dumps(rows), flush=True)
    kn_c = [r for r in rows if r['ok'] == 0]
    jv_c = [r for r in rows if r['ok'] == 6]
    ok(len(kn_c) >= 2 and len(jv_c) >= 2, 'mixed: both took turns (%d Knight, %d Jevil cycles)' % (len(kn_c), len(jv_c)))
    ok(all(r['act'] == 0 and r['kn'] == 1 and r['jv'] == 0 for r in kn_c), "mixed: the Knight's cycles: the Knight on stage, Jevil switched off")
    ok(all(r['act'] == 1000 and r['kn'] == 0 and r['jv'] == 1 for r in jv_c), "mixed: Jevil's cycles: Jevil on stage, the Knight switched off")
    ok(all(r['jvb'] == 0 for r in kn_c), "mixed: none of Jevil's pieces left in a Knight's cycle")
    ok(all(r['bgon'] == 0 and r['body'] == 0 for r in kn_c) and all(r['bgon'] == 1 and r['body'] == 1 for r in jv_c), 'mixed: his background and his body only while he is out')
    ok(all(r['name'] == 'Jevil' for r in jv_c), 'mixed: the battle names him Jevil while he is out %r' % sorted(set(r['name'] for r in rows)))
    ok(all(not r['twin'] for r in jv_c), 'mixed: no Twin Knight over Jevil')
    # (his phases by stage, as a knight's: stage 0 his phase 1 - attacks 0-3, stage 1 phases 1-2 - 0-7, then all but the finale)
    ok(all(r['ai'] <= {0: 3, 1: 7}.get(r['st'], 14) for r in jv_c), "mixed: Jevil's attacks from his phases for the stage (%r)" % [(r['st'], r['ai']) for r in jv_c])


NAMES = ['Chaos Teleport', 'Ring-Around', 'Heart Bombs', 'Devilsknife', 'Carousel', 'Club Bombs', 'Diamond Rain', 'Spade Spin',
         'Carousel Race', 'Spade Bombs', 'Dark Clubs', 'Devilsknife Swing', 'Teleport Frenzy', 'Chaos Bombs', 'Diamond Storm', 'BYE-BYE']

if __name__ == '__main__':
    t0 = time.time()
    if len(sys.argv) > 1 and sys.argv[1] == 'mixed':
        a, b = 'mixed', ''
        mixed()
    else:
        a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 15)
        for ai in range(a, b + 1):
            run_attack(ai)
    json.dump(RES, open('/home/claude/work/online/jevil_sweep_%s_%s.json' % (a, b), 'w'), indent=1)
    print('jevil52 %s-%s: %d checks, %d failed (%.0fs)' % (a, b, N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
