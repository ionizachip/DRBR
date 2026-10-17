"""Build 47: the screen shake never moves the online bullets, and REDUCED SHAKE.

The game shakes the screen by moving the camera (obj_shake: the view's x / y jump a few pixels back and forth and back to
where they were). Bullets placed from the camera (camerax() + 320, __view_get(XView) ...) would land in different places in
two games whose screens shook differently - online every game must make the same bullets. Build 47: while an online match
runs (global.kbr_det.on), camerax / cameray / __view_get(XView / YView) of view 0 give the camera's own place (the shake's
mycamerax / mycameray while a shake is on); the picture still shakes. Offline nothing changes.

Here the camera is a model (camera_get_view_x / camera_set_view_pos keep a real position: the emulator's are fixed at 0).
Parts:
  unit     offline: camerax() follows the shake as in the game; online: camerax() / __view_get stay on the camera's place
           while the real camera shakes, and after the shake the camera is back; REDUCED SHAKE: the game's no-shake flag on
           for the match (the camera does not move at all), the player's own value back after it
  match    the same online match three times: no shakes / shakes every 40 frames / shakes with the fix taken out (build 46):
           the bullets (30 / 60 / 90 frames into each attack) the same in the first two, and the third shows the problem
Usage: python3 t_cam47.py [part ...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

FAILS = []
N = [0]
STATS = {}


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def camera_model(sim, x=0.0, y=0.0):
    sim.cam = [float(x), float(y)]
    sim.cam_moves = 0

    def gx(s, c=0):
        return s.cam[0]

    def gy(s, c=0):
        return s.cam[1]

    def setp(s, c, x, y):
        if (float(x), float(y)) != (s.cam[0], s.cam[1]):
            s.cam_moves += 1
        s.cam[0] = float(x)
        s.cam[1] = float(y)
        return 0
    sim.mock('camera_get_view_x', gx)
    sim.mock('camera_get_view_y', gy)
    sim.mock('camera_set_view_pos', setp)
    sim.mock('view_get_camera', lambda s, i=0: 0)
    for ev in ('Create_0', 'Step_0', 'Alarm_0', 'Destroy_0'):
        p = BDIR + 'gml_Object_obj_shake_%s.gml' % ev
        sim.load_file(p, entry='gml_Object_obj_shake_%s' % ev)
    if 'obj_shake' not in sim.objects:
        sim.define_object('obj_shake')


def part_unit():
    sim, e = br_match(open_ok=0, kn=(0,), skin=1, seed=11)
    ok(e is None, 'unit: battle made (%r)' % (e,))
    camera_model(sim, 100, 50)
    # offline (the online match off): the game's own behaviour
    sim.run('global.kbr_det.on = false; global.flag[12] = 0; instance_create(0, 0, obj_shake);')
    seen = []
    for f in range(12):
        step(sim, 1)
        seen.append((sim.cam[0], J(sim, 'camerax()')))
    ok(any(c != 100 for c, _ in seen) and all(c == x for c, x in seen), 'unit: offline the camera shakes and camerax() follows it (as in the game): %s' % seen[:4])
    for f in range(20):
        step(sim, 1)
    ok(sim.cam == [100.0, 50.0], 'unit: offline the shake ends with the camera back (%s)' % sim.cam)
    # online
    sim.run('global.kbr_det.on = true; global.flag[12] = 0; instance_create(0, 0, obj_shake);')
    seen = []
    for f in range(12):
        step(sim, 1)
        seen.append((sim.cam[0], J(sim, 'camerax()'), J(sim, '__view_get(e__VW.XView, 0)'), J(sim, 'cameray()')))
    moved = any(c != 100 for c, _, _, _ in seen)
    ok(moved and all(x == 100 and v == 100 and y == 50 for c, x, v, y in seen), 'unit: online the picture shakes (camera %s) but camerax / __view_get / cameray stay on the camera\'s place: %s'
       % (sorted(set(c for c, _, _, _ in seen)), seen[:4]))
    for f in range(20):
        step(sim, 1)
    ok(sim.cam == [100.0, 50.0] and J(sim, 'camerax()') == 100, 'unit: online the shake ends with the camera back (%s)' % sim.cam)
    # the camera itself moving (not a shake): camerax() follows it online too
    sim.cam = [140.0, 50.0]
    ok(J(sim, 'camerax()') == 140, 'unit: online, with no shake, camerax() is the camera (%s)' % J(sim, 'camerax()'))
    sim.cam = [100.0, 50.0]
    # REDUCED SHAKE
    sim.run('global.flag[12] = 0; global.kfo.view.shake = 1; kbr_view_shake(global.kfo.M);')
    ok(J(sim, 'global.flag[12]') == 1, 'unit: REDUCED SHAKE on - the game\'s no-shake flag on for the match')
    sim.cam_moves = 0
    sim.run('instance_create(0, 0, obj_shake);')
    for f in range(30):
        step(sim, 1)
    ok(sim.cam_moves == 0, 'unit: REDUCED SHAKE - a shake does not move the camera at all (%d moves)' % sim.cam_moves)
    sim.run('kbr_view_shake_back(global.kfo.M);')
    ok(J(sim, 'global.flag[12]') == 0, 'unit: after the match the player\'s own value is back (0)')
    sim.run('global.flag[12] = 1; global.kfo.view.shake = 1; kbr_view_shake(global.kfo.M); kbr_view_shake_back(global.kfo.M);')
    ok(J(sim, 'global.flag[12]') == 1, 'unit: a player who had shakes off in the game keeps them off (1)')
    sim.run('global.kfo.view.shake = 0; global.flag[12] = 0; kbr_view_shake(global.kfo.M);')
    ok(J(sim, 'global.flag[12]') == 0, 'unit: REDUCED SHAKE off - the flag untouched')


SNAP = ('var _L = []; with (obj_bulletparent) array_push(_L, object_get_name(object_index) + "@" + string(round(x * 100) / 100) + "," + string(round(y * 100) / 100));'
        'global.CSN = _L;')


def run_match(shakes, fix, frames=1500, seed=4747):
    sim, e = br_match(open_ok=0, kn=(0, 2, 3, 4), skin=1, seed=seed, setx='_s.rush = 1; _s.mhp = 300;')
    if e is not None:
        return None, e
    camera_model(sim, 0, 0)
    if not fix:
        sim.define_script('cam46', 'function kbr_cam_fix_on() { return false; }')
    snaps = {}
    errs = 0
    for f in range(frames):
        if f % 30 == 0:
            sim.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        if shakes and f % 40 == 5:
            sim.run('instance_create(0, 0, obj_shake);')
        err = step(sim, 1)
        if err is not None:
            errs += 1
            return None, err
        st = J(sim, '[global.kfo.M.R.ph, global.kfo.M.R.k, global.kfo.M.R.af]')
        if st[0] == 'run' and st[2] in (30, 60, 90):
            sim.run(SNAP)
            snaps['%d:%d' % (st[1], st[2])] = J(sim, 'global.CSN')
    return snaps, None


def part_match():
    t0 = time.time()
    a, ea = run_match(False, True)
    b, eb = run_match(True, True)
    c, ec = run_match(True, False)
    ok(ea is None and eb is None and ec is None, 'match: three runs without error (%r %r %r)' % (ea, eb, ec))
    if a is None or b is None or c is None:
        return
    common = [k for k in a if k in b]
    same = sum(1 for k in common if a[k] == b[k])
    ok(common and same == len(common), 'match: online with shakes every 40 frames, the bullets are the same as with none: %d / %d snapshots' % (same, len(common)))
    common2 = [k for k in a if k in c]
    diff = sum(1 for k in common2 if a[k] != c[k])
    ok(diff > 0, 'match: with the fix taken out (build 46) the shakes do move bullets: %d / %d snapshots differ (the test sees the problem)' % (diff, len(common2)))
    nb = sum(len(v) for v in b.values())
    STATS['match'] = {'snapshots': len(common), 'same': same, 'bullets_compared': nb, 'build46_differs': diff, 'wall': round(time.time() - t0)}


PARTS = {'unit': part_unit, 'match': part_match}

if __name__ == '__main__':
    t0 = time.time()
    for k in (sys.argv[1:] or list(PARTS)):
        print('== part', k, flush=True)
        try:
            PARTS[k]()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    print('STATS', json.dumps(STATS))
    print('t_cam47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:30]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
