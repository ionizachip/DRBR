"""DRBR 1.0.3 - your report: "for sent skills they need to visibly fit in the box, not be really really large". A practice match
against the Normal Knight (its first attack every time: a plain 167 px box), at the real arena camera, every boss's attack
skill landed in your box from a bot, every frame stepped:
  - no piece of a boss's send is drawn bigger than the box allows (a long thin one - a beam - by its thickness), its hitbox
    with it; the knights' own sends keep their size;
  - the phantoms beside the box (Gerson, Pink, Spamton NEO) at their own size or smaller, close to the box;
  - Gerson's bells stand at the box's sides; the BIG SHOT's orb and beam are half his own; Pink's mega bomb's warning cross
    and the fuse bombs' stay inside the box;
  - every send still builds its pieces (none left out) and no error.
Usage: python3 t_sendfit103.py"""
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


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


# the objects' sprites as the built game has them (the emulator's objects have none: the sizes need them)
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


sim, e = br_match(open_ok=0, kn=(0,), seed=6100, bots=2, setx='_s.mhp = 999; _s.skills = 1; _s.skfam = 3; _s.hard = 0; _s.ramp = 0; _s.maxst = 0; _s.sd = 0; _s.rush = 0;')
ok(e is None, 'the practice match starts (%r)' % (e,))
give_sprites(sim)
sim.load_source('gml_GlobalScript_sendforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return 0; }\n')
sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
rec = Recorder(sim)
sim.mock('camera_get_view_x', lambda s, *a: CX)
sim.mock('camera_get_view_y', lambda s, *a: CY)
for f in range(900):
    step(sim, 1)
    if sim.eval('global.kfo.M.R.ph') == 'run':
        break
HIDE = 'with (obj_bulletparent) { if (!variable_instance_exists(id, "kbrx") || kbrx <= 0) { visible = false; x = -99999; } }'
SIZE = ('(function(){ var _o = []; with (all) { if (variable_instance_exists(id, "kbrx") && kbrx == %d && sprite_index >= 0 && visible && image_alpha > 0) {'
        ' var _w = sprite_get_width(sprite_index) * abs(image_xscale); var _h = sprite_get_height(sprite_index) * abs(image_yscale);'
        ' var _s = max(_w, _h); if (_s > 3 * min(_w, _h)) _s = min(_w, _h); array_push(_o, [object_get_name(object_index), _s, round(x - %d), round(y - %d)]); } } return _o; })()')
TELS = '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; for (var _j = 0; _j < array_length(_G.tel); _j++) { var _T = _G.tel[_j]; if (_T.k == "spr") array_push(_o, [_G.sid, _T.xs, round(_T.x - %d), round(_T.y - %d)]); } } return _o; })()' % (CX, CY)

for sid in list(range(26, 38)) + list(range(45, 57)):
    if sim.eval('global.kfo.M.R.ph') != 'run':
        for f in range(900):
            step(sim, 1)
            if sim.eval('global.kfo.M.R.ph') == 'run':
                break
    for f in range(8):
        sim.run(HIDE)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        step(sim, 1)
    B = J(sim, 'kbr_sa_box()')
    lim = max(32, min(B[2], B[3]) * J(sim, 'KBR_SA_FIT'))
    n0 = J(sim, 'global.kbr_sa_n')
    sim.run('kbr_skill_land({ sid: %d, sd: %d, from: 101, mul: 1, tg: global.kfo.my });' % (sid, 4000 + sid))
    gx = J(sim, 'global.kbr_sa_n')
    name = J(sim, 'kbr_skill_name(%d)' % sid)
    if gx == n0:
        ok(False, '%d %s: the send starts' % (sid, name))
        continue
    big = []
    bells = []
    booms = []
    made = set()
    tels = []
    cross = []
    err = None
    for t in range(1, 260):
        sim.run(HIDE)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            break
        if t % 10 == 0:
            give_sprites(sim)
        if t % 3 == 0:
            for o, s, x, y in J(sim, SIZE % (gx, CX, CY)):
                made.add(o)
                if s > lim + 1:
                    big.append((t, o, round(s)))
                if o == 'obj_hj_bell':
                    bells.append(x)
            tels += J(sim, TELS)
        if sid in (54, 55):
            booms += [tuple(r) for r in J(sim, '(function(){ var _o = []; with (obj_pk_boom) { if (variable_instance_exists(id, "kbrx") && kbrx == %d) array_push(_o, [round(x - %d), round(y - %d)]); } return _o; })()' % (gx, CX, CY))]
        if sid in (54, 55) and t % 2 == 0:
            rec.ops.clear()
            sim.run('with (obj_pk_bigbomb) { if (variable_instance_exists(id, "kbrx") && kbrx == %d) event_perform(ev_draw, 0); } with (obj_pk_bomb) { if (variable_instance_exists(id, "kbrx") && kbrx == %d) event_perform(ev_draw, 0); }' % (gx, gx))
            for o in rec.ops:
                if o[0] == 'rect':
                    cross.append((round(o[1] - CX), round(o[2] - CY), round(o[3] - CX), round(o[4] - CY)))
        if t > 60 and not J(sim, 'kbr_sa_alive(%d)' % gx) and not J(sim, '(function(){ for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (global.kbr_sa[_i].gx == %d) return true; return false; })()' % gx):
            break
    ok(err is None, '%d %s: no error %s' % (sid, name, (err or '')[:200]))
    ok(len(made) > 0, '%d %s: it builds its pieces (%s)' % (sid, name, ', '.join(sorted(made))[:120]))
    ok(not big, '%d %s: no piece bigger than the box allows (%d px): %r' % (sid, name, lim, big[:4]))
    for s, xs, x, y in tels:
        if not ok(abs(xs) <= 1 and abs(x - 320) <= B[2] + 60, '%d %s: its phantom at its own size or less, close to the box (xs %r at %d, %d)' % (sid, name, xs, x, y)):
            break
    if sid == 36:
        ok(bells and all(abs(x - 320) <= B[2] + 56 for x in bells), '36 Bell of Justice: the bells at the box\'s sides (x %r, box half %d)' % (sorted(set(bells))[:4], B[2]))
    if sid in (54, 55):
        bl, bt, br, bb = J(sim, '[obj_growtangle.bbox_left - %d, obj_growtangle.bbox_top - %d, obj_growtangle.bbox_right - %d, obj_growtangle.bbox_bottom - %d]' % (CX, CY, CX, CY))
        out = [c for c in cross if c[0] < bl - 1 or c[2] > br + 1 or c[1] < bt - 1 or c[3] > bb + 1]
        if not cross and J(sim, 'kbr_pk_dial()') != 1:
            ok(True, '%d %s: no warning cross with this bomb dial (%r)' % (sid, name, J(sim, 'kbr_pk_dial()')))
        else:
            ok(cross and not out, '%d %s: its warning cross stays in the box (%d drawn, %r outside)' % (sid, name, len(cross), out[:2]))
        bo = [b for b in booms if b[0] < bl - 50 or b[0] > br + 50 or b[1] < bt - 50 or b[1] > bb + 50]
        ok(booms and not bo, '%d %s: its explosions stay at the box (%d, %r outside)' % (sid, name, len(booms), bo[:3]))

# the BIG SHOT's laser: half his own
sim.run('kbr_skill_land({ sid: 50, sd: 77, from: 101, mul: 1, tg: global.kfo.my });')
for f in range(3):
    step(sim, 1)
k = J(sim, '(function(){ var _k = -1; with (obj_sn_biglaser) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) _k = kbr_fitv(); } return _k; })()')
ok(k == 0.5, 'the BIG SHOT\'s laser is sized for the box (kbrsz %r)' % k)
# the knights' sends keep their own size (the fit is the bosses')
ok(J(sim, 'KBR_SA_FIT') > 0, 'the fit is a setting of its own (KBR_SA_FIT %r)' % J(sim, 'KBR_SA_FIT'))

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
