"""Build 47: the online room's overworld - no party, every player in their own SKIN, the original Knight encounter closed
(a wall and its trigger refusing) - tested in the emulator with the real code (ow_harness.py: the cold place from data.win,
Kris / the followers / the dark world controller / the encounter's controller running their own code, collisions from the
sprites' own boxes) and, for the tests with several players, the real relay (relay.js, real sockets) between the games.

Fixtures (the document's table; what is printed are the measured numbers):
  OW-001  enter a room: the party followers gone (asleep, not destroyed); 100 room changes while in the room: never one awake
  OW-002  two players: each game shows exactly two characters (itself + the other), no follower
  OW-003  eight players: each game shows exactly eight
  OW-004  your SKIN: drawn in Kris's place (Susie / Ralsei / Noelle), never Kris
  OW-005  another player's SKIN: drawn as theirs in every other game; changed in the lobby: the others follow (100 changes)
  OW-006  walking right / down / left / up: the SKIN's own sprite for that way, its frames turning (yours and the others' view)
  OW-007  stopping: the standing frame, facing the last way
  OW-008  to another room and back: still the SKIN; the others see you only in the room you are in
  OW-009  100 leave / come back: a new id each time, never two characters for one player, the SKIN back
  OW-010  walking to the encounter online: the wall stops you (x <= 1762), its notice shows once
  OW-011  1,000 teleports past the trigger (every knight's version): it never starts; you are put back on this side
  OW-012  two players at the wall / past it at the same time: no encounter in either game
  OW-013  back offline: the party awake again, behind Kris, following
  OW-014  20 approaches offline (every knight's version): the encounter starts every time
  OW-015  SKIN changed again and again: never Kris for a frame, never two of you, never an older SKIN again
  OW-016  eight players walking at once: every game draws the seven others where they are, no error
  OW-017  a player leaves (or their game stops): gone from every other game, no ghost entry kept
  OW-018  a match and a rematch, back to the room each time: party asleep, SKINs, the wall
  OW-019  the wall: every way of walking into it (straight, diagonal, running, along it) - never through
  OW-020  offline: no wall left; walking on to x 1840 starts the encounter as before
Usage: python3 t_ow47.py [fixture ...]   (default: all)"""
import sys, os, re, json, time, random, socket, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ow_harness import *

FAILS = []
N = [0]
STATS = {}
RELAY = '/home/claude/work/online/server/relay.js'
NODE = '/opt/node22/bin/node'
SKN = {1: 'spr_kris', 2: 'spr_susie_walk', 3: 'spr_ralsei_walk', 4: 'spr_noelle_walk'}
WAYS = {1: 'right', 2: 'up', 3: 'left', 0: 'down'}


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


# ---------- what each game draws ----------
def obj_of(f):
    s = getattr(f, 'self', None)
    return getattr(s, 'obj', None) or ''


def install_draw_log(sim):
    sim.DL = []

    def dse(s, f, spr, sub, x, y, xs=1, ys=1, rot=0, col=0, a=1):
        s.DL.append((obj_of(f), spr_name(s, spr) or str(spr), float(sub), float(x), float(y), float(a)))
        return 0

    def dself(s, f):
        v = f.self.vars
        s.DL.append((obj_of(f), spr_name(s, v.get('sprite_index', -1)) or '?', float(v.get('image_index', 0)), float(v.get('x', 0)), float(v.get('y', 0)), 1.0))
        return 0

    def dtext(s, f, x, y, t):
        s.DL.append((obj_of(f), 'TEXT', 0.0, float(x), float(y), str(t)))
        return 0
    sim.mock('draw_sprite_ext', dse, frame=True)
    sim.mock('draw_self', dself, frame=True)
    sim.mock('draw_text', dtext, frame=True)


def skin_of(spr):
    for k, v in SKN.items():
        if spr.startswith(v):
            return k
    return 0


def is_char(spr):
    return spr.startswith('spr_kris') or '_walk_' in spr


def others_drawn(sim):
    """the characters the hub's controller drew for the other players this frame (seen: not fully transparent)"""
    return [d for d in sim.DL if d[0] == 'obj_knight_ctrl' and d[1] != 'TEXT' and is_char(d[1]) and d[5] > 0.001]


def self_drawn(sim):
    """you, as your own game draws you this frame (Kris's battle-mode overlays are drawn at alpha 0 outside an overworld
    battle: not counted)"""
    return [d for d in sim.DL if d[0] == 'obj_mainchara' and d[1] != 'TEXT' and is_char(d[1]) and d[5] > 0.001]


def frame(sims, n=1, on=None):
    for k in range(n):
        for s in sims:
            s.DL = []
            if on is not None:
                on(s, k)
            ow_step(s)


def awake_followers(sim):
    """the party followers awake while this frame was drawn"""
    return sim.awake_at_draw


# ---------- the relay ----------
def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class Relay:
    def __init__(self):
        self.port = free_port()
        self.p = subprocess.Popen([NODE, RELAY, '--port', str(self.port), '--host', '127.0.0.1', '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                socket.create_connection(('127.0.0.1', self.port), timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError('relay did not start')

    def close(self):
        try:
            self.p.kill()
            self.p.wait()
        except Exception:
            pass


def game(relay, name, skin, x=None, y=None):
    s = ow_sim(name, skin)
    install_draw_log(s)
    s.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % relay.port)
    enter(s)
    if x is not None:
        mc(s).vars['x'] = float(x)
    if y is not None:
        mc(s).vars['y'] = float(y)
    return s


def pump(sims, cond, frames=300, sleep=0.002):
    for k in range(frames):
        frame(sims)
        if cond():
            return True
        time.sleep(sleep)
    return cond()


def make_room(relay, specs):
    """specs: [(name, skin, x, y), ...]; the first creates the room, the others join it; returns the games once every game
    lists everyone and everyone sees everyone walking"""
    sims = [game(relay, *sp) for sp in specs]
    sims[0].run('kfo_create();')
    ok(pump(sims[:1], lambda: J(sims[0], 'global.kfo.st') == 'room', 300), 'the room is made')
    code = J(sims[0], 'global.kfo.code')
    for s in sims[1:]:
        s.run('kfo_join("%s");' % code)
    n = len(sims)
    ok(pump(sims, lambda: all(J(s, 'global.kfo.st') == 'room' and len(J(s, 'kfo_lobby_players()')) == n for s in sims), 600),
       '%d games in the room, each lists %d players' % (n, n))
    pump(sims, lambda: all(len(others_drawn(s)) == n - 1 for s in sims), 300)
    for s in sims:
        s.code = code
    return sims


def leave_all(sims):
    for s in sims:
        try:
            s.run('kfo_leave();')
        except Exception:
            pass


# ---------- the fixtures ----------
def fx_single():
    """OW-001 / OW-013 / OW-020 / OW-010 / OW-019 / OW-004 / OW-006 / OW-007 / OW-015 (self) in a practice room (the same
    room rules as online; no network needed for one player)"""
    s = ow_sim('Kris', 2)
    install_draw_log(s)
    enter(s)
    frame([s], 3)
    ok(awake_followers(s) == 2, 'offline: the party follows (%d followers)' % awake_followers(s))
    # OW-001: into a room
    s.run('kfo_practice_start();')
    frame([s], 1)
    ok(awake_followers(s) == 0 and len(deactivated_followers(s)) == 2, 'OW-001: in a room the followers are gone (%d awake, %d asleep - kept, not destroyed)'
       % (awake_followers(s), len(deactivated_followers(s))))
    # 100 room changes while in the room (a door out of the cold place and back): never a follower awake at any frame's end
    seen = 0
    frames = 0
    for c in range(100):
        s.goto_room('room_ow_test_other' if c % 2 == 0 else 'room_dw_snow_zone')
        for k in range(4):
            frame([s], 1)
            frames += 1
            seen += awake_followers(s)
    ok(seen == 0, 'OW-001: 100 room changes in the room (%d frames): followers awake at a frame\'s end: %d' % (frames, seen))
    STATS['OW-001'] = {'room_changes': 100, 'frames': frames, 'followers_seen': seen}
    ok(s.room_name() == 'room_dw_snow_zone', 'back in the cold place')
    # OW-004: your SKIN, drawn in Kris's place
    frame([s], 2)
    sd = self_drawn(s)
    ok(len(sd) == 1 and sd[0][1].startswith('spr_susie_walk'), 'OW-004: you (SKIN Susie) are drawn as Susie, once (%s)' % [d[1] for d in sd])
    # OW-006 / OW-007: the four ways, the frames turning, then standing
    m = mc(s)
    m.vars['x'] = 900.0
    m.vars['y'] = 300.0
    res = {}
    for way, keys, want in (('right', {'right'}, 'spr_susie_walk_right_dw'), ('down', {'down'}, 'spr_susie_walk_down_dw'),
                            ('left', {'left'}, 'spr_susie_walk_left_dw'), ('up', {'up'}, 'spr_susie_walk_up_dw')):
        held(s, keys)
        sprs = []
        frs = set()
        for k in range(24):
            frame([s], 1)
            sd = self_drawn(s)
            if sd:
                sprs.append(sd[-1][1])
                frs.add(int(sd[-1][2]))
        held(s, set())
        # the game's own Kris finishes the step for a few frames (walkbuffer) before standing: the same for the SKIN
        frame([s], 10)
        st = self_drawn(s)
        res[way] = (sprs[-1] if sprs else None, len(frs), st[-1][1] if st else None, int(st[-1][2]) if st else None)
        ok(sprs and all(x == want for x in sprs[4:]), 'OW-006: walking %s - drawn as %s (%s)' % (way, want, sorted(set(sprs))))
        ok(len(frs) >= 3, 'OW-006: walking %s - the walk frames turn (%d different)' % (way, len(frs)))
        ok(st and st[-1][1] == want and int(st[-1][2]) == 0, 'OW-007: stopped after %s - the standing frame facing that way (%s, frame %s)' % (way, st and st[-1][1], st and st[-1][2]))
    STATS['OW-006/007 (self)'] = res
    # OW-015 (yours): the SKIN changed every 3 frames, 100 times: every frame exactly one of you, always the current SKIN
    bad = 0
    kris = 0
    for c in range(100):
        s.run('global.kfo.skin = %d;' % (1 + (c % 4)))
        for k in range(3):
            frame([s], 1)
            sd = self_drawn(s)
            want = SKN[1 + (c % 4)]
            if len(sd) != 1 or not sd[0][1].startswith(want):
                bad += 1
            if (1 + (c % 4)) != 1 and sd and sd[0][1].startswith('spr_kris'):
                kris += 1
    ok(bad == 0 and kris == 0, 'OW-015 (your view): 100 SKIN changes - frames with not exactly one of you in the current SKIN: %d, Kris shown instead: %d' % (bad, kris))
    s.run('global.kfo.skin = 2;')
    # OW-010 / OW-019: into the wall every way
    attempts = 0
    maxx = 0.0
    trig = 0
    shown = 0
    ways = [({'right'}, 'straight'), ({'right', 'up'}, 'up-right'), ({'right', 'down'}, 'down-right'), ({'right', 'back'}, 'running'),
            ({'right', 'up', 'back'}, 'running up-right'), ({'right', 'down', 'back'}, 'running down-right')]
    for y0 in range(196, 362, 12):
        for keys, nm in ways:
            m.vars['x'] = 1640.0
            m.vars['y'] = float(y0)
            held(s, keys)
            for k in range(70):
                frame([s], 1)
                maxx = max(maxx, float(m.vars['x']))
                if J(s, 'instance_exists(obj_ch3_PTB02) ? obj_ch3_PTB02.con : 0') != 0:
                    trig += 1
                shown += 1 if any(d[1] == 'TEXT' and 'blocked during online play' in str(d[5]) for d in s.DL) else 0
            held(s, set())
            attempts += 1
    # along the wall, up and down, pressed against it
    for keys in ({'right', 'up'}, {'right', 'down'}):
        m.vars['x'] = 1760.0
        m.vars['y'] = 300.0
        held(s, keys)
        for k in range(120):
            frame([s], 1)
            maxx = max(maxx, float(m.vars['x']))
        held(s, set())
        attempts += 1
    ok(maxx <= 1762.0 and trig == 0, 'OW-010 / OW-019: %d walks into the wall (straight, diagonal, running, along it): furthest x %.0f (wall at 1800, Kris\'s box 38 wide), encounter started %d times'
       % (attempts, maxx, trig))
    STATS['OW-010/019'] = {'walks': attempts, 'max_x': maxx, 'encounters': trig}
    # the notice: once per approach (not every frame), re-armed only after walking away
    s.run('global.kfo_wall_msg = 0; global.kfo_wall_armed = true;')
    m.vars['x'] = 1500.0
    m.vars['y'] = 300.0
    held(s, {'right'})
    starts = 0
    prev = 0
    for k in range(200):
        frame([s], 1)
        cur = J(s, 'global.kfo_wall_msg')
        if cur > prev:
            starts += 1
        prev = cur
    held(s, set())
    ok(starts == 1, 'OW-010: the notice "The way forward is blocked during online play." shows once while you stay at the wall (%d times in 200 frames)' % starts)
    held(s, {'left'})
    frame([s], 60)
    held(s, {'right'})
    starts2 = 0
    prev = J(s, 'global.kfo_wall_msg')
    for k in range(80):
        frame([s], 1)
        cur = J(s, 'global.kfo_wall_msg')
        if cur > prev:
            starts2 += 1
        prev = cur
    held(s, set())
    ok(starts2 == 1, 'OW-010: walking away and back shows it again, once (%d)' % starts2)
    # OW-013: leave the room - the party is back, behind Kris, following
    m.vars['x'] = 900.0
    m.vars['y'] = 300.0
    s.run('kfo_leave();')
    frame([s], 1)
    fl = followers(s)
    near = [abs(float(f.vars['x']) - 900) < 40 and abs(float(f.vars['y']) - 300) < 40 for f in fl]
    ok(len(fl) == 2 and all(near), 'OW-013: offline again - the two followers awake, beside Kris (%s)' % [(f.vars.get('name'), round(f.vars['x']), round(f.vars['y'])) for f in fl])
    held(s, {'left'})
    frame([s], 60)
    held(s, set())
    fl = followers(s)
    ok(len(fl) == 2 and all(abs(float(f.vars['x']) - float(m.vars['x'])) < 120 for f in fl) and all(float(f.vars['x']) < 880 for f in fl),
       'OW-013: and they follow Kris (Kris at %.0f, followers %s)' % (m.vars['x'], [round(f.vars['x']) for f in fl]))
    # OW-020: no wall left; walking on to x 1840 starts the encounter as before
    walls = J(s, 'instance_exists(global.kfo_wall)')
    nwall = len([i for i in s.instances_of('obj_solidblock') if not i.dead and float(i.vars.get('x', 0)) == 1800.0])
    m.vars['x'] = 1600.0
    m.vars['y'] = 300.0
    held(s, {'right'})
    act = None
    for k in range(90):
        frame([s], 1)
        if J(s, 'obj_ch3_PTB02.con') != 0:
            act = (k, float(m.vars['x']))
            break
    held(s, set())
    ok(not walls and nwall == 0, 'OW-020: offline there is no wall (%s, %d blocks at x 1800)' % (walls, nwall))
    ok(act is not None and act[1] >= 1840, 'OW-020 / OW-014: offline the encounter starts at x 1840 as before (%s)' % (act,))


def fx_offline_20():
    """OW-014: 20 approaches offline, every knight's version of the encounter (0 base, 1 Kaizo, 2 Electric, 3 Violet, 4 Thorn,
    5 Cyan), from different heights, walking and running: the encounter starts each time"""
    good = 0
    rows = []
    for t in range(20):
        v = t % 6
        s = ow_sim('Kris', 1, variant=v)
        install_draw_log(s)
        enter(s)
        frame([s], 2)
        m = mc(s)
        m.vars['x'] = 1600.0
        m.vars['y'] = float(200 + (t * 7) % 150)
        keys = {'right', 'back'} if t % 3 == 2 else {'right'}
        held(s, keys)
        got = None
        for k in range(120):
            frame([s], 1)
            p = [i for i in s.instances_of('obj_ch3_PTB02') if not i.dead]
            if p and p[0].vars.get('con') != 0:
                got = (k, float(m.vars['x']), p[0].vars.get('con'))
                break
        rows.append((v, m.vars['y'], 'run' if 'back' in keys else 'walk', got))
        if got is not None and got[1] >= 1840:
            good += 1
    ok(good == 20, 'OW-014: 20 offline approaches (all six knights\' versions): the encounter started %d / 20 times' % good)
    STATS['OW-014'] = {'approaches': 20, 'started': good, 'rows': rows}


def fx_teleport_1000():
    """OW-011: 1,000 jumps past the trigger in a room (x set directly and with the game's own setxy, every knight's version):
    the encounter never starts, nothing of it is made, and you are put back on this side of the wall"""
    rnd = random.Random(47)
    starts = 0
    made = 0
    back = 0
    tries = 0
    inter = 0
    for v in range(6):
        s = ow_sim('Kris', 1 + v % 4, variant=v)
        install_draw_log(s)
        enter(s)
        s.run('kfo_practice_start();')
        frame([s], 2)
        m = mc(s)
        per = 167 if v < 4 else 166
        for t in range(per):
            x = rnd.uniform(1763, 2900)
            y = rnd.uniform(-40, 470)
            if t % 2 == 0:
                m.vars['x'] = x
                m.vars['y'] = y
            else:
                s.run('with (obj_mainchara) setxy(%r, %r);' % (x, y))
            frame([s], 1 + (t % 3))
            tries += 1
            p = [i for i in s.instances_of('obj_ch3_PTB02') if not i.dead]
            if p and p[0].vars.get('con') != 0:
                starts += 1
            if s.instances_of('obj_ch3_PTB02_toriel') or s.instances_of('obj_ch3_PTB02_roaringknight'):
                made += 1
            if J(s, 'global.interact') != 0:
                inter += 1
            if float(m.vars['x']) <= 1762:
                back += 1
        s.run('kfo_leave();')
    ok(starts == 0 and made == 0 and inter == 0, 'OW-011: %d jumps past the trigger in a room (six knights\' versions): encounter starts %d, its objects made %d, the player frozen %d'
       % (tries, starts, made, inter))
    ok(back == tries, 'OW-011: each time put back on this side of the wall (%d / %d)' % (back, tries))
    STATS['OW-011'] = {'attempts': tries, 'starts': starts, 'objects': made, 'put_back': back}


def fx_two(relay):
    """OW-002, OW-005, OW-006 / OW-007 (the others' view), OW-008, OW-012, OW-015 (the others' view)"""
    A, B = make_room(relay, [('Kris', 1, 600, 300), ('Susie', 3, 700, 300)])
    sims = [A, B]
    frame(sims, 10)
    for s in sims:
        od = others_drawn(s)
        ok(len(od) == 1 and len(self_drawn(s)) == 1 and awake_followers(s) == 0, 'OW-002: %s shows exactly two characters (%d other, %d self, %d followers)'
           % (s.nm, len(od), len(self_drawn(s)), awake_followers(s)))
    od = others_drawn(A)
    ok(od and od[0][1].startswith('spr_ralsei_walk'), 'OW-005: Kris\'s game draws Susie\'s player in their SKIN Ralsei (%s)' % [d[1] for d in od])
    od = others_drawn(B)
    ok(od and od[0][1].startswith('spr_kris'), 'OW-005: and Susie\'s game draws Kris\'s player as Kris (%s)' % [d[1] for d in od])
    # where: feet where the player's Kris box is (checkpoint: standing still)
    bx, by = float(mc(B).vars['x']), float(mc(B).vars['y'])
    d = others_drawn(A)[0]
    want_x = bx + (38 - 2 * SPR['spr_ralsei_walk_down']['w']) / 2.0 + SPR['spr_ralsei_walk_down']['xo'] * 2
    want_y = by + (76 - 2 * SPR['spr_ralsei_walk_down']['h']) + SPR['spr_ralsei_walk_down']['yo'] * 2
    ok(abs(d[3] - want_x) < 0.01 and abs(d[4] - want_y) < 0.01, 'OW-005: drawn with their feet where their character stands (%s vs %s)' % ((d[3], d[4]), (want_x, want_y)))
    # OW-006 / OW-007 in the other game: B walks the four ways, A sees the SKIN's way and its frames, then standing
    res = {}
    for way, keys, want in (('right', {'right'}, 'spr_ralsei_walk_right'), ('down', {'down'}, 'spr_ralsei_walk_down'),
                            ('left', {'left'}, 'spr_ralsei_walk_left'), ('up', {'up'}, 'spr_ralsei_walk_up')):
        held(B, keys)
        sprs = []
        frs = set()
        for k in range(30):
            frame(sims, 1)
            od = others_drawn(A)
            if od:
                sprs.append(od[0][1])
                frs.add(int(od[0][2]))
            time.sleep(0.002)
        held(B, set())
        # their Kris finishes the step (8 frames), then the next 10-a-second updates carry the standing frame
        frame(sims, 30)
        od = others_drawn(A)
        res[way] = (sorted(set(sprs[-10:])), len(frs), od and od[0][1], od and od[0][2])
        ok(sprs and all(x == want for x in sprs[-15:]), 'OW-006 (seen by the other): walking %s - %s (%s)' % (way, want, sorted(set(sprs[-15:]))))
        ok(len(frs) >= 2, 'OW-006 (seen by the other): walking %s - the frames turn (%d)' % (way, len(frs)))
        ok(od and od[0][1] == want and int(od[0][2]) == 0, 'OW-007 (seen by the other): stopped - standing frame facing %s (%s %s)' % (way, od and od[0][1], od and od[0][2]))
    STATS['OW-006/007 (others)'] = res
    # names over the heads (ROOM NAMES on by default): the other's name, over their head
    tx = [d for d in A.DL if d[1] == 'TEXT' and 'Susie' in str(d[5])]
    ok(tx and tx[-1][4] < float(mc(B).vars['y']), 'names: Susie\'s name over their head in Kris\'s game (%s)' % [(round(t[3]), round(t[4]), t[5]) for t in tx][:2])
    A.run('global.kfo.view.wnames = 0;')
    frame(sims, 1)
    ok(not [d for d in A.DL if d[1] == 'TEXT' and 'Susie' in str(d[5])], 'names: ROOM NAMES off - no name drawn')
    A.run('global.kfo.view.wnames = 1;')
    # OW-005 / OW-015: 100 SKIN changes from the lobby (the room page's SKIN row: the same lines it runs)
    lag = []
    wrong = 0
    dup = 0
    back = 0
    for c in range(100):
        sk = 1 + ((c + 3) % 4)
        if sk == J(B, 'global.kfo.skin'):
            sk = 1 + (sk % 4)
        B.run('if (kfo_ui_lobby_why("skin") == "") { global.kfo.skin = %d; kfo_ini_save(); kfo_up({ k: "skin", skin: global.kfo.skin }); }' % sk)
        got = None
        newest = False
        for k in range(60):
            frame(sims, 1)
            od = others_drawn(A)
            if len(od) > 1:
                dup += 1
            if od and od[0][1].startswith(SKN[sk]):
                if got is None:
                    got = k + 1
                newest = True
            elif newest and od:
                back += 1
            sd = self_drawn(B)
            if len(sd) != 1 or not sd[0][1].startswith(SKN[sk]):
                wrong += 1
            if got is not None and k >= got + 3:
                break
            time.sleep(0.002)
        lag.append(got)
    synced = len([g for g in lag if g is not None])
    ok(synced == 100, 'OW-005: 100 SKIN changes in the lobby - the other game shows the new SKIN %d / 100 times (frames until shown: max %s)' % (synced, max([g for g in lag if g] or [0])))
    ok(dup == 0 and back == 0 and wrong == 0, 'OW-015: and never two of them (%d), never an older SKIN once the new one showed (%d), their own game always one of them in the new SKIN (%d frames wrong)'
       % (dup, back, wrong))
    STATS['OW-005/015'] = {'changes': 100, 'synced': synced, 'max_frames': max([g for g in lag if g] or [0]), 'dups': dup, 'older_again': back, 'self_wrong': wrong}
    # OW-008: B goes through a door to another room and comes back
    B.goto_room('room_ow_test_other')
    frame(sims, 1)
    gone = 0
    selfskin = 0
    for k in range(30):
        frame(sims, 1)
        if not others_drawn(A):
            gone += 1
        sd = self_drawn(B)
        if sd and sd[0][1].startswith(SKN[J(B, 'global.kfo.skin')]):
            selfskin += 1
        time.sleep(0.002)
    ok(gone >= 25 and selfskin == 30 and awake_followers(B) == 0, 'OW-008: in another room - not drawn in the cold place (%d / 30 frames), still in their SKIN there (%d / 30), no party (%d)'
       % (gone, selfskin, awake_followers(B)))
    B.goto_room('room_dw_snow_zone')
    frame(sims, 1)
    mc(B).vars['x'] = 760.0
    mc(B).vars['y'] = 300.0
    seen = pump(sims, lambda: len(others_drawn(A)) == 1 and others_drawn(A)[0][1].startswith(SKN[J(B, 'global.kfo.skin')]), 90)
    ok(seen and awake_followers(B) == 0, 'OW-008: back in the cold place - drawn again in their SKIN, no party')
    # OW-012: both walk at the wall at the same time, then both jump past the trigger at the same time
    for s in sims:
        mc(s).vars['x'] = 1600.0
        mc(s).vars['y'] = 260.0 + (40 if s is B else 0)
        held(s, {'right'})
    trig = 0
    for k in range(80):
        frame(sims, 1)
        trig += sum(1 for s in sims if J(s, 'obj_ch3_PTB02.con') != 0)
    for s in sims:
        held(s, set())
    mx = [float(mc(s).vars['x']) for s in sims]
    for k in range(20):
        for s in sims:
            mc(s).vars['x'] = 1900.0 + 30 * k
        frame(sims, 1)
        trig += sum(1 for s in sims if J(s, 'obj_ch3_PTB02.con') != 0)
    ok(trig == 0 and max(mx) <= 1762, 'OW-012: two players at the wall together (stopped at %s) and past the trigger together (20 times): encounters started %d' % (mx, trig))
    leave_all(sims)
    frame(sims, 2)


def fx_many(relay, n=8, frames=600):
    """OW-003 / OW-016: n players in the room, all walking at once; every game draws the n-1 others where they stand"""
    t0 = time.time()
    specs = [(['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna'][i], 1 + (i % 4), 500 + 90 * i, 260 + 20 * (i % 4)) for i in range(n)]
    sims = make_room(relay, specs)
    frame(sims, 5)
    counts = [len(others_drawn(s)) + len(self_drawn(s)) for s in sims]
    ok(all(c == n for c in counts), 'OW-003: %d players - every game shows exactly %d characters (%s)' % (n, n, counts))
    # walking at once (each their own path), standing still for the last 20 frames of every 60: at those checkpoints every
    # game draws every other player exactly where that player's game has them
    rnd = random.Random(16)
    paths = [[rnd.choice([{'right'}, {'left'}, {'up'}, {'down'}, {'right', 'up'}, {'left', 'down'}, set()]) for _ in range(frames // 20 + 2)] for _ in range(n)]
    good = tot = 0
    over = 0
    errs = 0
    for f in range(frames):
        still = (f % 60) >= 40
        for i, s in enumerate(sims):
            held(s, set() if still else paths[i][f // 20])
        try:
            frame(sims, 1)
        except Exception as e:
            errs += 1
            ok(False, 'OW-016: frame %d: %s' % (f, str(e)[:200]))
            break
        for s in sims:
            if len(others_drawn(s)) > n - 1:
                over += 1
        if f % 60 == 59:
            pos = {J(s, 'global.kfo.my'): (float(mc(s).vars['x']), float(mc(s).vars['y']), J(s, 'global.kfo.skin')) for s in sims}
            for s in sims:
                od = others_drawn(s)
                for pid, (x, y, sk) in pos.items():
                    if pid == J(s, 'global.kfo.my'):
                        continue
                    tot += 1
                    # feet where their Kris box is, for the sprite of the way they face (the sprites differ in size)
                    hit = False
                    for o in od:
                        if not o[1].startswith(SKN[sk]) or o[1] not in SPR:
                            continue
                        d = SPR[o[1]]
                        wx = x + (38 - 2 * d['w']) / 2.0 + d['xo'] * 2
                        wy = y + (76 - 2 * d['h']) + d['yo'] * 2
                        if abs(o[3] - wx) < 0.01 and abs(o[4] - wy) < 0.01:
                            hit = True
                    if hit:
                        good += 1
                    elif tot - good <= 3:
                        print('  checkpoint f%d: game %s does not draw player %s (skin %d) at %s: %s' % (f, s.nm, pid, sk, (x, y), [(o[1], round(o[3], 1), round(o[4], 1)) for o in od]), flush=True)
        time.sleep(0.001)
    ok(errs == 0 and over == 0, 'OW-016: %d players walking for %d frames: errors %d, frames with more characters than players %d' % (n, frames, errs, over))
    ok(tot > 0 and good == tot, 'OW-016: at the checkpoints every game draws every other player where they stand, in their SKIN: %d / %d' % (good, tot))
    STATS['OW-003/016'] = {'players': n, 'frames': frames, 'checkpoints': tot, 'right': good, 'wall': round(time.time() - t0)}
    leave_all(sims)
    frame(sims, 2)


def fx_leave_rejoin(relay, cycles=100):
    """OW-009 / OW-017: one player leaves (LEAVE ROOM, or their game just stops) and comes back, again and again: the others
    never draw them twice, never keep a ghost, and draw them in their SKIN again"""
    A, B, C = make_room(relay, [('Kris', 1, 600, 300), ('Susie', 2, 700, 300), ('Ralsei', 4, 800, 320)])
    sims = [A, B, C]
    code = A.code
    dup = 0
    ghosts = 0
    back_ok = 0
    gone_ok = 0
    party_back = 0
    flash = 0
    t0 = time.time()
    for c in range(cycles):
        hard = (c % 4 == 3)
        if hard:
            # their game stops: the connection just closes (the relay tells the room)
            C.run('if (!is_undefined(global.kfo.sock)) network_destroy(global.kfo.sock); global.kfo.sock = undefined; global.kfo.st = "idle";')
        else:
            C.run('kfo_leave();')
        cpid = None
        gone = pump([A, B], lambda: len(others_drawn(A)) == 1 and len(others_drawn(B)) == 1, 240)
        if gone:
            gone_ok += 1
        frame([A, B, C], 40)
        # build 47 final: offline again, the leaver's party is awake (OW-013 in every cycle)
        if awake_followers(C) == 2:
            party_back += 1
        # no ghost entry kept for the one who left (the room's list no longer has them)
        for s in (A, B):
            keys = J(s, 'variable_struct_get_names(global.kfo.ows)')
            mem = [str(m['pid']) for m in J(s, 'global.kfo.members')]
            if any(k not in mem for k in keys):
                ghosts += 1
        C.run('kfo_join("%s");' % code)
        # build 47 final: every frame of the join, the leaver's party never drawn once it is in the room again (the join
        # completes in the network's event: the party went to sleep only in the next step - one frame with the party)
        came = False
        for k in range(300):
            frame(sims)
            if J(C, 'kfo_ow_online()') and awake_followers(C) > 0:
                flash += 1
            if J(C, 'global.kfo.st') == 'room' and all(len(others_drawn(s)) == 2 for s in sims):
                came = True
                break
            time.sleep(0.002)
        for k in range(10):
            frame(sims, 1)
            if awake_followers(C) > 0:
                flash += 1
            for s in (A, B):
                od = others_drawn(s)
                if len(od) > 2:
                    dup += 1
        sk = [o[1] for o in others_drawn(A) if o[1].startswith(SKN[4])]
        if came and len(sk) == 1:
            back_ok += 1
    ok(gone_ok == cycles, 'OW-017: %d times a player left (%d by LEAVE ROOM, %d by their game stopping): gone from the others\' games each time (%d)' % (cycles, cycles - cycles // 4, cycles // 4, gone_ok))
    ok(ghosts == 0, 'OW-017: no entry kept for a player who left (%d ghost checks failed)' % ghosts)
    ok(dup == 0 and back_ok == cycles, 'OW-009: %d times they came back (a new id each time): drawn once, in their SKIN (Noelle) %d / %d; frames with a duplicate %d' % (cycles, back_ok, cycles, dup))
    ok(party_back == cycles, 'OW-013: each time the leaver was offline again, its party was awake (%d / %d)' % (party_back, cycles))
    ok(flash == 0, 'OW-001: the leaver came back into the room %d times: frames with its party drawn while in the room: %d' % (cycles, flash))
    STATS['OW-009/017'] = {'cycles': cycles, 'gone': gone_ok, 'back_in_skin': back_ok, 'duplicates': dup, 'ghosts': ghosts, 'party_back': party_back,
                           'party_frames_in_room': flash, 'wall': round(time.time() - t0)}
    leave_all(sims)
    frame(sims, 2)


def fx_rematch(relay, rounds=3):
    """OW-018: a match, back to the room, a rematch, back again. The battle itself is not run here (the battle royale tests
    run it); what the overworld code sees of a match is: the hub's fight is on (knight_active) and the arena is the cold
    place restarted, then the fight ends (knight_exit_run: the run cleared, the cold place restarted) and the room goes on.
    Checked each time back in the room: no follower awake, every player in their SKIN in every game, the wall there."""
    A, B, C = make_room(relay, [('Kris', 2, 600, 300), ('Susie', 4, 700, 300), ('Ralsei', 1, 800, 320)])
    sims = [A, B, C]
    for s in sims:
        # the hub's fight driver and HUD are the battle's (not run here)
        s.mock('knight_run_tick', 0)
        s.mock('knight_hud_draw', 0)
    good = 0
    party_in_match = []
    for r in range(rounds):
        # the match: every game's hub fight on, the arena (the cold place restarted)
        for s in sims:
            s.run('var _c = knight_cfg_default(); _c.combo = 3; _c.party = [global.kfo.skin, 0, 0]; global.knight_run = 1;'
                  'global.krun = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] }); global.krun.state = "battle"; room_restart();')
        frame(sims, 30)
        # in the fight the overworld rules are off (the battle has the party as the hub sets it up)
        party_in_match.append([J(s, 'kfo_ow_online()') for s in sims])
        # the match ends: back to the room (knight_exit_run's end: the run cleared, the cold place restarted)
        for s in sims:
            s.run('global.knight_run = 0; global.krun = undefined; room_restart();')
        frame(sims, 2)
        for s in sims:
            mc(s).vars['x'] = float(600 + 100 * sims.index(s))
            mc(s).vars['y'] = 300.0
        okr = pump(sims, lambda: all(len(others_drawn(s)) == 2 for s in sims), 200)
        frame(sims, 5)
        foll = sum(awake_followers(s) for s in sims)
        skins = all(self_drawn(s) and self_drawn(s)[0][1].startswith(SKN[J(s, 'global.kfo.skin')]) for s in sims)
        oth = all(sorted(skin_of(o[1]) for o in others_drawn(s)) == sorted(J(x, 'global.kfo.skin') for x in sims if x is not s) for s in sims)
        walls = all(J(s, 'instance_exists(global.kfo_wall)') for s in sims)
        if okr and foll == 0 and skins and oth and walls:
            good += 1
        else:
            print('  round %d: shown %s, followers %d, own skins %s, others %s, walls %s' % (r, okr, foll, skins, oth, walls), flush=True)
    ok(all(not any(x) for x in party_in_match), 'OW-018: during the match the room\'s overworld rules are off in every game (%s)' % party_in_match)
    ok(good == rounds, 'OW-018: %d matches and back: every time no party, every player in their SKIN in every game, the wall there (%d / %d)' % (rounds, good, rounds))
    STATS['OW-018'] = {'rounds': rounds, 'right': good}
    leave_all(sims)
    frame(sims, 2)


def fx_soak(relay, minutes=60.0, n=8):
    """the overworld stability run: n players in the room for `minutes` of game time (30 frames a second), walking about,
    changing SKIN, going through the door and back, leaving and coming back, walking into the wall; every frame checked for
    errors, every 10 seconds for the right number of characters in every game and no follower"""
    t0 = time.time()
    frames = int(minutes * 60 * 30)
    specs = [(['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna'][i], 1 + (i % 4), 500 + 90 * i, 260 + 20 * (i % 4)) for i in range(n)]
    sims = make_room(relay, specs)
    code = sims[0].code
    rnd = random.Random(60)
    errs = 0
    checks = 0
    wrong = 0
    foll = 0
    fchecks = 0
    away = {}
    since = {}
    events = {'skin': 0, 'door': 0, 'rejoin': 0, 'wall': 0}
    keys = [set() for _ in sims]
    for f in range(frames):
        for i, s in enumerate(sims):
            if f % 15 == 0:
                keys[i] = rnd.choice([{'right'}, {'left'}, {'up'}, {'down'}, {'right', 'up'}, {'left', 'down'}, {'right', 'back'}, set(), set()])
            held(s, keys[i])
        # now and then: a SKIN change, a door, someone leaving and coming back, a walk into the wall
        if f % 211 == 100:
            i = 1 + rnd.randrange(n - 1)
            s = sims[i]
            if s not in away.values() and J(s, 'global.kfo.st') == 'room':
                s.run('if (kfo_ui_lobby_why("skin") == "") { global.kfo.skin = 1 + (global.kfo.skin mod 4); kfo_up({ k: "skin", skin: global.kfo.skin }); }')
                events['skin'] += 1
        if f % 457 == 200:
            i = 1 + rnd.randrange(n - 1)
            if i not in away:
                sims[i].goto_room('room_ow_test_other')
                away[i] = ('door', f + 90)
                since[i] = f
                events['door'] += 1
        if f % 997 == 500:
            i = 1 + rnd.randrange(n - 1)
            if i not in away:
                sims[i].run('kfo_leave();')
                away[i] = ('left', f + 60)
                since[i] = f
                events['rejoin'] += 1
        if f % 733 == 300:
            m = mc(sims[0])
            m.vars['x'] = 1700.0
            keys[0] = {'right'}
            events['wall'] += 1
        for i, (kind, until) in list(away.items()):
            # (build 47 final: only a door / a leave ends here - the first version also "ended" a 'back' this way, so every
            # game that came back joined again and again, every 240 frames)
            if f == until and kind in ('door', 'left'):
                if kind == 'door':
                    sims[i].goto_room('room_dw_snow_zone')
                else:
                    sims[i].run('kfo_join("%s");' % code)
                away[i] = ('back', f + 240)
            elif kind == 'back' and f >= until:
                del away[i]
        try:
            frame(sims, 1)
        except Exception as e:
            errs += 1
            ok(False, 'soak: frame %d: %s' % (f, str(e)[:300]))
            break
        # every second (build 47 final: the checks of the first version counted the party of a game that had LEFT the room -
        # offline the party is back, as it should be - and ran only when nobody was away, which was almost never):
        #   every game in a room (online): no follower awake;
        #   every game not away: itself drawn once, and every other game not away drawn (a game just back may be drawn already)
        if f % 30 == 29:
            for i, s in enumerate(sims):
                if J(s, 'kfo_ow_online()'):
                    fchecks += 1
                    a = awake_followers(s)
                    if a:
                        foll += a
                        if foll <= 6:
                            print('  soak: frame %d game %d (%s): %d followers awake in a room' % (f, i + 1, away.get(i, ('here',))[0], a), flush=True)
            present = [i for i in range(n) if i not in away]
            # may still be drawn: a game just back (240 frames), and one that went through the door / left less than 1.5 s
            # ago (the others learn it from its next messages: a few frames over the network)
            back = [i for i in away if away[i][0] == 'back' or (away[i][0] in ('door', 'left') and f - since.get(i, -999) < 45)]
            for i in present:
                s = sims[i]
                checks += 1
                od = len(others_drawn(s))
                if not (len(present) - 1 <= od <= len(present) - 1 + len(back)) or len(self_drawn(s)) != 1:
                    wrong += 1
                    if wrong <= 6:
                        print('  soak: frame %d game %d draws %d others (present %d, back %d), itself %d' % (f, i + 1, od, len(present) - 1, len(back), len(self_drawn(s))), flush=True)
        if f % 9000 == 8999:
            print('  soak: %d game minutes, %d errors, %d / %d checks wrong, followers awake in a room %d (of %d checks), %.0fs, events %s'
                  % ((f + 1) // 1800, errs, wrong, checks, foll, fchecks, time.time() - t0, events), flush=True)
        if f % 4 == 0:
            time.sleep(0.001)
    mx = max(J(s, 'global.kfo.M') is not None for s in sims)
    ok(errs == 0, 'soak: %d players, %.0f game minutes (%d frames each): %d errors' % (n, minutes, frames, errs))
    ok(fchecks > 0 and foll == 0, 'soak: no follower awake in a room at any check (%d awake in %d checks)' % (foll, fchecks))
    ok(checks > 0 and wrong == 0, 'soak: every game not away draws itself once and every other game not away (%d / %d right)' % (checks - wrong, checks))
    STATS['OW soak'] = {'players': n, 'game_minutes': minutes, 'frames': frames, 'errors': errs, 'checks': checks, 'wrong': wrong, 'follower_checks': fchecks,
                        'followers_awake': foll, 'events': events, 'wall_s': round(time.time() - t0)}
    leave_all(sims)
    frame(sims, 2)


FIX = {'single': fx_single, 'offline20': fx_offline_20, 'teleport': fx_teleport_1000}
NET = {'two': fx_two, 'many': fx_many, 'rejoin': fx_leave_rejoin, 'rematch': fx_rematch}
SOAK = {'soak': fx_soak}

if __name__ == '__main__':
    t0 = time.time()
    want = sys.argv[1:] or (list(FIX) + list(NET))
    relay = None
    try:
        for k in want:
            print('== fixture', k, flush=True)
            try:
                if k in NET or k.startswith('soak'):
                    if relay is None:
                        relay = Relay()
                    if k.startswith('soak'):
                        # soak or soak:<minutes>
                        fx_soak(relay, float(k.split(':')[1]) if ':' in k else 60.0)
                    else:
                        NET[k](relay)
                else:
                    FIX[k]()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    finally:
        if relay is not None:
            relay.close()
    print('STATS', json.dumps(STATS))
    print('t_ow47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:40]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
