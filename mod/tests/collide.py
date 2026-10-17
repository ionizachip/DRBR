"""DRBR: SOUL / bullet collisions in the emulator (it has none of its own - the reason the destroyonhit crash was not seen).

After each frame, as the runner does between Step and End Step:
  - every live bullet (obj_collidebullet or a child) whose collision box meets the SOUL's (obj_heart: spr_dodgeheartmask)
    runs obj_heart's "Collision with obj_collidebullet" event with other = that bullet - the real event (user event 5 of the
    bullet: scr_damage, destroyonhit ...);
  - the same against the graze box (obj_grazebox: spr_grazemask) runs obj_grazebox's collision event;
  - a bullet's own collision events with obj_heart / obj_grazebox (if it has one) run too.
Boxes: bbox_model (each sprite's / mask's real collision rectangle from the built data.win, turned with the instance; the
real masks lie inside it, so this hits at least as often as the game). Instances with a speed are moved by it (bbox_model.move)
when MOVE is on (the emulator does not move them itself).
Usage: collide.pump(sim) after each sim.step(1); collide.STATS counts the contacts."""
import bbox_model as BM
import anim

MOVE = True
ANIM = True     # sprite animation + Animation End (anim.py) - the runner's, which the emulator lacks
STATS = {'heart': 0, 'graze': 0, 'frames': 0}
_DESC = {}


def _is_bullet(sim, obj):
    r = _DESC.get(obj)
    if r is None:
        r = False
        try:
            r = 'obj_collidebullet' in sim.chain(obj)
        except Exception:
            r = obj == 'obj_collidebullet'
        _DESC[obj] = r
    return r


def _box(sim, inst):
    b = BM.box_of(sim, inst)
    return b


# what the real battle controller's Create sets and the emulator's stand-in battle does not (graze -> scr_tensionheal reads it)
_PREP = 'with (obj_battlecontroller) { if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0; }'


def pump(sim):
    STATS['frames'] += 1
    if 'obj_battlecontroller' in sim.objects:
        sim.run(_PREP)
    if ANIM:
        anim.tick(sim)
    if MOVE:
        BM.move_full(sim)
    hearts = [i for i in (sim.instances_of('obj_heart') if 'obj_heart' in sim.objects else []) if not i.dead]
    grazes = [i for i in (sim.instances_of('obj_grazebox') if 'obj_grazebox' in sim.objects else []) if not i.dead]
    n0 = pump_other(sim)
    if not hearts and not grazes:
        return n0
    bullets = [i for i in list(sim.instances.values()) if not i.dead and _is_bullet(sim, i.obj)]
    if not bullets:
        return 0
    n = 0
    for who, key, stat in [(h, 'obj_heart', 'heart') for h in hearts] + [(g, 'obj_grazebox', 'graze') for g in grazes]:
        if who.dead:
            continue
        hb = _box(sim, who)
        if hb is None:
            continue
        x1, y1, x2, y2 = hb
        for b in bullets:
            if b.dead or who.dead:
                continue
            q = BM.obb_of(sim, b)
            if q is None or not BM.obb_hits_rect(q, x1, y1, x2, y2):
                continue
            # the SOUL's (graze box's) event with the bullet, then the bullet's own event with the SOUL, as the runner pairs them
            sim.run_event(who, 'Collision', 'obj_collidebullet', other=b)
            if not b.dead:
                sim.run_event(b, 'Collision', key, other=who)
            STATS[stat] += 1
            n += 1
    return n


def chase(sim, want):
    """move the SOUL (obj_heart) so its mask's middle is on the middle of the first live bullet for which want(inst) is true
    (each bullet's real collision box, whatever its origin - a careless player stepping onto it). Returns the bullet or None."""
    hearts = [i for i in (sim.instances_of('obj_heart') if 'obj_heart' in sim.objects else []) if not i.dead]
    if not hearts:
        return None
    h = hearts[0]
    for b in list(sim.instances.values()):
        if b.dead or not _is_bullet(sim, b.obj):
            continue
        try:
            if not want(b):
                continue
        except Exception:
            continue
        bb = BM.box_of(sim, b)
        hb = BM.box_of(sim, h)
        if bb is None or hb is None:
            continue
        cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
        hx, hy = (hb[0] + hb[2]) / 2.0, (hb[1] + hb[3]) / 2.0
        h.vars['x'] = float(h.vars.get('x', 0)) + (cx - hx)
        h.vars['y'] = float(h.vars.get('y', 0)) + (cy - hy)
        return b
    return None


# DRBR: collisions between two pieces - the yellow SOUL's shots (Spamton NEO's fight: Chapter 2's "Collision with
# obj_yheart_shot" events, his copies obj_sn_yshot) and whatever has an event for them (a heart, an egg, a wall cell, his face):
# the runner's pairs, each frame, every instance (children too) of an object whose event (own or inherited) names the shot,
# against every live shot (and the shot's own event with it, when it has one). OTHER: the objects shot at.
OTHER = ('obj_sn_yshot',)
STATS['other'] = 0
_OEV = {}


def _other_objs(sim, tgt):
    """the objects with a Collision event against tgt (own or inherited), cached per object count"""
    k = (tgt, len(sim.objects))
    r = _OEV.get(k)
    if r is None:
        r = [o for o in list(sim.objects) if sim.find_event(o, ('Collision', tgt)) is not None]
        _OEV[k] = r
    return r


def pump_other(sim):
    n = 0
    for tgt in OTHER:
        if tgt not in sim.objects:
            continue
        shots = [i for i in sim.instances_of(tgt) if not i.dead]
        if not shots:
            continue
        seen = set()
        for o in _other_objs(sim, tgt):
            for a in [i for i in sim.instances.values() if i.obj == o and not i.dead]:
                if a.id in seen:
                    continue
                seen.add(a.id)
                qa = BM.obb_of(sim, a)
                if qa is None:
                    continue
                for s in shots:
                    if a.dead:
                        break
                    if s.dead:
                        continue
                    sb = _box(sim, s)
                    if sb is None or not BM.obb_hits_rect(qa, sb[0], sb[1], sb[2], sb[3]):
                        continue
                    sim.run_event(a, 'Collision', tgt, other=s)
                    if not s.dead and not a.dead and sim.find_event(s.obj, ('Collision', a.obj)) is not None:
                        sim.run_event(s, 'Collision', a.obj, other=a)
                    STATS['other'] += 1
                    n += 1
    return n
