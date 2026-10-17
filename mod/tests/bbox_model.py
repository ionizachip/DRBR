"""Build 49: a stand-in for GameMaker's motion and collision boxes in the emulator (for the bots' dodging tests).

The emulator keeps no sprite masks and does not move instances by their speed. Here:
  - every bullet (obj_collidebullet and its children) and the SOUL get bbox_left / top / right / bottom from their sprite's (or
    mask's) real collision box in the built data.win (rt/b48_objinfo.tsv: size, origin, margins), scaled and - for a turned
    sprite - the box around the turned rectangle;
  - instances with a speed move by it after each frame (x += speed * cos(direction), y -= speed * sin(direction)), as the
    runner does between Step and End Step;
  - collision_rectangle / collision_rectangle_list answer by the mask's rectangle turned with the instance (the real game's
    precise masks lie inside it, so the real game is never harder than this); build 50: for the stars and starchildren
    (their sprites exported to uiref/bul) a precise test uses their real pixels;
  - the battle box's sprite_width / height: its real sprite (75 x 75) times its scale.
Usage: install(sim) once; sync(sim) before the bots look (wrapped into kfo_host_bots_tick); move(sim) after each frame."""
import math, os

# (DRBR: the newest build's table - Jevil's and the new bosses' sprites are in it; KH_OBJINFO picks another)
INFO = os.environ.get('KH_OBJINFO') or next((p for p in ('/home/claude/work/rt/b53_objinfo.tsv', '/home/claude/work/rt/b51_objinfo.tsv') if os.path.exists(p)), '/home/claude/work/rt/b48_objinfo.tsv')
SPR = {}
OBJ = {}
for l in open(INFO):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'spr':
        SPR[r[1]] = tuple(int(v) for v in r[2:10])   # w, h, ox, oy, ml, mr, mt, mb
    elif r[0] == 'obj':
        OBJ[r[1]] = (r[2], r[3], r[4])               # parent, sprite, mask


def _sprite_name(sim, inst):
    names = getattr(sim, '_asset_names', None)
    if names is None or len(names) != len(sim.assets):
        sim._asset_names = names = {v: k for k, v in sim.assets.items()}
    # an object's own mask (set in data.win) comes first, as in the runner (obj_heart: spr_dodgeheartmask)
    mk = inst.vars.get('mask_index', -1)
    try:
        mk = int(mk)
    except Exception:
        mk = -1
    if mk < 0:
        o = inst.obj
        for _ in range(8):
            if o not in OBJ:
                break
            if OBJ[o][2] in SPR:
                return OBJ[o][2]
            o = OBJ[o][0]
    for key in ('mask_index', 'sprite_index'):
        v = inst.vars.get(key, -1)
        try:
            v = int(v)
        except Exception:
            continue
        if v >= 0 and names.get(v) in SPR:
            return names[v]
    # the object's own (or a parent's) mask / sprite in data.win
    o = inst.obj
    for _ in range(8):
        if o not in OBJ:
            break
        p, s, m = OBJ[o]
        if m in SPR:
            return m
        if s in SPR:
            return s
        o = p
    return None


def obb_of(sim, inst):
    """the mask's rectangle turned with the instance: its four corners in the room"""
    s = _sprite_name(sim, inst)
    if s is None:
        return None
    w, h, ox, oy, ml, mr, mt, mb = SPR[s]
    v = inst.vars
    try:
        x, y = float(v.get('x', 0)), float(v.get('y', 0))
        xs, ys = float(v.get('image_xscale', 1)), float(v.get('image_yscale', 1))
        ang = float(v.get('image_angle', 0))
    except Exception:
        return None
    pts = [((ml - ox) * xs, (mt - oy) * ys), ((mr + 1 - ox) * xs, (mt - oy) * ys), ((mr + 1 - ox) * xs, (mb + 1 - oy) * ys), ((ml - ox) * xs, (mb + 1 - oy) * ys)]
    if ang % 360:
        c, sn = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
        pts = [(px * c - py * sn, px * sn + py * c) for px, py in pts]
    return [(x + p[0], y + p[1]) for p in pts]


def obb_hits_rect(q, x1, y1, x2, y2):
    """separating axes: the rectangle's two and the turned one's two"""
    xs = [p[0] for p in q]
    ys = [p[1] for p in q]
    if max(xs) < x1 or min(xs) > x2 or max(ys) < y1 or min(ys) > y2:
        return False
    r = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    for i in range(2):
        ax = q[i + 1][0] - q[i][0]
        ay = q[i + 1][1] - q[i][1]
        if ax == 0 and ay == 0:
            continue
        pq = [p[0] * ax + p[1] * ay for p in q]
        pr = [p[0] * ax + p[1] * ay for p in r]
        if max(pq) < min(pr) or max(pr) < min(pq):
            return False
    return True


def box_of(sim, inst):
    s = _sprite_name(sim, inst)
    if s is None:
        return None
    w, h, ox, oy, ml, mr, mt, mb = SPR[s]
    v = inst.vars
    try:
        x, y = float(v.get('x', 0)), float(v.get('y', 0))
        xs, ys = float(v.get('image_xscale', 1)), float(v.get('image_yscale', 1))
        ang = float(v.get('image_angle', 0))
    except Exception:
        return None
    # the mask's corners relative to the origin, scaled, turned
    pts = [((ml - ox) * xs, (mt - oy) * ys), ((mr + 1 - ox) * xs, (mt - oy) * ys), ((ml - ox) * xs, (mb + 1 - oy) * ys), ((mr + 1 - ox) * xs, (mb + 1 - oy) * ys)]
    if ang % 360:
        c, sn = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
        pts = [(px * c - py * sn, px * sn + py * c) for px, py in pts]
    xs_ = [x + p[0] for p in pts]
    ys_ = [y + p[1] for p in pts]
    return (min(xs_), min(ys_), max(xs_) - 1, max(ys_) - 1)


def sync(sim, *a):
    # the battle box: its sprite's real size (spr_battlebg_0, 75 x 75) times its scale (the emulator's sprite_width is 64)
    for inst in (sim.instances_of('obj_growtangle') if 'obj_growtangle' in sim.objects else []):
        try:
            inst.vars['sprite_width'] = 75 * float(inst.vars.get('image_xscale', 1))
            inst.vars['sprite_height'] = 75 * float(inst.vars.get('image_yscale', 1))
        except Exception:
            pass
    for obj in ('obj_collidebullet', 'obj_heart'):
        if obj not in sim.objects:
            continue
        for inst in sim.instances_of(obj):
            if inst.dead:
                continue
            b = box_of(sim, inst)
            if b is None:
                inst.vars['bbox_left'], inst.vars['bbox_top'], inst.vars['bbox_right'], inst.vars['bbox_bottom'] = 0, 0, -1, -1
            else:
                inst.vars['bbox_left'], inst.vars['bbox_top'], inst.vars['bbox_right'], inst.vars['bbox_bottom'] = b
    return 0


def move(sim):
    for inst in list(sim.instances.values()):
        if inst.dead:
            continue
        v = inst.vars
        try:
            sp = float(v.get('speed', 0) or 0)
        except Exception:
            continue
        if sp == 0:
            continue
        try:
            d = math.radians(float(v.get('direction', 0) or 0))
            v['x'] = float(v.get('x', 0)) + sp * math.cos(d)
            v['y'] = float(v.get('y', 0)) - sp * math.sin(d)
        except Exception:
            pass


def move_full(sim):
    """DRBR: the runner's motion, whole - speed / direction and hspeed / vspeed are one motion (writing either pair sets the
    other in the game; the emulator keeps four plain variables, so the pair written since the last frame wins), then friction
    (towards 0 - negative friction speeds up), gravity (gravity_direction), then x += hspeed, y += vspeed. The bosses' ported
    code moves by all of these (Chapter 4's Gerson: hspeed / vspeed, gravity, negative friction)."""
    tab = sim.__dict__.setdefault('_mvtab', {})
    for inst in list(sim.instances.values()):
        if inst.dead:
            tab.pop(inst.id, None)
            continue
        v = inst.vars
        try:
            sp = float(v.get('speed', 0) or 0)
            dr = float(v.get('direction', 0) or 0)
            hs = float(v.get('hspeed', 0) or 0)
            vs = float(v.get('vspeed', 0) or 0)
            fr = float(v.get('friction', 0) or 0)
            gr = float(v.get('gravity', 0) or 0)
        except Exception:
            continue
        last = tab.get(inst.id)
        if last is None:
            last = (0.0, 0.0, 0.0, 0.0)
        sdc = (sp != last[0], dr != last[1])
        hvc = hs != last[2] or vs != last[3]
        if hvc and not any(sdc):
            if hs != 0 or vs != 0:
                sp = math.hypot(hs, vs)
                dr = math.degrees(math.atan2(-vs, hs)) % 360.0
            else:
                sp = 0.0
        elif any(sdc):
            if hvc:
                # both pairs written this frame (hspeed = 3; direction = 90): the length from whichever named it last we
                # cannot know - the speed when it was written, else the new hspeed / vspeed's
                if not sdc[0]:
                    sp = math.hypot(hs, vs)
                if not sdc[1] and (hs != 0 or vs != 0):
                    dr = math.degrees(math.atan2(-vs, hs)) % 360.0
            hs = sp * math.cos(math.radians(dr))
            vs = -sp * math.sin(math.radians(dr))
        if sp == 0 and fr == 0 and gr == 0 and hs == 0 and vs == 0:
            tab[inst.id] = (sp, dr, hs, vs)
            continue
        if fr != 0 and sp != 0:
            ns = sp - fr if sp > 0 else sp + fr
            if (sp > 0 and ns < 0) or (sp < 0 and ns > 0):
                ns = 0.0
            sp = ns
            hs = sp * math.cos(math.radians(dr))
            vs = -sp * math.sin(math.radians(dr))
        if gr != 0:
            gd = math.radians(float(v.get('gravity_direction', 270) or 0))
            hs += gr * math.cos(gd)
            vs -= gr * math.sin(gd)
            sp = math.hypot(hs, vs)
            if hs != 0 or vs != 0:
                dr = math.degrees(math.atan2(-vs, hs)) % 360.0
        try:
            v['x'] = float(v.get('x', 0)) + hs
            v['y'] = float(v.get('y', 0)) + vs
        except Exception:
            pass
        v['speed'], v['direction'], v['hspeed'], v['vspeed'] = sp, dr, hs, vs
        tab[inst.id] = (sp, dr, hs, vs)


# build 50: the stars' and starchildren's precise masks (their real pixels, every frame together), from the sprites
# exported to uiref/bul - a precise test against them is answered by those pixels, not by the mask's rectangle
PMASK_DIR = '/home/claude/work/uiref/bul/'
_PM = {}


def pmask(name):
    if name in _PM:
        return _PM[name]
    m = None
    try:
        from PIL import Image
        fr = sorted(f for f in os.listdir(PMASK_DIR) if f.startswith(name + '_') and f[len(name) + 1:-4].isdigit() and f.endswith('.png'))
        if fr and name in SPR:
            w, h = SPR[name][0], SPR[name][1]
            m = [[False] * w for _ in range(h)]
            for f in fr:
                im = Image.open(PMASK_DIR + f).convert('RGBA')
                if im.size != (w, h):
                    m = None
                    break
                px = im.load()
                for yy in range(h):
                    for xx in range(w):
                        if px[xx, yy][3] > 0:
                            m[yy][xx] = True
    except Exception:
        m = None
    _PM[name] = m
    return m


def precise_hits_rect(sim, inst, x1, y1, x2, y2):
    """the instance's real pixels against the rectangle (sampled every pixel, at least the corners and the middle)"""
    s = _sprite_name(sim, inst)
    m = pmask(s) if s else None
    if m is None:
        return True
    w, h, ox, oy = SPR[s][0], SPR[s][1], SPR[s][2], SPR[s][3]
    v = inst.vars
    try:
        x, y = float(v.get('x', 0)), float(v.get('y', 0))
        xs, ys = float(v.get('image_xscale', 1)), float(v.get('image_yscale', 1))
        ang = math.radians(float(v.get('image_angle', 0)))
    except Exception:
        return True
    if xs == 0 or ys == 0:
        return False
    c, sn = math.cos(ang), math.sin(ang)
    nx = max(1, int(math.ceil(x2 - x1)))
    ny = max(1, int(math.ceil(y2 - y1)))
    for i in range(nx + 1):
        for j in range(ny + 1):
            px = x1 + (x2 - x1) * i / nx
            py = y1 + (y2 - y1) * j / ny
            dx, dy = px - x, py - y
            lx = dx * c - dy * sn
            ly = dx * sn + dy * c
            u = int(math.floor(lx / xs + ox))
            q = int(math.floor(ly / ys + oy))
            if 0 <= u < w and 0 <= q < h and m[q][u]:
                return True
    return False


def _hits(sim, x1, y1, x2, y2, obj, prec=False):
    x1, x2 = min(float(x1), float(x2)), max(float(x1), float(x2))
    y1, y2 = min(float(y1), float(y2)), max(float(y1), float(y2))
    out = []
    try:
        insts = [sim.instances[int(obj)]] if int(obj) >= 100000 and int(obj) in sim.instances else sim.instances_of(obj)
    except Exception:
        insts = sim.instances_of(obj)
    for inst in insts:
        if inst.dead or 'growtangle' in inst.obj:
            continue
        q = obb_of(sim, inst)
        if q is None:
            continue
        if obb_hits_rect(q, x1, y1, x2, y2):
            if prec and not precise_hits_rect(sim, inst, x1, y1, x2, y2):
                continue
            out.append(inst)
    return out


def install(sim):
    def crl(s, x1, y1, x2, y2, obj, prec, notme, lst, ordered=False):
        h = _hits(s, x1, y1, x2, y2, obj, bool(prec))
        L = s.ds_list(lst)
        for i in h:
            L.append(i.id)
        return len(h)

    def cr(s, x1, y1, x2, y2, obj, prec=False, notme=False):
        h = _hits(s, x1, y1, x2, y2, obj, bool(prec))
        return h[0].id if h else -4
    sim.mock('collision_rectangle_list', crl)
    sim.mock('collision_rectangle', cr)

    def cp(s, x, y, obj, prec=False, notme=False):
        h = _hits(s, x, y, x, y, obj, bool(prec))
        return h[0].id if h else -4
    sim.mock('collision_point', cp)
    sim.mock('test_bbox_sync', sync)

    # the sprites' sizes and origins as in data.win (the emulator's are fixed numbers)
    def spr_field(k, d):
        def f(s, spr, *a):
            names = getattr(s, '_asset_names', None)
            if names is None or len(names) != len(s.assets):
                s._asset_names = names = {v: kk for kk, v in s.assets.items()}
            try:
                n = names.get(int(spr))
            except Exception:
                n = None
            return SPR[n][k] if n in SPR else d
        return f
    sim.mock('sprite_get_width', spr_field(0, 1))
    sim.mock('sprite_get_height', spr_field(1, 1))
    sim.mock('sprite_get_xoffset', spr_field(2, 0))
    sim.mock('sprite_get_yoffset', spr_field(3, 0))
