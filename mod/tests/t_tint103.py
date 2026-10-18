"""DRBR 1.0.3 - your request: "make the sent attacks from the other bosses be tinted your soul color ... and actually look nice
when in attack ... like the actual graphic of the thing being sent". Every boss's attack skill landed in your box from a bot
whose SOUL colour is forced (an odd green, TCOL), at the real arena camera, every frame stepped and, on chosen frames, drawn
the game's way (Draw Begin / Draw / Draw End by depth, an instance with no Draw event drawing its sprite, draw_self too):
  - every picture a piece of the send draws (its own colours) has the same picture drawn right over it as a silhouette in
    the sender's colour at half its alpha - by the piece's own Draw (kbr_ov_*) or, for a piece drawn the default way (the
    game's obj_regularbullet / obj_collidebullet / obj_afterimage, a boss's pieces with no Draw), by the drawer just above
    its depth (obj_knight_saov); never over the piece's own flash (fog);
  - the boss's phantom beside the box (Gerson, Pink, Spamton NEO) the same;
  - Flowery's sends (on his board, in a Flowery match) the same;
  - the knights' sends keep their own light mix (image_blend), no silhouette;
  - a boss's own pieces in his own fight (Jevil, Spamton NEO, Pink, Gerson) never get it, and draw exactly as before;
  - no error.
Usage: python3 t_tint103.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import Recorder

FAILS = []
N = [0]
CX, CY = br_harness.CAM
TR, TG, TB = 17, 233, 101
TCOL = TR | (TG << 8) | (TB << 16)


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


OBJSPR = {}
for l in open('/home/claude/work/src/built102/assets.tsv'):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'obj' and r[3]:
        OBJSPR[r[1]] = r[3]


def give_sprites(sim):
    got = {}
    for o, od in sim.objects.items():
        if o in OBJSPR and getattr(od, 'sprite', None) in (None, -1):
            try:
                od.sprite = sim.asset_index(OBJSPR[o])
                got[o] = od.sprite
            except Exception:
                pass
    for i in sim.instances.values():
        if not i.dead and i.obj in got and i.vars.get('sprite_index', -1) in (-1, None):
            i.vars['sprite_index'] = got[i.obj]


def setup(row, seed, setx=''):
    sim, e = br_match(open_ok=row, kn=(row,), seed=seed, bots=2, setx='_s.mhp = 999; _s.skills = 1; _s.skfam = 3; _s.hard = 0; _s.ramp = 0; _s.maxst = 0; _s.sd = 0; _s.rush = 0;' + setx)
    if e:
        return None, None
    give_sprites(sim)
    sim.load_source('gml_GlobalScript_tintforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.TATK; }\nfunction kbr_pcol(_s) { return global.TCOL; }\n')
    sim.run('global.TATK = 0; global.TCOL = %d; global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];' % TCOL)
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    rec = Recorder(sim)
    sim.mock('camera_get_view_x', lambda s, *a: CX)
    sim.mock('camera_get_view_y', lambda s, *a: CY)

    def dself(s, f):
        v = f.self.vars
        sp = v.get('sprite_index', -1)
        if isinstance(sp, (int, float)) and sp >= 0:
            rec.ops.append(('spr', rec.name_of(sp), v.get('image_index', 0), v.get('x', 0), v.get('y', 0), v.get('image_xscale', 1), v.get('image_yscale', 1),
                            v.get('image_angle', 0), rec.fogc(v.get('image_blend', 16777215)), v.get('image_alpha', 1), None, None))
        return 0
    sim.mock('draw_self', dself, frame=True)
    for f in range(900):
        if step(sim, 1):
            break
        if sim.eval('global.kfo.M.R.ph') == 'run':
            break
    return sim, rec


def draw_all(sim, rec):
    """one frame drawn the game's way; the sprite ops per instance (id, object, kbrx) in order"""
    rec.ops.clear()
    insts = sorted([i for i in sim.instances.values() if not i.dead], key=lambda i: -i.vars.get('depth', 0))
    out = []
    errs = []
    for num in (72, 0, 73):
        for inst in insts:
            if inst.dead or inst.id not in sim.instances or not inst.vars.get('visible', True):
                continue
            n0 = len(rec.ops)
            found = sim.find_event(inst.obj, ('Draw', num))
            if found is not None:
                try:
                    sim._run_entry(inst, found[0], ('Draw', num), found[1], None)
                except Exception as ex:
                    errs.append('draw %s %d: %s' % (inst.obj, num, str(ex)[:200]))
            elif num == 0:
                spr = inst.vars.get('sprite_index', -1)
                if isinstance(spr, (int, float)) and spr >= 0:
                    sim.run('with (%d) draw_sprite_ext(sprite_index, image_index, x, y, image_xscale, image_yscale, image_angle, image_blend, image_alpha);' % inst.id)
            for o in rec.ops[n0:]:
                if o[0] == 'spr':
                    out.append((inst.id, inst.obj, inst.vars.get('kbrx', 0), o))
    return out, errs


def is_tfog(o):
    return isinstance(o[8], tuple) and o[8][0] == 'fog' and o[8][1] == TCOL


def coverage(ops, gx):
    """the send's own pictures (not under fog, visible) and whether each has the sender's silhouette over it"""
    mine = [(i, ob, o) for i, ob, k, o in ops if k == gx and not isinstance(o[8], tuple) and (o[9] or 0) > 0.02]
    over = [o for i, ob, k, o in ops if is_tfog(o) and (k == gx or ob == 'obj_knight_saov')]
    keys = {}
    for o in over:
        keys[(o[1], round(o[3], 1), round(o[4], 1))] = keys.get((o[1], round(o[3], 1), round(o[4], 1)), 0) + 1
    miss = []
    for i, ob, o in mine:
        k = (o[1], round(o[3], 1), round(o[4], 1))
        if keys.get(k, 0) > 0:
            keys[k] -= 1
        else:
            miss.append((ob, o[1]))
    alphas = sorted(set(round(o[9] / max(0.001, 1), 2) for o in over))
    return len(mine), miss, over


SHOTS = (12, 30, 55, 90)
CLEAR = 'with (obj_bulletparent) { if (!variable_instance_exists(id, "kbrx") || kbrx <= 0) { visible = false; x = -99999; } }'


def run_send(sim, rec, sid, frames=100, flowery=False):
    n0 = J(sim, 'global.kbr_sa_n')
    sim.run('kbr_skill_land({ sid: %d, sd: %d, from: 101, mul: 1, tg: global.kfo.my });' % (sid, 5000 + sid))
    gx = J(sim, 'global.kbr_sa_n')
    if gx == n0:
        return None
    res = {'pics': 0, 'miss': [], 'over': 0, 'err': None, 'objs': set(), 'ph': 0, 'alpha_bad': []}
    for t in range(1, frames + 1):
        if not flowery:
            sim.run(CLEAR)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            res['err'] = err
            break
        if t % 10 == 0:
            give_sprites(sim)
        if t in SHOTS:
            give_sprites(sim)
            ops, errs = draw_all(sim, rec)
            if errs:
                res['err'] = errs[0]
                break
            n, miss, over = coverage(ops, gx)
            res['pics'] += n
            res['miss'] += miss
            res['over'] += len(over)
            res['objs'] |= set(ob for i, ob, k, o in ops if k == gx)
            # the phantom (the hub controller's Draw): its silhouette in the sender's colour
            res['ph'] += sum(1 for i, ob, k, o in ops if ob == 'obj_knight_ctrl' and is_tfog(o))
            # half the picture's alpha (never more than half)
            res['alpha_bad'] += [round(o[9], 2) for o in over if o[9] > 0.5 + 1e-6]
    return res


t0 = time.time()
# ---------------- the bosses' sends in a knight match (Jevil, Gerson, Spamton NEO, Pink)
sim, rec = setup(0, 6400)
ok(sim is not None, 'the practice match against the Normal Knight starts')
PH = {}
for sid in list(range(26, 38)) + list(range(45, 57)):
    if J(sim, 'global.kfo.M.R.ph') != 'run':
        for f in range(900):
            step(sim, 1)
            if J(sim, 'global.kfo.M.R.ph') == 'run':
                break
    for f in range(6):
        sim.run(CLEAR)
        step(sim, 1)
    if J(sim, 'global.kfo.M.out'):
        sim, rec = setup(0, 6400 + sid)
    name = J(sim, 'kbr_skill_name(%d)' % sid)
    r = run_send(sim, rec, sid)
    if r is None:
        ok(False, '%d %s: the send starts' % (sid, name))
        continue
    ok(r['err'] is None, '%d %s: no error %s' % (sid, name, (r['err'] or '')[:160]))
    ok(r['pics'] > 0 and not r['miss'], '%d %s: every picture of it (%d drawn) in your colour - the silhouette over each (%d); none without %r' % (sid, name, r['pics'], r['over'], sorted(set(r['miss']))[:4]))
    ok(not r['alpha_bad'], '%d %s: the colour at half the picture\'s alpha at most %r' % (sid, name, r['alpha_bad'][:3]))
    PH[sid] = r['ph']
ok(all(PH.get(s, 0) > 0 for s in (32, 49, 55)), 'the bosses\' phantoms beside the box in your colour (Gerson 32: %d, Spamton 49: %d, Pink 55: %d)' % (PH.get(32, 0), PH.get(49, 0), PH.get(55, 0)))

# ---------------- a dark SOUL colour (black): lifted as a name in it is, so the send stays easy to see
for f in range(6):
    sim.run(CLEAR)
    step(sim, 1)
sim.run('global.TCOL = c_black;')
n0 = J(sim, 'global.kbr_sa_n')
sim.run('kbr_skill_land({ sid: 27, sd: 5999, from: 101, mul: 1, tg: global.kfo.my });')
gx = J(sim, 'global.kbr_sa_n')
for t in range(12):
    sim.run(CLEAR)
    step(sim, 1)
dk = J(sim, '(function(){ var _o = []; with (all) if (variable_instance_exists(id, "kbrx") && kbrx == %d && variable_instance_exists(id, "kbrovc")) array_push(_o, kbrovc); return _o; })()' % gx)
lift = J(sim, 'kfo_col_text(c_black)')
ok(dk and all(c == lift for c in dk) and J(sim, 'kfo_col_lum(%d)' % lift) >= 90, 'a black SOUL\'s send: its colour lifted to %06X (bright %d) so it stays easy to see' % (lift, J(sim, 'kfo_col_lum(%d)' % lift)))
sim.run('global.TCOL = %d;' % TCOL)

# ---------------- the knights' sends: their own light mix, no silhouette
kn_over = 0
kn_tint = 0
for sid in (1, 3, 5, 17, 19):
    for f in range(6):
        sim.run(CLEAR)
        step(sim, 1)
    n0 = J(sim, 'global.kbr_sa_n')
    sim.run('kbr_skill_land({ sid: %d, sd: %d, from: 101, mul: 1, tg: global.kfo.my });' % (sid, 5100 + sid))
    gx = J(sim, 'global.kbr_sa_n')
    for t in range(1, 50):
        sim.run(CLEAR)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        step(sim, 1)
        if t in (15, 35):
            ops, errs = draw_all(sim, rec)
            kn_over += sum(1 for i, ob, k, o in ops if k == gx and is_tfog(o))
            kn_tint += J(sim, '(function(){ var _n = 0; with (all) if (variable_instance_exists(id, "kbrx") && kbrx == %d && variable_instance_exists(id, "kbrtb") && kbrtb != -1) _n++; return _n; })()' % gx)
ok(kn_over == 0 and kn_tint > 0, 'the knights\' sends keep their own light mix (%d tinted pieces) and get no silhouette (%d)' % (kn_tint, kn_over))

# ---------------- Flowery's sends, on his board
fs, frec = setup(8, 6500, '_s.skfam = 7;')
ok(fs is not None, 'a practice match against Flowery starts')
if fs is not None:
    for sid in range(38, 45):
        # into one of his attacks (the board runs then)
        for f in range(900):
            if J(fs, 'global.kfo.M.R.ph') == 'run' and J(fs, 'kbr_fl_sa_ready()'):
                break
            step(fs, 1)
        name = J(fs, 'kbr_skill_name(%d)' % sid)
        r = run_send(fs, frec, sid, 100, flowery=True)
        if r is None:
            ok(False, '%d %s: the send starts' % (sid, name))
            continue
        ok(r['err'] is None, '%d %s: no error %s' % (sid, name, (r['err'] or '')[:160]))
        ok(r['pics'] > 0 and not r['miss'], '%d %s: every picture of it (%d drawn) in your colour (%d); none without %r' % (sid, name, r['pics'], r['over'], sorted(set(r['miss']))[:4]))

# ---------------- a boss's own pieces in his own fight: never coloured, drawn as before
for row, boss, atks in ((6, 'Jevil', (0, 3, 6)), (9, 'Spamton NEO', (0, 5)), (10, 'Pink', (0, 4)), (7, 'Gerson', (0, 2))):
    bs, brec = setup(row, 6600 + row, '_s.skills = 0;')
    if bs is None:
        ok(False, '%s: the practice match starts' % boss)
        continue
    own = 0
    over = 0
    err = None
    for a in atks:
        bs.run('global.TATK = %d;' % a)
        for f in range(220):
            bs.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            err = step(bs, 1)
            if err:
                break
            if f % 40 == 39:
                give_sprites(bs)
                ops, errs = draw_all(bs, brec)
                own += sum(1 for i, ob, k, o in ops if not k and ob.startswith(('obj_jv_', 'obj_sn_', 'obj_pk_', 'obj_hj_')))
                over += sum(1 for i, ob, k, o in ops if is_tfog(o))
                err = err or (errs[0] if errs else None)
        if err:
            break
    ok(err is None and own > 0 and over == 0, '%s\'s own pieces in his own fight: %d pictures, none coloured (%d) %s' % (boss, own, over, (err or '')[:120]))

print('\n%d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
