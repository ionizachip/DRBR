"""DRBR: FLOWERY (Chapter 5) - each of his 13 attacks (Chapter 5's own pieces, obj_fl_*: the orange SOUL, its board, the bamboo,
the Jarona lunges, the friends' attacks) in a practice match (the emulator: the real merged code, a mocked engine, the
collision / animation / motion / geometry models of collide.py, anim.py, bbox_model.py, geom.py), one match per attack, the
attack forced as every cycle's; the battle camera away from the room's corner (KH_CAM) so code that takes the camera for 0, 0
shows. Two players: IDLE (never touches a key) and DASHER (holds the confirm key 12 frames, lets go, every 26 frames - the
charge, the dash, the parries and the breaks run). Checked for each:
  - it starts at the shared tick, the ORANGE SOUL is up (obj_fl_soul and its board), it ends by its cut with no error and no
    frame run twice;
  - Chapter 5's own turn end (its pieces' end writes, noted by kbr_fl_done) comes within its length, or its pieces are all
    gone before the cut;
  - nothing of it is left after the cut, the red SOUL is back (visible, moving again), the box as it was, Flowery back in his
    place and seen; no knight on stage.
Usage: python3 t_flowery53.py [first last] [--dash]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

FAILS = []
N = [0]
RES = {}
OK_F = 8   # Flowery's online id (the roster's row)


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


PIECES = ('["obj_fl_soul", "obj_fl_ctrl", "obj_fl_wall", "obj_fl_bullet", "obj_fl_word", "obj_fl_orbit", "obj_fl_pad", "obj_fl_thorns", "obj_fl_bloom", '
          '"obj_fl_jarona", "obj_fl_box", "obj_fl_book", "obj_fl_pickup", "obj_fl_wordflower", "obj_fl_beam", "obj_fl_mfancy", "obj_fl_mfog", "obj_fl_mcenter", "obj_fl_particle"]')
LEFT = '(function(){ var _o = {}; var _l = %s; for (var _i = 0; _i < array_length(_l); _i++) { var _n = instance_number(asset_get_index(_l[_i])); if (_n > 0) variable_struct_set(_o, _l[_i], _n); } return _o; })()' % PIECES
NAMES = ['Bamboo Run', 'Jarona!', 'Thorn Chase', 'Petal Jarona', "Seth's Book", "Aqua's Knives", "Seth's Book II", 'Tag Team', 'Just Kidding!',
         'Cactus Chase', 'Justice Chase', 'Max Jarona', 'The Final Jarona']


def run_attack(ai, dash=False):
    sim, e = br_match(open_ok=OK_F, kn=(OK_F,), seed=SEED0 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, 'attack %d: practice with Flowery only (%s)' % (ai, e)):
        return
    live_input(sim)
    sim.load_source('gml_GlobalScript_t_dasher', DASHER)
    sim.run('global.JV_FORCE = %d;' % ai)
    sim.load_source('gml_GlobalScript_flforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    t0 = time.time()
    started = ended = -1
    why = ''
    err = None
    tt0 = None
    orange = 0
    dashes = 0
    dprev = 0
    box0 = None
    hits0 = J(sim, 'global.kfo.M.hits')
    h0 = collide.STATS['heart']
    for f in range(2600):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        if dash and started >= 0:
            # the DASHER plays like a person: lines up with the nearest blue piece / Jarona ahead, holds Z (the charge) and lets
            # go when it is close (the dash) - kbr_t_dasher
            w = J(sim, 'kbr_t_dasher()')
            keys_set(sim, ok=w[0], up=w[1], down=w[2])
        elif dash:
            keys_set(sim, ok=0, up=0, down=0)
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
            box0 = J(sim, 'instance_exists(obj_growtangle) ? [round(obj_growtangle.x), round(obj_growtangle.y), obj_growtangle.image_xscale, obj_growtangle.image_yscale] : []')
        if started >= 0 and ended < 0 and J(sim, 'instance_exists(obj_fl_soul) && instance_exists(obj_fl_ctrl)'):
            orange += 1
            dn = J(sim, 'obj_fl_soul.dashing ? 1 : 0')
            if dn and not dprev:
                dashes += 1
            dprev = dn
        if started >= 0 and b['k'] >= 1:
            ended = f
            why = b['cut']
            break
    keys_set(sim, ok=0, up=0, down=0)
    ch5 = J(sim, 'variable_global_exists("kbr_fl_end") ? global.kbr_fl_end : -2') if err is None else None
    left = J(sim, LEFT) if err is None and ended >= 0 else None
    soul = J(sim, 'instance_exists(obj_heart) ? [obj_heart.visible, variable_instance_exists(obj_heart, "canmove") ? obj_heart.canmove : -1, sprite_get_name(obj_heart.sprite_index)] : []') if err is None else None
    box1 = J(sim, 'instance_exists(obj_growtangle) ? [round(obj_growtangle.x), round(obj_growtangle.y), obj_growtangle.maxxscale, obj_growtangle.maxyscale, obj_growtangle.image_xscale, obj_growtangle.image_yscale] : []') if err is None else None
    keep = J(sim, '[instance_number(obj_fl_flowery), instance_exists(obj_fl_flowery) ? obj_fl_flowery.visible : -1, instance_number(obj_knight_enemy), instance_number(obj_fl_towery)]') if err is None else None
    hits = (J(sim, 'global.kfo.M.hits') - hits0) if err is None else None
    flm = J(sim, 'variable_struct_exists(global.kfo.M, "flm") ? global.kfo.M.flm : [-2, 0]') if err is None else None
    RES[ai] = {'started': started, 'ended': ended, 'frames': (ended - started) if ended >= 0 else -1, 'ch5': ch5, 'why': why, 'tt0': tt0,
               'orange': orange, 'dashes': dashes, 'flm': flm, 'left': left, 'soul': soul, 'box': [box0, box1], 'keep': keep, 'hits': hits, 'contacts': collide.STATS['heart'] - h0,
               'err': err[:300] if err else None, 'retry': getattr(sim, 'retrylog', [])[:2], 'wall': round(time.time() - t0)}
    print('attack', ai, 'dash' if dash else 'idle', json.dumps(RES[ai]), flush=True)
    nm = NAMES[ai] + (' (dasher)' if dash else '')
    ok(err is None, 'attack %d (%s): no error %s' % (ai, nm, (err or '')[:240]))
    ok(started >= 0, 'attack %d: it started (frame %d)' % (ai, started))
    ok(ended >= 0 and why in ('end', 'next'), 'attack %d: it ended (%s after %d frames)' % (ai, why, ended - started))
    ok(orange > 0, 'attack %d: the orange SOUL and its board were up (%d frames)' % (ai, orange))
    ok(ch5 is not None and (ch5 == -1 or 0 <= ch5 <= (tt0 or 0) + 2), 'attack %d: Chapter 5 would have ended it at %s, within its length (%s)' % (ai, ch5, tt0))
    ok(left == {}, 'attack %d: nothing of it left after it %r' % (ai, left))
    ok(soul is not None and soul[:2] == [True, 1], 'attack %d: the red SOUL is back (seen, moving) %r' % (ai, soul))
    # (Flowery widened it at the arm and moved it 5 px left: the next attack gets the knights' box back - its place, 2 x 2)
    ok(box0 is not None and box1 is not None and len(box1) == 6 and box1[0] == box0[0] + 5 and box1[1] == box0[1] and box1[2:] == [2, 2, 2, 2], 'attack %d: the box is the knights\' again %r' % (ai, [box0, box1]))
    ok(keep is not None and keep[0] == 1 and keep[1] and keep[2] == 0 and keep[3] == 1, 'attack %d: Flowery (seen) and his tower, no knight %r' % (ai, keep))
    ok(not getattr(sim, 'retrylog', []), 'attack %d: no frame run twice %r' % (ai, getattr(sim, 'retrylog', [])[:2]))
    # the orange SOUL's own play: the dasher dashes; the attack's FLOWERY TP went out for the GROUP MERCY (its cycle, 0 for the idle)
    if dash:
        ok(dashes >= 1, 'attack %d: the dasher dashed (%d dashes)' % (ai, dashes))
    # (Seth's boxes boost a SOUL that rides them and his word flowers are picked up by touch: TP without a key there)
    ok(flm is not None and flm[0] == 0 and ((flm[1] > 0) if dash else (flm[1] == 0 or ai in TP_IDLE)),
       'attack %d: its FLOWERY TP for the GROUP MERCY %r' % (ai, flm))


DASHER = '''
function kbr_t_dasher()
{
    if (!instance_exists(obj_fl_soul))
        return [0, 0, 0];
    var _sx = obj_fl_soul.x;
    var _sy = obj_fl_soul.y;
    var _best = 9999;
    var _ty = _sy;
    with (obj_fl_jarona)
    {
        var _d = bbox_left - _sx;
        if (visible && _d > -20 && _d < _best)
        {
            _best = _d;
            _ty = _sy;
        }
    }
    with (obj_fl_wall)
    {
        if (breakable)
        {
            var _d2 = bbox_left - _sx;
            if (_d2 > -10 && _d2 < _best)
            {
                _best = _d2;
                _ty = (bbox_top + bbox_bottom) / 2;
            }
        }
    }
    with (obj_fl_bullet)
    {
        if (breakable)
        {
            var _d3 = bbox_left - _sx;
            if (_d3 > -10 && _d3 < _best)
            {
                _best = _d3;
                _ty = y;
            }
        }
    }
    // Aqua's lilypads: dash onto them (the jump over her knives)
    with (obj_fl_pad)
    {
        var _d4 = bbox_left - _sx;
        if (_d4 > -10 && _d4 < _best)
        {
            _best = _d4;
            _ty = (bbox_top + bbox_bottom) / 2;
        }
    }
    return [(_best > 70) ? 1 : 0, (_ty < (_sy - 6)) ? 1 : 0, (_ty > (_sy + 6)) ? 1 : 0];
}
'''

SEED0 = 5800
TP_IDLE = (4, 6)   # Seth's Book I / II: his boxes' boosters dash for you, his word flowers are touched

if __name__ == '__main__':
    t0 = time.time()
    dash = '--dash' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    a, b = (int(args[0]), int(args[1])) if len(args) > 1 else (0, 12)
    for ai in range(a, b + 1):
        run_attack(ai, dash)
    json.dump(RES, open('/home/claude/work/online/flowery_sweep_%s_%s%s.json' % (a, b, '_dash' if dash else ''), 'w'), indent=1)
    print('flowery53 %s-%s: %d checks, %d failed (%.0fs)' % (a, b, N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
