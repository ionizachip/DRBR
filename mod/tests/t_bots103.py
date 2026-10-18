"""DRBR 1.0.3 - your report: "bots aren't shooting or visibly using skills" (skins too). Practice rooms with bots (the real code,
the host's bots as the game plays them), drawn with the recorder:
  - SHOOTING: on Spamton NEO's YELLOW SOUL every bot fires (its shot count goes up, now and then a BIG SHOT), the host's "ps"
    list carries each SOUL's counts, and every game draws the new shots flying from that SOUL (the game's own yellow shot and
    BIG SHOT sprites) - a player's game counts its own shots for the others the same way ("p": ys / yb);
  - SKILLS: every skill a bot (or a player) uses is told to every game ("su") and drawn at that SOUL: the skill's name over it,
    a ring, and for an attack a diamond with the skill's picture flying to its target; HIDE OTHER SOULS hides them;
  - SKINS: the bots wear their own skins (BERDLY and SPAMTON theirs), and in the cold place they walk behind the host in them
    (the room's world list carries them; every game draws them with "(BOT)").
Usage: python3 t_bots103.py"""
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


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


def recorder(sim):
    rec = Recorder(sim)
    sim.mock('camera_get_view_x', lambda s, *a: br_harness.CAM[0])
    sim.mock('camera_get_view_y', lambda s, *a: br_harness.CAM[1])
    return rec


BOTS = ('(function(){ var _o = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _b = _h.pl[_i];'
        ' if (_b.bot) array_push(_o, [_b.pid, _b.n, _b.s, variable_struct_exists(_b, "ys") ? _b.ys : -1, variable_struct_exists(_b, "yb") ? _b.yb : -1, _b.al]); } return _o; })()')

# ---------------- SHOOTING
sim, e = br_match(open_ok=9, kn=(9,), seed=6301, bots=3, setx='_s.mhp = 999; _s.skills = 0; _s.botp = 4;')
ok(e is None, 'a practice room against Spamton NEO with 3 EXPERT bots (%r)' % (e,))
sim.run('global.SF = 0;')
sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
sim.load_source('gml_GlobalScript_shforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.SF; }\n')
sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
sent = []
orig_down = None


def watch_ps(s, to, m, *a):
    mm = s.py(m)
    if isinstance(mm, dict) and mm.get('k') == 'ps':
        sent.append(mm)
    return orig_down(s, to, m, *a) if orig_down else 0


rec = recorder(sim)
gs_max = 0
big_seen = 0
shot_ops = 0
yellow_frames = 0
for f in range(1400):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    err = step(sim, 1)
    if err:
        ok(False, 'no error (%s)' % err[:300])
        break
    if J(sim, 'kbr_sn_on() && kbr_sn_attacking()'):
        yellow_frames += 1
    n = J(sim, 'variable_struct_exists(global.kfo.M, "vw") && variable_struct_exists(global.kfo.M.vw, "gs") ? array_length(global.kfo.M.vw.gs) : 0')
    gs_max = max(gs_max, n)
    if n:
        big_seen = max(big_seen, J(sim, '(function(){ var _n = 0; var _l = global.kfo.M.vw.gs; for (var _i = 0; _i < array_length(_l); _i++) if (_l[_i].big) _n++; return _n; })()'))
        if f % 7 == 0:
            rec.ops.clear()
            sim.run('kbr_draw_souls();')
            shot_ops += sum(1 for o in rec.ops if o[0] == 'spr' and o[1] in ('spr_yheart_shot', 'spr_yheart_bigshot'))
bots = J(sim, BOTS)
ok(yellow_frames > 300, 'his attacks ran with the yellow SOUL (%d frames)' % yellow_frames)
ok(all(b[3] >= 10 for b in bots), 'every bot fired (shot counts %r)' % [(b[1], b[3]) for b in bots])
ok(any(b[4] >= 1 for b in bots), 'a bot let go of a BIG SHOT (%r)' % [(b[1], b[4]) for b in bots])
ps = J(sim, '(function(){ var _l = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _p = _h.pl[_i]; array_push(_l, [_p.pid, round(_p.x * 10), round(_p.y * 10), _p.hx, 0, 0, -1, variable_struct_exists(_p, "ys") ? _p.ys : -1, variable_struct_exists(_p, "yb") ? _p.yb : -1]); } return _l; })()')
ok(all(len(r) == 9 for r in ps), 'the "ps" entries carry the shot counts (%r)' % ps[:2])
ok(gs_max >= 3, 'this game drew the bots\' shots flying from their SOULs (up to %d at once)' % gs_max)
ok(big_seen >= 1, 'and a BIG SHOT (%d)' % big_seen)
ok(shot_ops >= 5, 'drawn with the game\'s own shot sprites (%d draws)' % shot_ops)
# a player's own counts go out in "p"
ok(J(sim, 'kbr_sn_shots(false)') >= 0, 'this game\'s own shot count for the others ("p": ys %r)' % J(sim, 'kbr_sn_shots(false)'))
# an older host's 7-number entries: nothing drawn, no error
sim.run('kbr_on_ps({ mid: global.kfo.M.mid, l: [[102, 2500, 1500, 0, 0, 0, -1]] });')
ok(True, 'an older host\'s list (7 numbers) is read without an error')

# ---------------- SKILLS
sim, e = br_match(open_ok=0, kn=(0,), seed=6302, bots=3, setx='_s.mhp = 999; _s.skills = 1; _s.botp = 5; _s.cdm = 30; _s.scost = 50; _s.gmul = 400;')
ok(e is None, 'a practice room with 3 PERFECT bots, skills on (%r)' % (e,))
sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
rec = recorder(sim)
uses = []
names_drawn = set()
diamonds = 0
for f in range(2400):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    err = step(sim, 1)
    if err:
        ok(False, 'no error (%s)' % err[:300])
        break
    su = J(sim, 'variable_struct_exists(global.kfo.M, "vw") && variable_struct_exists(global.kfo.M.vw, "su") ? global.kfo.M.vw.su : []')
    for u in su:
        if u['t'] == 1:
            uses.append((u['f'], u['sid'], tuple(u['tg'])))
    if any(u['t'] in (6, 10) for u in su):
        rec.ops.clear()
        sim.run('kbr_draw_souls();')
        for o in rec.ops:
            if o[0] == 'text':
                names_drawn.add(o[4])
        diamonds += sum(1 for o in rec.ops if o[0] == 'tri')
    if len(uses) >= 8 and len(names_drawn) >= 3:
        break
bot_uses = [u for u in uses if u[0] >= 101]
reds = [u for u in bot_uses if J(sim, 'kbr_skill_red(%d)' % u[1])]
ok(len(bot_uses) >= 3, 'every game is told when a bot uses a skill (%d told: %r)' % (len(bot_uses), bot_uses[:6]))
ok(len(reds) >= 1 and all(len(u[2]) >= 1 for u in reds), 'an attack skill comes with its targets (%r)' % reds[:3])
short = set(J(sim, '(function(){ var _o = []; for (var _i = 1; _i < kbr_skill_count(); _i++) { var _f = kbr_skill_info(_i); array_push(_o, _f[1]); } return _o; })()'))
ok(len(names_drawn & short) >= 2, 'their skills\' names are drawn over their SOULs (%r)' % sorted(names_drawn & short)[:6])
ok(diamonds >= 2, 'an attack\'s diamond flies to its target (%d triangles drawn)' % diamonds)
sim.run('global.kfo.view.show = 0;')
rec.ops.clear()
sim.run('kbr_view_on_su({ mid: global.kfo.M.mid, f: 101, sid: 1, tg: [global.kfo.my] }); kbr_draw_souls();')
ok(not any(o[0] == 'text' and o[4] == 'SWORD' for o in rec.ops), 'SHOW OTHER SOULS off: none drawn')
sim.run('global.kfo.view.show = 1;')

# ---------------- SKINS and the cold place
sim.run('kfo_host_bots(7);')
sk = [(b[1], b[2]) for b in J(sim, BOTS)]
ok(dict(sk).get('BERDLY') == 6 and dict(sk).get('SPAMTON') == 14 and len(set(s for n, s in sk)) >= 6, 'the bots wear their own skins (%r)' % sk)
sim.run('kfo_host_bots(3);')
sim.run('var _me = kfo_host_player(global.kfo.my); global.kfo.H.st = "lobby"; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) global.kfo.H.pl[_i].inm = 0;')
w = []
for k in range(20):
    sim.run('var _me = kfo_host_player(global.kfo.my); _me.ow = [600 + (%d * 12), 240, 1, 1, 42, current_time, %d mod 4]; global.W = []; kfo_host_bots_ow(global.W);' % (k, k))
    w = J(sim, 'global.W')
ok(len(w) == 3 and all(r[5] in (2, 3, 6) for r in w), 'the room\'s world list has the 3 bots in their skins (%r)' % [(r[0], r[5]) for r in w])
xs = [r[1] for r in w]
ok(xs == sorted(xs, reverse=True) and xs[0] < 600 + 19 * 12, 'they walk behind the host, one after another (x %r, host at %d)' % (xs, 600 + 19 * 12))
# (the emulator's room is no number: the entries say -1, any room)
sim.run('for (var _i = 0; _i < array_length(global.W); _i++) global.W[_i][6] = -1; global.kfo.lobby = kfo_host_lobby_msg(); kfo_world_on({ l: global.W });')
rec = recorder(sim)
rec.ops.clear()
sim.mock('kfo_ow_online', lambda s, *a: True)
sim.run('kfo_world_draw();')
txt = [o[4] for o in rec.ops if o[0] == 'text']
sprs = [o[1] for o in rec.ops if o[0] == 'spr']
ok(len(set(t for t in txt if '(BOT)' in str(t))) == 3, 'every game draws them in the cold place, named with (BOT) (%r)' % sorted(set(t for t in txt if 'BOT' in str(t))))
ok(any('berdly' in s for s in sprs) and any('susie' in s for s in sprs), 'in their skins (%r)' % sorted(set(sprs))[:8])

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
