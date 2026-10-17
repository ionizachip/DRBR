"""DRBR: PINK (Chapter 5) - every one of her 19 attacks (her own Chapter 5 pieces, obj_pk_*) in a practice match (the emulator: the
real merged code, a mocked engine, SOUL / bullet collisions on, the SOUL's keys real - live_input), one match per attack, the
attack forced as every cycle's. Two players:
  idle  - never touches a key: the attack runs Chapter 5's full length (its own turn timer: the time measured here is its tt);
  mover - changes lane / node every few frames (the arrows, as a player would), collects what comes to it.
Each run:
  - it starts at the shared tick; the SOUL is purple while it runs (her purple controls on) - except her concert (type 209: a
    red SOUL on the stage); it ends by its cut with no error; idle: by its own turn timer ("end") within its place (tt);
  - nothing of it is left after the cut, the SOUL is itself again (spr_dodgeheart, visible, can move, alpha 1, scale 1);
  - Pink, her stage (on) stay; no knight on stage; no bullet needed the contract's fallback; no frame was re-run.
Usage: python3 t_pink53.py [first last] [--idle | --move]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

FAILS = []
N = [0]
RES = {}
OK_S = 10   # Pink's online id (the roster's row)


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


PIECES = ['obj_pk_dbc', 'obj_pk_purple', 'obj_pk_move', 'obj_pk_cat', 'obj_pk_doki', 'obj_pk_bomb', 'obj_pk_bigbomb', 'obj_pk_boom', 'obj_pk_smoke',
          'obj_pk_chargeball', 'obj_pk_chargestar', 'obj_pk_lanebullet', 'obj_pk_face', 'obj_pk_meteor', 'obj_pk_flamebit', 'obj_pk_rollbg', 'obj_pk_zap',
          'obj_pk_rim', 'obj_pk_zapring', 'obj_pk_curtains', 'obj_pk_fan', 'obj_pk_fanheart', 'obj_pk_hater', 'obj_pk_dust', 'obj_pk_trail', 'obj_pk_ripple',
          'obj_pk_sweat', 'obj_pk_tea', 'obj_pk_node', 'obj_pk_nodeact', 'obj_pk_bell', 'obj_pk_sparkle', 'obj_pk_saw', 'obj_pk_healheart']
LEFT = '(function(){ var _o = {}; var _l = %s; for (var _i = 0; _i < array_length(_l); _i++) { var _a = asset_get_index(_l[_i]); if (_a < 0) continue; var _n = instance_number(_a); if (_n > 0) variable_struct_set(_o, _l[_i], _n); } return _o; })()' % json.dumps(PIECES)

NAMES = ['Kitty Lanes', 'Bomb Grid', 'Kitty Lanes + Bombs', 'Heart Bombs', 'Mewers Live!', 'Kitty Mix', 'Rolling Box', '3D Tunnel', 'Bomb Grid II',
         'Mewers Live! Encore', 'Rolling Box Bursts', 'Ghost Face Push', 'Big Bomb Storm', 'Kitty Conga', '3D Tunnel II', 'Kitty Rush', 'Bomb Chain',
         'Mewers Live! Finale', 'Final Date']
TYPES = [200, 203, 200, 203, 209, 200, 202, 208, 203, 209, 202, 202, 203, 200, 208, 200, 203, 209, 210]
SEED0 = 5300
# the mover's keys: a lane change every 9 frames, round the four directions (one press each), with the odd pause
MOVES = ['up', 'left', 'down', 'right', None, 'down', 'right', 'up', 'left', None]


def run_attack(ai, mode):
    sim, e = br_match(open_ok=OK_S, kn=(OK_S,), seed=SEED0 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, 'attack %d %s: practice with Pink only (%s)' % (ai, mode, e)):
        return
    live_input(sim)
    sim.run('global.JV_FORCE = %d;' % ai)
    sim.load_source('gml_GlobalScript_snforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    t0 = time.time()
    started = ended = -1
    why = ''
    err = None
    tt0 = None
    slot = None
    yellow = 0
    fake = 0
    box_def = None
    shots = bigs = 0
    h0 = collide.STATS['heart']
    hits0 = J(sim, 'global.kfo.M.hits')
    left_mid = None
    for f in range(2600):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        # the keys: the shooter taps Z every 6 frames for 60 frames, then holds it 30 frames and lets go (a BIG SHOT)
        kk = {'up': 0, 'down': 0, 'left': 0, 'right': 0}
        if mode == 'move' and started >= 0 and ended < 0 and (f - started) % 9 < 2:
            mv = MOVES[((f - started) // 9) % len(MOVES)]
            if mv:
                kk[mv] = 1
        keys_set(sim, **kk)
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
            slot = J(sim, 'kbr_tl_get(global.kfo.M.tl, 0).dur')
        if started >= 0 and ended < 0:
            yy = J(sim, '[instance_exists(obj_pk_purple) && kbr_soul_mode() == "purple"]')
            yellow += 1 if yy[0] else 0
        if started >= 0 and b['k'] >= 1:
            ended = f
            why = b['cut']
            break
    left = J(sim, LEFT) if err is None and ended >= 0 else None
    soul = J(sim, 'instance_exists(obj_heart) ? [sprite_get_name(obj_heart.sprite_index), obj_heart.visible, obj_heart.canmove, obj_heart.image_alpha, obj_heart.image_xscale, kbr_pk_purple_on()] : []') if err is None else None
    box1 = J(sim, 'instance_exists(obj_growtangle) ? [obj_growtangle.x - camerax(), obj_growtangle.y - cameray(), obj_growtangle.maxxscale, obj_growtangle.maxyscale] : []') if err is None else None
    keep = J(sim, '[instance_number(obj_pk_pink), instance_number(obj_pk_bg), instance_exists(obj_pk_bg) ? (obj_pk_bg.a > 0) : -1, 1, instance_number(obj_knight_enemy)]') if err is None else None
    bfix = J(sim, 'variable_global_exists("kbr_bfix") ? global.kbr_bfix : {}') if err is None else None
    hits = J(sim, 'global.kfo.M.hits') - hits0 if err is None else None
    frames = (ended - started) if ended >= 0 else -1
    RES['%d_%s' % (ai, mode)] = {'started': started, 'ended': ended, 'frames': frames, 'why': why, 'tt0': tt0, 'slot': slot, 'purple_frames': yellow, 'left': left, 'soul': soul, 'box': box1, 'keep': keep, 'contacts': collide.STATS['heart'] - h0, 'hits': hits,
                                 'bfix': bfix, 'err': err[:400] if err else None, 'wall': round(time.time() - t0)}
    print('attack', ai, mode, json.dumps(RES['%d_%s' % (ai, mode)]), flush=True)
    nm = NAMES[ai]
    ok(err is None, 'attack %d %s (%s): no error %s' % (ai, mode, nm, (err or '')[:300]))
    ok(started >= 0, 'attack %d %s: it started (frame %d)' % (ai, mode, started))
    ok(ended >= 0 and why in ('end', 'next'), 'attack %d %s: it ended (%s after %d frames)' % (ai, mode, why, frames))
    if mode == 'idle':
        # Chapter 2's own end (its turn timer) inside its place in the timeline: the place is long enough for the whole attack
        ok(why == 'end' and slot is not None and frames <= slot, 'attack %d idle: Chapter 5 ends it itself (%s, %d frames) within its place (%s)' % (ai, why, frames, slot))
    else:
        ok(slot is not None and frames <= slot + 2, 'attack %d move: it ended within its place (%d <= %s)' % (ai, frames, slot))
    if TYPES[ai] == 209:
        ok(yellow == 0, 'attack %d %s: her concert keeps the SOUL red (purple %d frames)' % (ai, mode, yellow))
    else:
        ok(yellow > 0 and yellow >= frames - 30, 'attack %d %s: the SOUL was purple all the attack (%d of %d frames)' % (ai, mode, yellow, frames))
    ok(left == {}, 'attack %d %s: nothing of it left after it %r' % (ai, mode, left))
    ok(soul is not None and soul == ['spr_dodgeheart', True, 1, 1, 1, False], 'attack %d %s: the SOUL is itself again %r' % (ai, mode, soul))
    ok(box1 is not None and box1 == [320, 170, 2, 2], 'attack %d %s: the box is back to the battle\'s %r' % (ai, mode, box1))
    ok(keep is not None and keep[0] == 1 and keep[1] == 1 and keep[2] == True and keep[4] == 0, 'attack %d %s: Pink, her stage (on); no knight %r' % (ai, mode, keep))
    ok(bfix == {}, 'attack %d %s: no bullet needed the contract\'s fallback %r' % (ai, mode, bfix))
    ok(not getattr(sim, 'retrylog', []), 'attack %d %s: no frame re-run %r' % (ai, mode, getattr(sim, 'retrylog', [])[:2]))


if __name__ == '__main__':
    t0 = time.time()
    modes = ['idle', 'move']
    if '--idle' in sys.argv:
        modes = ['idle']
    if '--move' in sys.argv:
        modes = ['move']
    for a in sys.argv[1:]:
        if a.startswith('--seed='):
            SEED0 = int(a[7:])
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    a, b = (int(args[0]), int(args[1])) if len(args) > 1 else (0, 18)
    for ai in range(a, b + 1):
        for m in modes:
            run_attack(ai, m)
    json.dump(RES, open('/home/claude/work/online/pink_sweep_%s_%s_%s_s%d.json' % (a, b, '_'.join(modes), SEED0), 'w'), indent=1)
    print('pink53 %s-%s: %d checks, %d failed (%.0fs)' % (a, b, N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
