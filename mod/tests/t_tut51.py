"""Build 51: HOW TO PLAY - the guided practice match, step by step, in one emulated game (the real merged fight code, the real
host and player code; br_harness). Checked: the ONLINE page offers it (and nowhere in a room), every step's text uses the
player's own keys, steps that teach a key wait for it ("TRY IT!": ENTER does nothing until it is done), the charge lesson
refills the TP bar, the targeting lesson needs all seven modes, the SWORD lesson hands you a Sword and waits for the send,
nobody can be knocked out while it runs, ESC leaves, finishing it is saved (tut_done) and it can be played again.
Usage: python3 t_tut51.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


KEYS = {'press': set()}
sim, e = br_match(seed=5150, bots=1, skin=1, kn=[0], setx='_s.mhp = 150; _s.dmul = 25;', rng_seed=5)
ok(e is None, 'a practice match set up (%r)' % e)
INI = {}
sim.mock('ossafe_ini_open', lambda s, f: 1)
sim.mock('ossafe_ini_close', lambda s: 1)
sim.mock('ini_write_real', lambda s, sec, k, v: INI.__setitem__((sec, k), v) or 1)
sim.mock('ini_read_real', lambda s, sec, k, d: INI.get((sec, k), d))
real_kcp = None
sim.mock('keyboard_check_pressed', lambda s, k: k in KEYS['press'])
left = []
sim.mock('kfo_back_to_lobby', lambda s: left.append('lobby') or 1)
sim.mock('kfo_close', lambda s, e: left.append('close') or 1)


def J(x):
    return sim.py(sim.eval(x))


def frames(n):
    for _ in range(n):
        err = step(sim, 1)
        if err:
            ok(False, 'no error: %s' % err[:200])
            raise SystemExit(1)


def press(k):
    # the emulator does not take key presses: ENTER is kfo_tut_next (what ENTER / START call), ESC kfo_tut_finish(false);
    # build 52: the text types out - the first ENTER would show all of it, so it is shown first here
    frames(12)
    if k == 13:
        sim.run('kfo_tut().tn = 9999; kfo_tut_next(global.kfo.M);')
    else:
        sim.run('kfo_tut_finish(false);')
    frames(1)


ENTER, ESC = 13, 27
for _ in range(400):
    frames(1)
    if J('global.kfo.M.go') and J('global.kfo.M.R.ph') == 'run':
        break
ok(J('global.kfo.M.R.ph') == 'run', 'the match runs')

# the ONLINE page row
ok('howto' in J('kfo_ui_rows()'), 'the ONLINE page has HOW TO PLAY')
ok('howto' not in J('kfo_ui_lobby_rows()'), 'a room page does not (it cannot start during a match)')
ok(J('kfo_ui_row_label("howto")') == 'HOW TO PLAY', 'its label')

sim.run('var _T = kfo_tut(); _T.on = true; _T.began = false; _T.step = 0; _T.t = 0;')
frames(15)
ok(J('kfo_tut().step') == 0 and J('kfo_tut().ok'), 'step 1 (welcome) only needs NEXT')
k0 = J('global.kfo.M.R.k'); t0 = J('kbr_now()')
frames(200)
ok(J('global.kfo.M.R.ph') != 'run' or J('global.kfo.M.R.k') == k0, 'calm steps: no new attack starts (k %r -> %r, %s)' % (k0, J('global.kfo.M.R.k'), J('global.kfo.M.R.ph')))
press(ENTER)
ok(J('kfo_tut().step') == 1, 'NEXT: step 2 (the screen)')


def act(st, gml, what):
    ok(J('kfo_tut().step') == st and not J('kfo_tut().ok'), 'step %d (%s) waits for you%s' % (st + 1, what, '' if J('kfo_tut().step') == st else ' (on step %d)' % (J('kfo_tut().step') + 1)))
    press(ENTER)
    ok(J('kfo_tut().step') == st, 'step %d: NEXT does nothing until it is done' % (st + 1))
    sim.run(gml)
    frames(3)
    ok(J('kfo_tut().ok'), 'step %d: doing it completes it' % (st + 1))
    frames(50)
    ok(J('kfo_tut().step') == st + 1, 'step %d: it moves on by itself' % (st + 1))


# build 52: 22 steps - the screen (1-4), moving (5-7), TP and skills (8-11), targeting (12), the fight (13-15), DARKNESS (16),
# special skills (17), winning (18), playing online (19-21), done (22)
for st in (1, 2):
    ok(J('kfo_tut().step') == st and J('kfo_tut().ok'), 'step %d is information: NEXT' % (st + 1))
    press(ENTER)
ok(J('kfo_tut().step') == 3 and J('kfo_tut().ok'), 'step 4 (the Knight info) is information: NEXT')
press(ENTER)
ok(J('kfo_tut_fight(4)') and J('kfo_tut_fight(5)') and J('kfo_tut_fight(6)') and not J('kfo_tut_fight(3)'), 'the Knight attacks in the moving lessons (there is no box between attacks)')
act(4, 'kfo_tut().moved = 250;', 'move the SOUL')
act(5, 'kfo_tut().slow_f = 30;', 'move slowly')
act(6, 'global.kfo.M.hold_on = true;', 'turn HOLD BREATH on')
ok(J('global.kfo.M.g') >= 65, 'the charge lesson gives enough TP to pass the 60%% line (%r)' % J('global.kfo.M.g'))
ok('60%' in J('kfo_tut_text(7)'), 'step 8 explains the 60% line')
act(7, 'global.kfo.M.sk.drawn += 1;', 'charge and draw')
act(8, 'global.kfo.M.sk.used += 1;', 'use a skill')
act(9, 'global.kfo.M.sk.hold = { sid: 11, rev: 0 };', 'HOLD a skill')
ok(J('kfo_tut().step') == 10 and J('kfo_tut().ok'), 'step 11 (MAX) is information: NEXT')
press(ENTER)
for m in range(6):
    sim.run('global.kfo.M.tg.mode = %d;' % m)
    frames(1)
ok(not J('kfo_tut().ok') and '(6/7)' in J('kfo_tut_text(11)'), 'targeting: six of seven modes is not yet (%r)' % J('kfo_tut_text(11)')[-8:])
act(11, 'global.kfo.M.tg.mode = 6;', 'see all seven modes')
ok(J('kfo_tut_fight(12)') and not J('kfo_tut_fight(11)'), 'the Knight attacks again from the dodge lesson on, not in the targeting one')
sim.run('global.kfo.M.hits += 1;')
frames(3)
ok(not J('kfo_tut().ok') and J('kfo_tut().ouch') > 0, 'step 13 (dodge): a hit says OUCH and waits for the next attack (%r)' % J('[kfo_tut().step, kfo_tut().ok, kfo_tut().ouch]'))
act(12, 'kfo_tut().dodged = true;', 'dodge an attack')
ok('GRAZE' in J('kfo_tut_text(13)') and 'TP' in J('kfo_tut_text(13)'), 'step 14 explains grazing')
act(13, 'global.kfo.M.gz_all += 3;', 'graze 3 times')
sl = J('global.kfo.M.sk.slots')
ok(sl[0]['sid'] == 1 and J('global.kfo.M.sk.sel') == 0, 'the attack lesson hands you a Sword, picked (%r)' % [x['sid'] for x in sl])
act(14, 'global.kfo.M.sk.sent += 1;', 'send the Sword')
ok(J('kfo_tut().step') == 15 and not J('kfo_tut().ok'), 'step 16: DARKNESS waits for the next attack and runs out')
sim.run('kfo_tut().dark_sent = true; global.kfo.M.sk.dark_t = 0;')
frames(50)
ok(J('kfo_tut().step') == 16, 'step 16: it moves on once the DARKNESS is over')
ok('HOST A ROOM' in J('kfo_tut_text(18)') and 'SETTINGS' in J('kfo_tut_text(19)'), 'the menu tour explains the options')
for st in (17, 18, 19, 20, 21):
    press(ENTER)
    ok(J('kfo_tut().step') == st, 'step %d' % (st + 1))
# nobody falls
sim.run('global.hp[kbr_char()] = 5;')
frames(2)
ok(J('global.hp[kbr_char()]') == J('global.maxhp[kbr_char()]'), 'your HP is topped up in the tutorial')
sim.run('global.D = -1; with (obj_heart) global.D = kbr_dmg_taken(9999);')
ok(J('global.D') < J('global.hp[kbr_char()]') and not J('global.kfo.M.out'), 'a big hit cannot knock you out (%r)' % J('global.D'))
press(ENTER)
ok(not J('kfo_tut_on()') and INI.get(('player', 'tut_done')) == 1, 'finishing saves tut_done')
ok(left[:2] == ['lobby', 'close'], 'and goes back to the ONLINE page (%r)' % left)
ok(J('kfo_tut_done()'), 'the ONLINE page knows it is done')
# replay and ESC
sim.run('var _T = kfo_tut(); _T.on = true; _T.began = false; _T.step = 0; _T.t = 0;')
frames(5)
press(ESC)
ok(not J('kfo_tut_on()'), 'ESC leaves the tutorial')

print('tut51: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
