"""DRBR: the runner's instance-geometry queries for the emulator (its own answer a fixed "no", and distance_to_point a fixed
1000000). The ported bosses steer by them (Gerson's box throw walks the SOUL into the box's turned mask with position_meeting;
his shells are blocked only within distance_to_point 36 of the SOUL), so the boss tests answer them from each instance's real
collision mask (bbox_model: the sprite's / mask's rectangle from data.win, scaled and turned with the instance - the precise
masks of the game lie inside it):
  position_meeting / instance_position / collision_point     a point in a mask
  place_meeting / instance_place / place_free / place_empty  self's mask moved to (x, y) against others' (not self)
  collision_rectangle / collision_line / collision_circle    a shape against masks
  distance_to_point / distance_to_object                     between bounding boxes, 0 when they meet
  instance_nearest / instance_furthest                       by the instances' positions (their origins)
`obj` is an object (its children too), an instance id, or all. Solid-only queries (place_free) look at solid instances."""
import math
import bbox_model as BM

ALL = -3
NOONE = -4


def _insts(sim, obj):
    try:
        o = int(obj)
    except Exception:
        o = None
    if o == ALL:
        return [i for i in sim.instances.values() if not i.dead]
    if o is not None and o >= 100000:
        i = sim.instances.get(o)
        return [i] if i is not None and not i.dead else []
    try:
        return [i for i in sim.instances_of(o if o is not None else obj) if not i.dead]
    except Exception:
        return []


def _pt_in(q, x, y):
    # convex quad, either winding: the point on the same side of every edge
    s = 0
    for i in range(4):
        ax, ay = q[i]
        bx, by = q[(i + 1) % 4]
        c = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if c > 1e-9:
            if s < 0:
                return False
            s = 1
        elif c < -1e-9:
            if s > 0:
                return False
            s = -1
    return True


def _proj(q, ax, ay):
    p = [x * ax + y * ay for x, y in q]
    return min(p), max(p)


def obb_hits_obb(q1, q2):
    for q in (q1, q2):
        for i in range(2):
            ax = q[i + 1][0] - q[i][0]
            ay = q[i + 1][1] - q[i][1]
            if ax == 0 and ay == 0:
                continue
            a1, b1 = _proj(q1, -ay, ax)
            a2, b2 = _proj(q2, -ay, ax)
            if b1 < a2 or b2 < a1:
                return False
    return True


def _seg_hits(q, x1, y1, x2, y2):
    if _pt_in(q, x1, y1) or _pt_in(q, x2, y2):
        return True
    for i in range(4):
        ax, ay = q[i]
        bx, by = q[(i + 1) % 4]
        d = (x2 - x1) * (by - ay) - (y2 - y1) * (bx - ax)
        if d == 0:
            continue
        t = ((ax - x1) * (by - ay) - (ay - y1) * (bx - ax)) / d
        u = ((ax - x1) * (y2 - y1) - (ay - y1) * (x2 - x1)) / d
        if 0 <= t <= 1 and 0 <= u <= 1:
            return True
    return False


def _circ_hits(q, cx, cy, r):
    if _pt_in(q, cx, cy):
        return True
    for i in range(4):
        ax, ay = q[i]
        bx, by = q[(i + 1) % 4]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((cx - ax) * dx + (cy - ay) * dy) / L))
        px, py = ax + t * dx, ay + t * dy
        if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
            return True
    return False


def _moved(sim, inst, x, y):
    q = BM.obb_of(sim, inst)
    if q is None:
        return None
    try:
        dx = float(x) - float(inst.vars.get('x', 0))
        dy = float(y) - float(inst.vars.get('y', 0))
    except Exception:
        return None
    return [(p[0] + dx, p[1] + dy) for p in q]


def _first(sim, obj, test, notme=None):
    for i in _insts(sim, obj):
        if notme is not None and i is notme:
            continue
        q = BM.obb_of(sim, i)
        if q is not None and test(q):
            return i
    return None


def _box(sim, inst):
    b = BM.box_of(sim, inst)
    if b is None:
        try:
            x, y = float(inst.vars.get('x', 0)), float(inst.vars.get('y', 0))
        except Exception:
            return None
        return (x, y, x, y)
    return b


def install(sim):
    if getattr(sim, '_geom_on', False):
        return
    sim._geom_on = True

    def position_meeting(s, f, x, y, obj):
        return _first(s, obj, lambda q: _pt_in(q, float(x), float(y))) is not None

    def instance_position(s, f, x, y, obj):
        i = _first(s, obj, lambda q: _pt_in(q, float(x), float(y)))
        return i.id if i is not None else NOONE

    def collision_point(s, f, x, y, obj, prec=False, notme=False):
        i = _first(s, obj, lambda q: _pt_in(q, float(x), float(y)), f.self if notme else None)
        return i.id if i is not None else NOONE

    def _place(s, f, x, y, obj, solid=False):
        me = f.self
        if me is None or not hasattr(me, 'vars'):
            return None
        mq = _moved(s, me, x, y)
        if mq is None:
            return None
        for i in _insts(s, obj):
            if i is me:
                continue
            if solid and not i.vars.get('solid', False):
                continue
            q = BM.obb_of(s, i)
            if q is not None and obb_hits_obb(mq, q):
                return i
        return None

    def place_meeting(s, f, x, y, obj):
        return _place(s, f, x, y, obj) is not None

    def instance_place(s, f, x, y, obj):
        i = _place(s, f, x, y, obj)
        return i.id if i is not None else NOONE

    def place_free(s, f, x, y):
        return _place(s, f, x, y, ALL, solid=True) is None

    def place_empty(s, f, x, y, obj=ALL):
        return _place(s, f, x, y, obj) is None

    def collision_rectangle(s, f, x1, y1, x2, y2, obj, prec=False, notme=False):
        a1, a2 = min(float(x1), float(x2)), max(float(x1), float(x2))
        b1, b2 = min(float(y1), float(y2)), max(float(y1), float(y2))
        i = _first(s, obj, lambda q: BM.obb_hits_rect(q, a1, b1, a2, b2), f.self if notme else None)
        return i.id if i is not None else NOONE

    def collision_line(s, f, x1, y1, x2, y2, obj, prec=False, notme=False):
        i = _first(s, obj, lambda q: _seg_hits(q, float(x1), float(y1), float(x2), float(y2)), f.self if notme else None)
        return i.id if i is not None else NOONE

    def collision_circle(s, f, x, y, r, obj, prec=False, notme=False):
        i = _first(s, obj, lambda q: _circ_hits(q, float(x), float(y), float(r)), f.self if notme else None)
        return i.id if i is not None else NOONE

    def distance_to_point(s, f, x, y):
        me = f.self
        b = _box(s, me) if me is not None and hasattr(me, 'vars') else None
        if b is None:
            return 0
        x, y = float(x), float(y)
        dx = max(b[0] - x, 0, x - b[2])
        dy = max(b[1] - y, 0, y - b[3])
        return math.hypot(dx, dy)

    def distance_to_object(s, f, obj):
        me = f.self
        b = _box(s, me) if me is not None and hasattr(me, 'vars') else None
        if b is None:
            return 1000000
        best = 1000000
        for i in _insts(s, obj):
            if i is me:
                continue
            c = _box(s, i)
            if c is None:
                continue
            dx = max(c[0] - b[2], 0, b[0] - c[2])
            dy = max(c[1] - b[3], 0, b[1] - c[3])
            best = min(best, math.hypot(dx, dy))
        return best

    def _near(s, f, x, y, obj, far=False):
        best, bd = None, None
        for i in _insts(s, obj):
            try:
                d = math.hypot(float(i.vars.get('x', 0)) - float(x), float(i.vars.get('y', 0)) - float(y))
            except Exception:
                continue
            if bd is None or (d > bd if far else d < bd):
                best, bd = i, d
        return best.id if best is not None else NOONE

    def instance_nearest(s, f, x, y, obj):
        return _near(s, f, x, y, obj)

    def instance_furthest(s, f, x, y, obj):
        return _near(s, f, x, y, obj, True)

    for n, fn in (('instance_nearest', instance_nearest), ('instance_furthest', instance_furthest), ('position_meeting', position_meeting), ('instance_position', instance_position), ('collision_point', collision_point),
                  ('place_meeting', place_meeting), ('instance_place', instance_place), ('place_free', place_free),
                  ('place_empty', place_empty), ('collision_rectangle', collision_rectangle), ('collision_line', collision_line),
                  ('collision_circle', collision_circle), ('distance_to_point', distance_to_point), ('distance_to_object', distance_to_object)):
        sim.mock(n, fn, frame=True)
