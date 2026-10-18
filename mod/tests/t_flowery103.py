"""DRBR 1.0.3 - your report: "Flowery's background is bugged out". His tower (obj_fl_towery, Chapter 5's spinning flower tower behind
his battle) is drawn at the middle of the screen - Chapter 5 put it at x 320, the middle of ITS battle room's view; the arena
here is far into the cold place (the battle's camera starts at x 2063), so the tower was drawn about 1750 pixels left of the
screen and the background was empty. A practice match against Flowery at the real arena camera, several of his attacks, the
tower's Draw run with its surfaces recorded:
  - the tower's front and back (and their outlines) are drawn on the screen, centred on its middle (the camera's x + 320);
  - it follows the camera (moved 40 pixels: drawn 40 pixels further);
  - no error.
Usage: python3 t_flowery103.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *

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


sim, e = br_match(open_ok=8, kn=(8,), seed=7401, bots=1, setx='_s.mhp = 999; _s.skills = 0;')
ok(e is None, 'a practice match against Flowery starts (%r)' % (e,))
sim.mock('camera_get_view_x', lambda s, *a: CAM_X[0])
sim.mock('camera_get_view_y', lambda s, *a: CY)
CAM_X = [CX]
sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
DRAWN = []
sim.mock('draw_surface_ext', lambda s, i, x, y, xs, ys, *r: (DRAWN.append((float(x), float(xs))), 0)[1])
sim.mock('draw_surface_part_ext', lambda s, i, l, t, w, h, x, y, xs, ys, *r: 0)
err = None
tw = 0
for f in range(1500):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    err = step(sim, 1)
    if err:
        break
    if J(sim, 'instance_exists(obj_fl_towery)'):
        tw += 1
        if tw >= 200:
            break
ok(err is None, 'his attacks run (%s)' % (err or 'no error')[:200])
ok(tw > 0, 'his tower is up (%d frames)' % tw)
if tw:
    fixed = J(sim, 'obj_fl_towery.fixed_position')
    DRAWN.clear()
    sim.run('with (obj_fl_towery) event_perform(ev_draw, 0);')
    xs = [x for x, s in DRAWN]
    print('  fixed_position %r, the tower\'s surfaces drawn at x %r (camera %d)' % (fixed, [round(x - CX) for x in xs], CX))
    ok(len(xs) >= 4 and all(CX - 60 <= x <= CX + 700 for x in xs), 'the tower is drawn on the screen (x %r relative to the camera)' % [round(x - CX) for x in xs])
    mid = (min(xs) + max(xs)) / 2
    ok(abs(mid - (CX + 320)) < 40, 'centred on the screen\'s middle (%d; the middle %d)' % (round(mid - CX), 320))
    # the camera moves 40 pixels: the tower with it
    CAM_X[0] = CX + 40
    DRAWN.clear()
    sim.run('with (obj_fl_towery) event_perform(ev_draw, 0);')
    xs2 = [x for x, s in DRAWN]
    ok(len(xs2) == len(xs) and all(abs((b - a) - 40) < 0.01 for a, b in zip(xs, xs2)), 'it follows the camera (moved %r)' % sorted(set(round(b - a, 2) for a, b in zip(xs, xs2))))
    CAM_X[0] = CX

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
