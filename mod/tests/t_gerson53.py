"""DRBR: GERSON, the Hammer of Justice (Chapter 4) - every one of his 19 attacks (his own Chapter 4 pieces, obj_hj_*) in a
practice match (the emulator: the real merged code, a mocked engine, SOUL / bullet collisions on), one match per attack, the
attack forced as every cycle's:
  - it starts at the shared tick; his shot list runs (a green attack puts the shield up: the SOUL turns green and is pulled to
    the box's middle); it ends by its cut with no error;
  - its natural end (the list done, no spear / controller left) comes before its length (tt) - the length is long enough;
  - nothing of it is left after the cut, the SOUL is red again (color 0, spr_dodgeheart, alpha 1), the box is as it was;
  - Gerson, his background (on) stay; no knight on stage.
Usage: python3 t_gerson53.py [first last] | mixed"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

FAILS = []
N = [0]
RES = {}
OK_G = 7   # Gerson's online id (the roster's row)


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


PIECES = ('["obj_hj_spear", "obj_hj_shield", "obj_hj_shieldpiece", "obj_hj_switch", "obj_hj_chevron", "obj_hj_fakeheart", "obj_hj_teleport", "obj_hj_swing", '
          '"obj_hj_swing2", "obj_hj_swinghit", "obj_hj_column", "obj_hj_squish", "obj_hj_boxthrow", "obj_hj_hammer", "obj_hj_shellkick", "obj_hj_pinball", '
          '"obj_hj_boxshrink", "obj_hj_jumparc", "obj_hj_tpfx", "obj_hj_note", "obj_hj_bell", "obj_hj_bellhit"]')
LEFT = '(function(){ var _o = {}; var _l = %s; for (var _i = 0; _i < array_length(_l); _i++) { var _n = instance_number(asset_get_index(_l[_i])); if (_n > 0) variable_struct_set(_o, _l[_i], _n); } return _o; })()' % PIECES
BUSY = '(function(){ var _g = instance_find(obj_hj_gerson, 0); if (_g == noone) return -1; var _b = (_g.attackcon == 1 || _g.attackcon == 2) ? 1 : 0; if (instance_exists(obj_hj_spear) || instance_exists(obj_hj_boxthrow) || instance_exists(obj_hj_shellkick) || instance_exists(obj_hj_pinball) || instance_exists(obj_hj_squish) || instance_exists(obj_hj_swing) || instance_exists(obj_hj_swing2)) _b = 1; return _b; })()'


def run_attack(ai, chase=False):
    sim, e = br_match(open_ok=OK_G, kn=(OK_G,), seed=SEED0 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, 'attack %d: practice with Gerson only (%s)' % (ai, e)):
        return
    sim.run('global.JV_FORCE = %d;' % ai)
    sim.load_source('gml_GlobalScript_hjforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    t0 = time.time()
    started = ended = natural = -1
    why = ''
    err = None
    tt0 = None
    green = 0
    box0 = None
    my = J(sim, 'global.kfo.my')
    h0 = collide.STATS['heart']
    hits0 = J(sim, 'global.kfo.M.hits')
    for f in range(2200):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        if chase:
            collide.chase(sim, lambda b: b.vars.get('visible', True) and not ('kbrt' in b.vars and b.vars.get('kbrt') != my))
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
            box0 = J(sim, 'instance_exists(obj_growtangle) ? [obj_growtangle.image_xscale, obj_growtangle.image_yscale, obj_growtangle.image_angle] : []')
        if started >= 0 and natural < 0 and f > started + 3 and J(sim, BUSY) == 0:
            natural = f - started
        if started >= 0 and ended < 0 and J(sim, 'instance_exists(obj_heart) && obj_heart.sprite_index == spr_hj_greenheart'):
            green += 1
        if started >= 0 and b['k'] >= 1:
            ended = f
            why = b['cut']
            break
    # where Chapter 4 would have ended this turn (its pieces' end writes, noted by kbr_hj_done; frames from the attack's start)
    ch4 = J(sim, 'variable_global_exists("kbr_hj_end") ? global.kbr_hj_end : -2') if err is None else None
    left = J(sim, LEFT) if err is None and ended >= 0 else None
    soul = J(sim, 'instance_exists(obj_heart) ? [obj_heart.color, sprite_get_name(obj_heart.sprite_index), obj_heart.image_alpha] : []') if err is None else None
    box1 = J(sim, 'instance_exists(obj_growtangle) ? [obj_growtangle.image_xscale, obj_growtangle.image_yscale, obj_growtangle.image_angle] : []') if err is None else None
    keep = J(sim, '[instance_number(obj_hj_gerson), instance_number(obj_hj_bg), instance_exists(obj_hj_bg) ? obj_hj_bg.on : -1, instance_number(obj_knight_enemy)]') if err is None else None
    bfix = J(sim, 'variable_global_exists("kbr_bfix") ? global.kbr_bfix : {}') if err is None else None
    hits = J(sim, 'global.kfo.M.hits') - hits0 if err is None else None
    RES[ai] = {'started': started, 'ended': ended, 'frames': (ended - started) if ended >= 0 else -1, 'natural': natural, 'ch4': ch4, 'why': why, 'tt0': tt0,
               'green_frames': green, 'left': left, 'soul': soul, 'box': [box0, box1], 'keep': keep, 'contacts': collide.STATS['heart'] - h0, 'hits': hits, 'bfix': bfix,
               'err': err[:300] if err else None, 'wall': round(time.time() - t0)}
    print('attack', ai, json.dumps(RES[ai]), flush=True)
    nm = NAMES[ai]
    ok(err is None, 'attack %d (%s): no error %s' % (ai, nm, (err or '')[:240]))
    ok(started >= 0, 'attack %d: it started (frame %d)' % (ai, started))
    ok(ended >= 0 and why in ('end', 'next'), 'attack %d: it ended (%s after %d frames)' % (ai, why, ended - started))
    ok(natural >= 0 and (tt0 is None or natural <= tt0 + 2), 'attack %d: its own end (%d frames) fits its length (%s)' % (ai, natural, tt0))
    # Chapter 4's own turn end came before the cut: the length is long enough for the whole attack
    ok(ch4 is not None and 0 <= ch4 <= (tt0 or 0) + 2, 'attack %d: Chapter 4 would have ended it at %s, within its length (%s)' % (ai, ch4, tt0))
    if ai in GREEN:
        ok(green > 0, 'attack %d: the green SOUL was up (%d frames)' % (ai, green))
    ok(left == {}, 'attack %d: nothing of it left after it %r' % (ai, left))
    ok(soul == [0, 'spr_dodgeheart', 1], 'attack %d: the SOUL is red again %r' % (ai, soul))
    ok(box0 is not None and box1 == box0, 'attack %d: the box is as it was %r' % (ai, [box0, box1]))
    ok(keep is not None and keep[0] == 1 and keep[1] == 1 and keep[2] == 1 and keep[3] == 0, 'attack %d: Gerson and his background (on), no knight %r' % (ai, keep))
    ok(bfix == {}, 'attack %d: no bullet needed the contract\'s fallback %r' % (ai, bfix))
    # the emulator ran every frame once (no frame re-run after a missing function / global: that would skip a frame's events)
    ok(not getattr(sim, 'retrylog', []), 'attack %d: no frame re-run %r' % (ai, getattr(sim, 'retrylog', [])[:2]))


NAMES = ['Green Switch', 'Spear Lesson', 'Crossfire', 'Diagonals', 'Red Hammer', 'Shell Kick', 'Hammer Toss', 'Diagonal Barrage', 'Shell Bounce',
         'Shell Storm', 'Hammer Swings', 'Box Squish', 'Double Bounce', 'Shell Gauntlet', 'Spiral', 'Random Rush', 'Slow Flood', 'Shell Medley',
         'Final Rounds']
GREEN = {0, 1, 2, 3, 4, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18}

SEED0 = 5300

if __name__ == '__main__':
    t0 = time.time()
    chase = '--chase' in sys.argv
    for a in sys.argv[1:]:
        if a.startswith('--seed='):
            SEED0 = int(a[7:])
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    a, b = (int(args[0]), int(args[1])) if len(args) > 1 else (0, 18)
    for ai in range(a, b + 1):
        run_attack(ai, chase)
    json.dump(RES, open('/home/claude/work/online/gerson_sweep_%s_%s%s_s%d.json' % (a, b, '_chase' if chase else '', SEED0), 'w'), indent=1)
    print('gerson53 %s-%s: %d checks, %d failed (%.0fs)' % (a, b, N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
