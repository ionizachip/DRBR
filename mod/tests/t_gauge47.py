"""Build 47 (was t_gauge46; Hold Breath no longer drains or doubles grazes - the fights' own HoldBreath, a faster SOUL): skill charge accounting. The player's own match code (kbr_me_tick, kbr_on_graze, the skills'
charge and draw, hits) runs frame by frame with random input on the REAL keyboard functions - Hold Breath (the S key, build
46) on and off, the game's own slow key X (button2) held on its own now and then (it must NOT hold your breath any more), the
CHARGE key (C) held for a while and let go, grazes, hits, the slots emptied now and then so draws keep happening - for several
rooms (default, FAST CHARGE + DOUBLE GRAZE, other rates and costs, RANDOM SKILL COSTS, MAXIMUM CHAOS). Next to it a reference
ledger applies only the documented sources (about one point a second x CHARGE RATE, a graze x GRAZE CHARGE - doubled while
holding your breath -, Hold Breath's 1 every 20 frames, the charge spent on a draw, the 0..100 limits). Build 46 removed the
"+5 per five clean seconds" bonus: the ledger has none, so a bonus left anywhere shows as an unexplained gain, and no
"clean seconds" line may ever be logged. After every frame the game's gauge must equal the ledger.
Usage: python3 t_gauge46.py [frames per room (6000)] [seed]"""
import sys, os, json, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from br_shot import br_frame

FR = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 45
FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


def J(sim, e):
    return sim.py(sim.eval(e))


ROOMS = [('default', {}), ('fast+dgraze', {'m_fast': 1, 'm_dgraze': 1}), ('rates', {'gmul': 250, 'grz': 50, 'scost': 75, 'slots': 2, 'g0': 50}),
         ('rcost', {'m_rcost': 1, 'scost': 150}), ('chaos', {'m_chaos': 1})]
STATE = ('(function() { var _M = global.kfo.M; return { g: _M.g, af: _M.alive_f, cl: variable_struct_exists(_M, "clean") ? 1 : 0, hold: _M.hold, ch: _M.sk.charging, chg: _M.sk.charge,'
         ' sl: array_length(_M.sk.slots), need: kbr_skill_need(), need2: kbr_skill_need2(), slots: _M.eff.slots, gmul: _M.eff.gmul, grz: _M.eff.grz,'
         ' sk: _M.eff.skills, out: _M.out }; })()')
tot = {'frames': 0, 'unexplained': 0, 'draws': 0, 'grazes': 0, 'hits': 0, 'hold_frames': 0, 'x_only_frames': 0, 'tick_gain': 0.0, 'spent': 0.0}
R = random.Random(SEED)
for name, setx in ROOMS:
    m, _ = br_frame('t_gauge', n=4, out=(), render=False)
    inp = {'s': 0, 'c': 0, 'x': 0}
    # build 46: the keys are read with keyboard_check (S = Hold Breath, C = charge); X is the game's own slow (button2)
    m.mock('button2_h', lambda s: inp['x'])
    m.mock('button3_h', lambda s: 0)
    m.mock('button1_h', lambda s: 0)
    for b in ('left_h', 'right_h', 'up_h', 'down_h'):
        m.mock(b, lambda s: 0)
    m.define_object('obj_testbullet')
    m.run('global.TBI = instance_create(0, 0, obj_testbullet); global.kfo.hostid = 1; global.kfo.mode = "local"; var _M = global.kfo.M;'
          'var _s = kfo_set_clean(json_parse(%s)); _M.set = _s; _M.eff = kbr_eff(_s); _M.sk = kbr_skills_new(_M.eff); _M.out = false; _M.me = true;'
          'global.hp[1] = 100000000; global.maxhp[1] = 100000000; _M.g = clamp(_M.eff.g0, 0, 100); _M.alive_f = 0; _M.hold = false;'
          '_M.hold_was = false; _M.sd_on = false; _M.R.ph = "run"; global.knight_frozen = false; global.HI = instance_create(300, 160, obj_heart);'
          % json.dumps(json.dumps(setx)))
    s = J(m, STATE)
    ok(s['sk'] in (1, True), '%s: skills on' % name)
    g = s['g']
    ok(s['cl'] == 0, '%s: the match has no clean-seconds counter any more' % name)
    af, hold, ch, chg = s['af'], bool(s['hold']), bool(s['ch']), s['chg']
    s_left = 0
    x_left = 0
    c_left = 0
    bad = 0
    prev_s = 0
    room = {'draws': 0, 'grazes': 0, 'hits': 0}
    for f in range(FR):
        # input: Hold Breath (S) sessions, X (slow) sessions, C sessions (held 10-110 frames, then let go), grazes, hits, slots
        # emptied now and then
        if s_left <= 0 and R.random() < 0.01:
            s_left = R.randint(20, 160)
        inp['s'] = 1 if s_left > 0 else 0
        s_left -= 1
        if x_left <= 0 and R.random() < 0.01:
            x_left = R.randint(20, 160)
        inp['x'] = 1 if x_left > 0 else 0
        x_left -= 1
        if c_left <= 0 and R.random() < 0.02:
            c_left = R.randint(10, 110)
        inp['c'] = 1 if c_left > 0 else 0
        c_left -= 1
        held = set()
        if inp['s']:
            held.add(ord('S'))
        if inp['c']:
            held.add(ord('C'))
        m.input.pressed = held - m.input.held
        m.input.held = held
        if f % 500 == 0:
            m.run('global.kfo.M.sk.slots = [];')
        s = J(m, STATE)    # also rolls RANDOM SKILL COSTS' next cost before the frame (the code would roll it at the draw)
        # the ledger starts each frame from the game's numbers only if a mismatch was found (then counted)
        ngr = R.choice([0] * 8 + [1, 1, 2, 3])
        for _ in range(ngr):
            m.run('kbr_on_graze();')
            g = min(100.0, max(0.0, g + (s['grz'] / 100.0)))   # build 47: Hold Breath no longer doubles grazes
        room['grazes'] += ngr
        if R.random() < 0.012:
            m.run('with (global.TBI) global.D = kbr_dmg_taken(0);')
            room['hits'] += 1
        m.run('kbr_me_tick();')
        # the ledger's frame
        af += 1
        if af % 30 == 0:
            g2 = min(100.0, max(0.0, g + s['gmul'] / 100.0))
            tot['tick_gain'] += g2 - g
            g = g2
        # build 47: Hold Breath is the fights' own (a faster SOUL): no gauge needed, nothing drained
        # build 50: Hold Breath is a toggle - each press of S turns it on / off
        if inp['s'] and not prev_s:
            hold = not hold
        prev_s = inp['s']
        h = hold
        if h:
            tot['hold_frames'] += 1
        if inp['x'] and not inp['s']:
            tot['x_only_frames'] += 1
        drew = False
        if inp['c']:
            if not ch:
                ch = True
                chg = 0.0
            chg = min(g, chg + 1.5)
        elif ch:
            ch = False
            amt = math.floor(chg)
            chg = 0.0
            if amt >= s['need']:
                rm = max(1, min(4, s['slots'])) - s['sl']
                if rm > 0:
                    g = max(0.0, g - amt)
                    tot['spent'] += amt
                    drew = True
        t = J(m, STATE)
        if drew:
            room['draws'] += 1
            ok(t['sl'] > s['sl'], '%s frame %d: a draw the ledger expects put a skill in a slot' % (name, f))
        if abs(t['g'] - g) > 1e-6 or t['af'] != af or t['cl'] != 0 or bool(t['hold']) != hold:
            bad += 1
            if bad <= 5:
                print('UNEXPLAINED %s frame %d: game g=%.4f af=%s clean-field=%s hold=%s / ledger g=%.4f af=%s hold=%s (s=%d x=%d c=%d grazes=%d)'
                      % (name, f, t['g'], t['af'], t['cl'], t['hold'], g, af, hold, inp['s'], inp['x'], inp['c'], ngr), flush=True)
            g, af, hold = t['g'], t['af'], bool(t['hold'])
        ch, chg = bool(t['ch']), t['chg']
    ok(bad == 0, '%s: %d frames, the gauge always equals the ledger (%d unexplained)' % (name, FR, bad))
    logs = J(m, '(function() { var _o = []; var _l = global.kfo.M.log; for (var _i = 0; _i < array_length(_l); _i++) array_push(_o, _l[_i].t); return _o; })()')
    ok(not [l for l in logs if 'clean' in l.lower()], '%s: no clean-seconds line in the log (%r)' % (name, [l for l in logs if 'clean' in l.lower()][:2]))
    ok(room['draws'] > 5, '%s: draws happened (%d)' % (name, room['draws']))
    tot['frames'] += FR
    tot['unexplained'] += bad
    for k in ('draws', 'grazes', 'hits'):
        tot[k] += room[k]
    print(name, json.dumps(room), flush=True)
print('totals', json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in tot.items()}))
print('gauge accounting: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
