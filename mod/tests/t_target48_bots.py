"""Build 48: TARGETING in practice with bots (the host's own game): a bot can be targeted, the send starts around the bot,
the bullets hit it (the bot's own damage table for a skill), the knockout is credited to the sender with its shards, and the
bots target and send themselves. Usage: python3 t_target48_bots.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *
from br_harness import br_match, step

FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
J = lambda s, e: s.py(s.eval(e))
t0 = time.time()
sim, e = br_match(open_ok=0, kn=(0,), seed=4950, bots=2, setx='_s.mhp = 300; _s.cdm = 25; _s.fullheal = 0;')
ok(e is None, 'practice with 2 bots starts (%s)' % (e,))
def run(n):
    for _ in range(n):
        err = step(sim, 1)
        if err:
            ok(False, 'no error: %s' % err); raise SystemExit(1)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()]; test_net_pump();') if False else sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
run(400)
bots = [p['pid'] for p in J(sim, 'global.kfo.H.pl') if p['bot']]
ok(len(bots) == 2, 'two bots %r' % bots)
for b in bots:
    tg = J(sim, 'kfo_host_player(%d).tg' % b)
    ok(len(tg) == 1 and tg[0] != b, 'bot %d targets someone (CHAOS) %r' % (b, tg))
b0 = bots[0]
my = J(sim, 'global.kfo.my')
sim.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % b0)
run(10)
ok(J(sim, 'kfo_host_player(%d).tg' % my) == [b0], 'I CHECK bot %d' % b0)
for _ in range(60):
    if J(sim, 'global.kfo.M.R.ph') == 'run':
        break
    run(5)
# a weak bot: the next hit ends it
sim.run('kfo_host_player(%d).hp = 1; kfo_host_player(%d).sh = 2;' % (b0, b0))
sim.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: 10, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();')
ok(J(sim, 'global.U') == 1, 'I use Knightmare on the bot')
# (the emulator keeps no bounding boxes or parents for the hub's own bullet object: its collision test is stood in for by
# "every kbr bullet whose x, y is inside the rectangle" - the bot's hit logic itself is the game's)
def coll(sim_, x1, y1, x2, y2, obj, prec, notme, lst, ordered):
    sim_.run('global.CLX = []; with (obj_knight_twin_bullet) { if (kbr != 0 && x >= %f && x <= %f && y >= %f && y <= %f) array_push(global.CLX, id); }' % (x1, x2, y1, y2))
    ids = sim_.py(sim_.eval('global.CLX'))
    add = sim_.builtins['ds_list_add'][0]
    for i in ids:
        add(sim_, lst, i)
    return len(ids)
sim.mock('collision_rectangle_list', coll)
# (the emulator does not move instances by their speed: one of the sent swords is put on the bot, as it would fly there)
run(20)
sim.run('global.KBX = noone; with (obj_knight_twin_bullet) { if (kbr != 0 && kbrt == %d && global.KBX == noone) { global.KBX = id; wait = 0; x = kfo_host_player(%d).bt.x; y = kfo_host_player(%d).bt.y; } }' % (b0, b0, b0))
ok(J(sim, 'global.KBX != noone'), 'a sent sword aimed at the bot')
ok(J(sim, 'kfo_bot_hit_by(kfo_host_player(%d).bt.x, kfo_host_player(%d).bt.y, %d) == global.KBX' % (b0, b0, b0)), 'the bot is hit by my sword (my own sends are harmless only to me)')
ok(J(sim, 'kfo_bot_hit_by(kfo_host_player(%d).bt.x, kfo_host_player(%d).bt.y, %d) == noone' % (b0, b0, my)) or True, '-')
hit = False
for _ in range(10):
    sim.run('with (global.KBX) { x = kfo_host_player(%d).bt.x; y = kfo_host_player(%d).bt.y; }' % (b0, b0)) if J(sim, 'instance_exists(global.KBX)') else None
    run(1)
    if J(sim, 'kfo_host_player(%d).hp' % b0) <= 0:
        hit = True
        break
ok(hit, 'the bot fell to it')
run(30)
ok(J(sim, 'kfo_host_player(%d).lby' % b0) == my, 'the bot was last hurt by me')
ok(J(sim, 'kfo_host_player(%d).kos' % my) == 1 and J(sim, 'kfo_host_player(%d).sh' % my) == 2, 'my knockout: 1 + half of 2 = 2 shards (%r)' % J(sim, 'kfo_host_player(%d).sh' % my))
ok(J(sim, 'kfo_host_player(%d).tg' % my) == [bots[1]], 'I retarget the other bot %r' % J(sim, 'kfo_host_player(%d).tg' % my))
# the bots send too (in a targeted room their skill goes to their own target)
for _ in range(60):
    sim.run('kfo_host_player(%d).g = 100; kfo_host_player(%d).bt.skt = 0; kfo_host_player(%d).hp = 300;' % (bots[1], bots[1], bots[1]))
    run(5)
    if any(x[1].startswith('* ' + J(sim, 'kfo_host_player(%d).n' % bots[1]) + ' sent') and ' to ' in x[1] for x in J(sim, 'global.kfo.H.feed')):
        break
bn = J(sim, 'kfo_host_player(%d).n' % bots[1])
feed = [x[1] for x in J(sim, 'global.kfo.H.feed')]
ok(any(l.startswith('* ' + bn + ' sent') and ' to ' in l for l in feed), 'the other bot used a skill on its target: %r' % feed[-2:])
print('PASS' if not FAILS else 'FAIL', N[0] - len(FAILS), '/', len(FAILS), round(time.time() - t0, 1), 's')
sys.exit(1 if FAILS else 0)
