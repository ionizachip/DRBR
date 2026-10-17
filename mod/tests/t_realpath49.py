"""Build 49: the REAL PATH - the other SOULs and the bots with the battle where it really is.

In the real game the hub's fight is Chapter 3's own Knight encounter in room_dw_snow_zone: the arena cutscene (obj_ch3_PTB02)
pans the camera to the arena, far into the room (the camera's x about 1970-2720), and the battle - its box, every SOUL, every
bullet - is made from that camera (camerax() + ...). Every earlier test ran the battle with the emulator's camera at 0, so the
box and the SOULs were at x 0-640.

Build 48 failed there in two places, both invisible at camera 0:
  1. the host kept every player's SOUL position inside -200..1000 ("p" message): a real SOUL at x 2300 came back as 1000, so
     the others' SOULs were drawn at x 1000 - outside the screen (the camera shows 2063-2703).
  2. the bots: kfo_bot_box() took a box at x >= 2000 for "no box", so a bot was never placed, never moved and never sent a
     position: nothing to draw (and it never took a hit - it only lost HP to the "no battle" fallback).
Build 49: positions travel relative to the battle's camera (each game draws them at that + its own camera); no room-x limits.

This test puts each emulated game's camera where the real arena's is (a camera model: camera_get_view_x / y give it; each game a
different one, as two players never stop at exactly the same spot) BEFORE the battle is made, then:
  A  two games: every checkpoint (both SOULs still), each game draws the other's SOUL where that SOUL is on ITS screen:
     drawn x = other's heart x - other's camera + my camera (+ the heart's 2 px), and inside my screen
  B  practice with 3 bots (camera 2063 / 2400 / 2720,40): the bots are placed in the box, move, and are drawn (the same
     kbr_draw_souls as the online players) inside the box, never outside the screen
  C  the DEBUG OVERLAY lines (F3): the stamp, the room, every other SOUL with room / relative x, y and DRAWN
Usage: python3 t_realpath49.py [A B C] [--old]   (--old: run against build 48's code (KH_MERGED=.../rt/b48/) and require the
failure to show: no agreement, bots never placed)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OLD = '--old' in sys.argv
import br_harness
import br_multi
from br_multi import *

FAILS = []
N = [0]
STATS = {}
IN = 2


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def camera_model(sim, x=0.0, y=0.0):
    sim.cam = [float(x), float(y)]
    sim.mock('camera_get_view_x', lambda s, c=0: s.cam[0])
    sim.mock('camera_get_view_y', lambda s, c=0: s.cam[1])
    sim.mock('camera_get_view_width', lambda s, c=0: 640)
    sim.mock('camera_get_view_height', lambda s, c=0: 480)

    def setp(s, c, x, y):
        s.cam[0] = float(x)
        s.cam[1] = float(y)
        return 0
    sim.mock('camera_set_view_pos', setp)
    sim.mock('view_get_camera', lambda s, i=0: 0)


CAMS = {}
_orig_lu = br_harness.lu_battle


def lu_cam(host, pre=None, **kw):
    """the battle made with the camera where the real arena's is (set before anything of the battle exists)"""
    def pre2(s):
        if pre is not None:
            pre(s)
        cid = getattr(s, 'cid', 1)
        camera_model(s, *CAMS.get(cid, CAMS.get(1, (0, 0))))
    return _orig_lu(host, pre=pre2, **kw)


br_harness.lu_battle = lu_cam
br_multi.lu_battle = lu_cam

LOGGER_SRC = None


def instrument(sims):
    import t_view47
    for s in sims:
        s.load_source('gml_GlobalScript_view47_log', t_view47.LOGGER)
        s.run('global.SDL = []; global.SDT = "";')
        s.load_file(MDIR + 'gml_Object_obj_heart_Draw_0.gml', entry='gml_Object_obj_heart_Draw_0')
        if 'spr_dodgeheart' not in s.assets:
            s.define_asset('spr_dodgeheart')
        s.objects['obj_heart'].sprite = s.assets['spr_dodgeheart']
        s.run('with (obj_heart) sprite_index = spr_dodgeheart;')


def draws(s, who='r'):
    return [d for d in J(s, 'global.SDL') if d[0] == who]


def heart(s):
    return tuple(J(s, 'instance_exists(obj_heart) ? [obj_heart.x, obj_heart.y] : [-1, -1]'))


def box(s):
    return J(s, 'instance_exists(obj_growtangle) ? [obj_growtangle.x, obj_growtangle.y] : [-1, -1]')


MOVES = [('right',), ('up',), ('left',), ('down',), ('right', 'down'), ('left', 'up'), ()]


def part_a():
    t0 = time.time()
    CAMS.clear()
    CAMS.update({1: (2063.0, 0.0), 2: (2400.0, 40.0)})
    net, sims = make_room(2, 'normal', 4242, setx='_s.rush = 1; _s.mhp = 300; _s.spec = 1;')
    instrument(sims)
    hist = {0: [], 1: []}
    good = tot = 0
    onscreen = offscreen = 0
    samples = []
    boxes = set()
    for f in range(1300):
        net.t += 1000.0 / 30.0
        if f % 30 == 0:
            for s in sims:
                s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
                s.log.clear()
        still = (f % 120) >= 95
        for i, s in enumerate(sims):
            s.run('test_net_pump(); global.SDL = [];')
            s.kb = set() if still else set(MOVES[((f // 17) + i * 3) % len(MOVES)])
            e = step(s, 1)
            if e is not None:
                ok(False, 'A: game %d frame %d: %s' % (i + 1, f, e[:300]))
                return
        for i, s in enumerate(sims):
            hist[i].append(heart(s))
            hist[i] = hist[i][-12:]
            b = box(s)
            if b[0] >= 0:
                boxes.add((i, round(b[0] - s.cam[0]), round(b[1] - s.cam[1])))
            for d in draws(s, 'r'):
                if s.cam[0] <= d[1] <= s.cam[0] + 640 and s.cam[1] <= d[2] <= s.cam[1] + 480:
                    onscreen += 1
                else:
                    offscreen += 1
        if f % 120 == 119:
            for i, s in enumerate(sims):
                o = sims[1 - i]
                h = hist[1 - i]
                if len(h) < 10 or h[-1] == (-1, -1) or any(p != h[-1] for p in h[-10:]):
                    continue
                tot += 1
                want = (h[-1][0] - o.cam[0] + s.cam[0] + IN, h[-1][1] - o.cam[1] + s.cam[1] + IN)
                dr = draws(s, 'r')
                hit = any(abs(d[1] - want[0]) < 0.051 and abs(d[2] - want[1]) < 0.051 for d in dr)
                good += hit
                if len(samples) < 6:
                    samples.append({'game': i + 1, 'other_heart': h[-1], 'want': [round(want[0], 2), round(want[1], 2)], 'drawn': [[round(d[1], 2), round(d[2], 2)] for d in dr][:3]})
    STATS['A'] = {'checkpoints': tot, 'agree': good, 'drawn_on_screen': onscreen, 'drawn_off_screen': offscreen, 'samples': samples,
                  'box_rel_to_camera': sorted(boxes)[:6], 'wall': round(time.time() - t0)}
    print('A', json.dumps(STATS['A']), flush=True)
    ok(len(boxes) > 0 and all(260 <= bx <= 380 for _, bx, _ in boxes), 'A: the battle box is made from the camera (box x - camera x: %s)' % sorted({b[1] for b in boxes}))
    if OLD:
        ok(tot >= 6 and good == 0, 'A (build 48): the other SOUL is never drawn where it is (%d / %d) - the bug reproduced' % (good, tot))
        ok(offscreen > 0 and onscreen == 0, 'A (build 48): every draw of the other SOUL is outside the screen (%d off, %d on)' % (offscreen, onscreen))
    else:
        ok(tot >= 6 and good == tot, 'A: each game draws the other SOUL where it is on its own screen: %d / %d checkpoints' % (good, tot))
        ok(onscreen > 100 and offscreen == 0, 'A: every draw of the other SOUL is on the screen (%d on, %d off)' % (onscreen, offscreen))


def part_b():
    for cam in ((2063.0, 0.0), (2400.0, 0.0), (2720.0, 40.0)):
        t0 = time.time()
        CAMS.clear()
        CAMS[1] = cam
        sim, e = br_match(open_ok=0, kn=(0,), seed=4950, bots=3, setx='_s.mhp = 300; _s.botp = 2;')
        ok(e is None, 'B cam %s: practice with 3 bots starts (%s)' % (cam, e))
        if e is not None:
            return
        instrument([sim])
        pos = {}
        drawn_in = drawn_out = 0
        frames_run = 0
        nd_max = 0
        bhist = []
        for f in range(900):
            sim.run('global.SDL = []; if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            sim.kb = set(MOVES[(f // 20) % len(MOVES)])
            err = step(sim, 1)
            if err:
                ok(False, 'B: error %s' % err[:300])
                return
            if f % 30 == 0:
                sim.log.clear()
            ph = J(sim, 'global.kfo.M.R.ph')
            if ph != 'run':
                continue
            frames_run += 1
            bx = J(sim, 'kfo_bot_box()')
            sim.run('global.BL = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot && is_struct(_b.bt)) array_push(global.BL, [_b.pid, _b.bt.placed, _b.bt.x, _b.bt.y, _b.al, _b.hp]); }')
            for b in J(sim, 'global.BL'):
                pos.setdefault(b[0], []).append((b[1], round(b[2], 1), round(b[3], 1)))
            dr = draws(sim, 'r')
            nd_max = max(nd_max, len(dr))
            bhist.append(bx)
            bhist[:] = bhist[-6:]
            # (a box that changed in the last 5 frames - the next attack's, or one closing - is skipped: the bots and the SOULs
            # follow it within a few frames, as the players' own SOULs are pushed in by its walls)
            if bx is not None and len(bhist) == 6 and all(b == bx for b in bhist):
                for d in dr:
                    cx, cy = d[1] + 8, d[2] + 8
                    if bx[0] - 12 <= cx <= bx[2] + 12 and bx[1] - 12 <= cy <= bx[3] + 12:
                        drawn_in += 1
                    else:
                        drawn_out += 1
                        if drawn_out <= 5:
                            print('   outside: frame %d af %d box %s drawn %s bots %s' % (f, J(sim, 'global.kfo.M.R.af'), bx, [round(d[1], 1), round(d[2], 1)], J(sim, 'global.BL')), flush=True)
        placed = {k: any(p[0] for p in v) for k, v in pos.items()}
        moved = {k: len({(p[1], p[2]) for p in v if p[0]}) for k, v in pos.items()}
        STATS['B %s' % (cam,)] = {'run_frames': frames_run, 'placed': placed, 'distinct_positions': moved, 'drawn_in_box': drawn_in, 'drawn_outside': drawn_out,
                                 'most_drawn_at_once': nd_max, 'stamp': J(sim, 'knight_build_stamp()') if not OLD else '', 'wall': round(time.time() - t0)}
        print('B', cam, json.dumps(STATS['B %s' % (cam,)]), flush=True)
        if OLD:
            ok(frames_run > 100 and not any(placed.values()), 'B cam %s (build 48): the bots are never placed (%s) - the bug reproduced' % (cam, placed))
            ok(drawn_in == 0, 'B cam %s (build 48): no bot is drawn in the box (%d)' % (cam, drawn_in))
        else:
            ok(frames_run > 100 and len(placed) == 3 and all(placed.values()), 'B cam %s: all 3 bots placed in the box %s' % (cam, placed))
            ok(all(v >= 20 for v in moved.values()), 'B cam %s: every bot moves (distinct positions %s)' % (cam, moved))
            ok(drawn_in > 200 and drawn_out == 0 and nd_max == 3, 'B cam %s: the bots are drawn by kbr_draw_souls inside the box (%d in, %d out, up to %d at once)' % (cam, drawn_in, drawn_out, nd_max))


def part_c():
    CAMS.clear()
    CAMS[1] = (2063.0, 0.0)
    sim, e = br_match(open_ok=0, kn=(0,), seed=4950, bots=2, setx='_s.mhp = 300;')
    ok(e is None, 'C: practice with 2 bots (%s)' % (e,))
    for f in range(400):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        step(sim, 1)
        if f % 30 == 0:
            sim.log.clear()
        if J(sim, 'global.kfo.M.R.ph') == 'run' and J(sim, 'instance_exists(obj_heart)') and f > 200:
            break
    # (the battle harness loads no room: room_get_name answers the arena's room)
    sim.mock('room_get_name', lambda s_, r: 'room_dw_snow_zone')
    sim.run('kh_dbg().on = true; global.DL = kh_dbg_lines();')
    lines = J(sim, 'global.DL')
    print('\n'.join('   | ' + l for l in lines))
    ok(lines[0].startswith('KNIGHT HUB V2 - BUILD 51 - '), 'C: the stamp: %s' % lines[0])
    ok(any(l.startswith('ROOM ') and 'CAMERA 2063' in l for l in lines), 'C: the room and camera line')
    ok(any(l.startswith('OTHER SOULS: 2 (bots 2)') for l in lines), 'C: two other SOULs, both bots')
    bl = [l for l in lines if l.startswith(' P') and '[BOT]' in l]
    ok(len(bl) == 2 and all('room 2' in l and 'DRAWN' in l and 'depth -99000' in l for l in bl), 'C: each bot: room x 2xxx, depth, DRAWN (%s)' % bl)
    ok(any(l.startswith('BOT BOX: 2') for l in lines), 'C: the bots box at the arena x')


if __name__ == '__main__':
    parts = [a for a in sys.argv[1:] if not a.startswith('--')] or (['A', 'B'] if OLD else ['A', 'B', 'C'])
    t0 = time.time()
    for p in parts:
        {'A': part_a, 'B': part_b, 'C': part_c}[p]()
    print('STATS', json.dumps(STATS))
    print('PASS' if not FAILS else 'FAIL', N[0] - len(FAILS), '/', N[0], round(time.time() - t0), 's')
    sys.exit(1 if FAILS else 0)
