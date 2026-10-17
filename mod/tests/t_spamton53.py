"""DRBR: SPAMTON NEO (Chapter 2) - every one of his 15 attacks (his own Chapter 2 pieces, obj_sn_*) in a practice match (the
emulator: the real merged code, a mocked engine, SOUL / bullet collisions on, the SOUL's keys real - live_input), one match
per attack, the attack forced as every cycle's. Two players:
  idle    - never shoots: the attack runs Chapter 2's full length (its own turn timer: the time measured here is its tt);
  shooter - lines up with his pieces and shoots (taps, then a held BIG SHOT): the shots break what Chapter 2 lets them break,
            and an attack Chapter 2 ends early (the big heart, the face, the pipis) ends early in this game only.
Each run:
  - it starts at the shared tick; the SOUL is yellow while it runs (spr_yellowheart, the driver on); it ends by its cut with
    no error; idle: by its own turn timer ("end") within its place in the timeline (tt);
  - nothing of it is left after the cut, the SOUL is red again (spr_dodgeheart, alpha 1), the box is back (the default box);
  - Spamton, his background (on), the yellow SOUL's driver stay; no knight on stage; no bullet needed the contract's fallback;
    no frame was re-run.
Usage: python3 t_spamton53.py [first last] [--idle | --shoot]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

FAILS = []
N = [0]
RES = {}
OK_S = 9   # Spamton NEO's online id (the roster's row)


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


PIECES = ['obj_sn_bc', 'obj_sn_guymaker', 'obj_sn_lilguy', 'obj_sn_lilbullet', 'obj_sn_biglaser', 'obj_sn_laserfhb', 'obj_sn_armtel', 'obj_sn_cannonshot',
          'obj_sn_dissolve', 'obj_sn_bullet', 'obj_sn_bulletfin', 'obj_sn_wallctrl', 'obj_sn_wallcell', 'obj_sn_wallbomb', 'obj_sn_bombhit', 'obj_sn_wireheart',
          'obj_sn_heartlaser', 'obj_sn_laser', 'obj_sn_heartbomb', 'obj_sn_heatbullet', 'obj_sn_phonecall', 'obj_sn_headstream', 'obj_sn_headpuff',
          'obj_sn_pipthrow', 'obj_sn_pipegg', 'obj_sn_pipcone', 'obj_sn_pipfx', 'obj_sn_pippiece', 'obj_sn_pipwall', 'obj_sn_armsmoke', 'obj_sn_handhead',
          'obj_sn_phonehand', 'obj_sn_spreadshot', 'obj_sn_face', 'obj_sn_facetarget', 'obj_sn_eyelaser', 'obj_sn_eyelaserseg', 'obj_sn_crescent',
          'obj_sn_finalebox', 'obj_sn_warpbox', 'obj_sn_forme', 'obj_sn_formehit', 'obj_sn_formemouth', 'obj_sn_dollar', 'obj_sn_fakeheart', 'obj_sn_playback',
          'obj_sn_lastattack', 'obj_sn_lasthit', 'obj_sn_bigshot', 'obj_sn_smoke', 'obj_sn_finalorb', 'obj_sn_yshot', 'obj_sn_yshotanim', 'obj_sn_ytrail',
          'obj_sn_yspark', 'obj_sn_superend']
LEFT = '(function(){ var _o = {}; var _l = %s; for (var _i = 0; _i < array_length(_l); _i++) { var _a = asset_get_index(_l[_i]); if (_a < 0) continue; var _n = instance_number(_a); if (_n > 0) variable_struct_set(_o, _l[_i], _n); } return _o; })()' % json.dumps(PIECES)
# what a yellow SOUL shoots at (the shooter lines up with the nearest)
TARGETS = ('obj_sn_wireheart', 'obj_sn_pipegg', 'obj_sn_face', 'obj_sn_wallcell', 'obj_sn_handhead', 'obj_sn_formehit', 'obj_sn_forme', 'obj_sn_finalorb',
           'obj_sn_lilguy', 'obj_sn_dollar', 'obj_sn_bigshot', 'obj_sn_lasthit')

NAMES = ['Flying Heads', 'RECREW Columns', 'Heart Attack', 'Pipis Call', 'Phonehands', 'Look In My Eyes', 'Heart Attack II', 'BIG SHOT Dance',
         'Look In My Eyes II', 'Phonehands II', 'Pipis Call II', 'RECREW Columns II', 'Heart Attack III', 'Pipis Call III', 'NEO Finale']
SEED0 = 5300


def aim(sim):
    """the shooter's SOUL: on the height of the nearest target to its right (inside the box)"""
    hs = [i for i in sim.instances_of('obj_heart') if not i.dead] if 'obj_heart' in sim.objects else []
    if not hs:
        return
    h = hs[0]
    hx = float(h.vars.get('x', 0))
    best = None
    for o in TARGETS:
        if o not in sim.objects:
            continue
        for b in sim.instances_of(o):
            if b.dead:
                continue
            bx = float(b.vars.get('x', 0))
            if bx < hx:
                continue
            if best is None or bx - hx < best[0]:
                best = (bx - hx, float(b.vars.get('y', 0)))
    if best is None:
        return
    box = J(sim, 'instance_exists(obj_growtangle) ? [obj_growtangle.y - (obj_growtangle.sprite_height / 2), obj_growtangle.y + (obj_growtangle.sprite_height / 2)] : []')
    ty = best[1] - 10
    if box:
        ty = max(box[0] + 2, min(box[1] - 22, ty))
    h.vars['y'] = ty


def run_attack(ai, mode):
    sim, e = br_match(open_ok=OK_S, kn=(OK_S,), seed=SEED0 + ai, bots=0, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, 'attack %d %s: practice with Spamton NEO only (%s)' % (ai, mode, e)):
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
        z = 0
        if mode == 'shoot' and started >= 0 and ended < 0:
            aim(sim)
            ph = (f - started) % 90
            z = 1 if (ph < 60 and ph % 6 < 2) or (60 <= ph < 89) else 0
        keys_set(sim, ok=z)
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
            yy = J(sim, '[kbr_sn_yellow_on() && instance_exists(obj_heart) && obj_heart.sprite_index == spr_yellowheart, instance_exists(obj_sn_fakeheart)]')
            yellow += 1 if yy[0] else 0
            # (the final forme swallows the SOUL - Chapter 2's fake heart: the SOUL is not yellow while it is gone)
            fake += 1 if yy[1] else 0
        if started >= 0 and b['k'] >= 1:
            ended = f
            why = b['cut']
            break
    if err is None and ended >= 0:
        # the SOUL's yellow pieces this run (the driver's counts) and what is left after the cut
        sb = J(sim, '[obj_sn_ysoul.shots, obj_sn_ysoul.bigs]')
        shots, bigs = sb[0], sb[1]
    left = J(sim, LEFT) if err is None and ended >= 0 else None
    soul = J(sim, 'instance_exists(obj_heart) ? [obj_heart.color, sprite_get_name(obj_heart.sprite_index), obj_heart.image_alpha, kbr_sn_yellow_on()] : []') if err is None else None
    box1 = J(sim, 'instance_exists(obj_growtangle) ? [obj_growtangle.x - camerax(), obj_growtangle.y - cameray(), obj_growtangle.maxxscale, obj_growtangle.maxyscale] : []') if err is None else None
    keep = J(sim, '[instance_number(obj_sn_neo), instance_number(obj_sn_bg), instance_exists(obj_sn_bg) ? (obj_sn_bg.a > 0) : -1, instance_number(obj_sn_ysoul), instance_number(obj_knight_enemy)]') if err is None else None
    bfix = J(sim, 'variable_global_exists("kbr_bfix") ? global.kbr_bfix : {}') if err is None else None
    hits = J(sim, 'global.kfo.M.hits') - hits0 if err is None else None
    frames = (ended - started) if ended >= 0 else -1
    RES['%d_%s' % (ai, mode)] = {'started': started, 'ended': ended, 'frames': frames, 'why': why, 'tt0': tt0, 'slot': slot, 'yellow_frames': yellow, 'fake': fake, 'shots': shots,
                                 'bigs': bigs, 'left': left, 'soul': soul, 'box': box1, 'keep': keep, 'contacts': collide.STATS['heart'] - h0, 'hits': hits,
                                 'bfix': bfix, 'err': err[:400] if err else None, 'wall': round(time.time() - t0)}
    print('attack', ai, mode, json.dumps(RES['%d_%s' % (ai, mode)]), flush=True)
    nm = NAMES[ai]
    ok(err is None, 'attack %d %s (%s): no error %s' % (ai, mode, nm, (err or '')[:300]))
    ok(started >= 0, 'attack %d %s: it started (frame %d)' % (ai, mode, started))
    ok(ended >= 0 and why in ('end', 'next'), 'attack %d %s: it ended (%s after %d frames)' % (ai, mode, why, frames))
    if mode == 'idle':
        # Chapter 2's own end (its turn timer) inside its place in the timeline: the place is long enough for the whole attack
        ok(why == 'end' and slot is not None and frames <= slot, 'attack %d idle: Chapter 2 ends it itself (%s, %d frames) within its place (%s)' % (ai, why, frames, slot))
    else:
        ok(shots > 0 and bigs > 0, 'attack %d shoot: the yellow SOUL fired (%d shots, %d BIG SHOTs)' % (ai, shots, bigs))
        ok(slot is not None and frames <= slot + 2, 'attack %d shoot: it ended within its place (%d <= %s)' % (ai, frames, slot))
    ok(yellow > 0 and yellow >= frames - 4 - fake, 'attack %d %s: the SOUL was yellow all the attack (%d of %d frames; %d swallowed)' % (ai, mode, yellow, frames, fake))
    ok(left == {}, 'attack %d %s: nothing of it left after it %r' % (ai, mode, left))
    ok(soul is not None and soul[1:] == ['spr_dodgeheart', 1, False] and soul[0] == 0, 'attack %d %s: the SOUL is red again %r' % (ai, mode, soul))
    ok(box1 is not None and box1 == [245, 170, 2, 2], 'attack %d %s: the box is back to the battle\'s %r' % (ai, mode, box1))
    ok(keep is not None and keep[0] == 1 and keep[1] == 1 and keep[2] == True and keep[3] == 1 and keep[4] == 0, 'attack %d %s: Spamton, his background (on), the driver; no knight %r' % (ai, mode, keep))
    ok(bfix == {}, 'attack %d %s: no bullet needed the contract\'s fallback %r' % (ai, mode, bfix))
    ok(not getattr(sim, 'retrylog', []), 'attack %d %s: no frame re-run %r' % (ai, mode, getattr(sim, 'retrylog', [])[:2]))


if __name__ == '__main__':
    t0 = time.time()
    modes = ['idle', 'shoot']
    if '--idle' in sys.argv:
        modes = ['idle']
    if '--shoot' in sys.argv:
        modes = ['shoot']
    for a in sys.argv[1:]:
        if a.startswith('--seed='):
            SEED0 = int(a[7:])
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    a, b = (int(args[0]), int(args[1])) if len(args) > 1 else (0, 14)
    for ai in range(a, b + 1):
        for m in modes:
            run_attack(ai, m)
    json.dump(RES, open('/home/claude/work/online/spamton_sweep_%s_%s_%s_s%d.json' % (a, b, '_'.join(modes), SEED0), 'w'), indent=1)
    print('spamton53 %s-%s: %d checks, %d failed (%.0fs)' % (a, b, N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
