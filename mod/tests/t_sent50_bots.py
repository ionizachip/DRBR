"""Build 50: the bots and the new attack items. A practice match (the host's own game) with six bots, one per preset (DUMMY ...
PERFECT), every knight in the pool, the emulator's motion and collision stand-in (bbox_model). I target every bot (ROARING)
and use every item in turn; the bots draw and use skills themselves (they send real attacks at me).

  - each item puts up its hidden copy around every bot (twin bullets aimed at that bot: never shown, never a hit for me);
  - the bots dodge them: hits taken go down with the bot's skill (DUMMY > ... > PERFECT, PERFECT few);
  - the bots' own sends at me are the real Knight objects in my game; the bots' hit test runs among them without an error;
  - no errors over the whole run.
Usage: python3 t_sent50_bots.py   (BOT_FRAMES=3600 by default)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *
from br_harness import br_match, step
import bbox_model
import t_view47

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


J = lambda s, e: s.py(s.eval(e))
PRE = ['DUMMY', 'EASY', 'NORMAL', 'HARD', 'EXPERT', 'PERFECT']
ITEMS = [1, 2, 3, 4, 5, 6, 7, 10, 17, 18, 19, 20, 21]

sim, e = br_match(open_ok=0, kn=(0, 1, 2, 3, 4, 5), seed=5051, bots=6, setx='_s.mhp = 999; _s.cdm = 25;')
ok(e is None, 'practice with 6 bots (%s)' % (e,))
bbox_model.install(sim)
src = t_view47.func_src('kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
sim.load_source('gml_GlobalScript_sent50b_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')
sim.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; _c.pre = _i; global.kfo.H.botcfg[_i] = _c; }')
my = J(sim, 'global.kfo.my')
frames = int(os.environ.get('BOT_FRAMES', '3600'))
t0 = time.time()
used = 0
copies = {}
leaks = 0
real_at_me = set()
item_i = 0
for f in range(frames):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];'
            'for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) _b.hp = _b.mh; }')
    if f == 300:
        sim.run('global.kfo.M.tg.mode = 6; kbr_tg_send(global.kfo.M, true);')
    # every 90 frames of a running attack: the next item at every bot
    if f > 320 and f % 90 == 0 and J(sim, 'global.kfo.M.R.ph') == 'run':
        sid = ITEMS[item_i % len(ITEMS)]
        item_i += 1
        sim.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
        if J(sim, 'global.U') == 1:
            used += 1
            for _ in range(3):
                err = step(sim, 1)
                if err:
                    ok(False, 'error after item %d: %s' % (sid, err[:300]))
                    raise SystemExit(1)
                bbox_model.move(sim)
            n = J(sim, 'instance_number(obj_knight_twin_bullet)')
            vis = J(sim, '(function(){ var _n = 0; with (obj_knight_twin_bullet) { if (kbr != 0 && kbrt != global.kfo.my && (visible || active)) _n++; } return _n; })()')
            copies[sid] = max(copies.get(sid, 0), n)
            leaks += vis
    err = step(sim, 1)
    if err:
        ok(False, 'error at frame %d: %s' % (f, err[:400]))
        raise SystemExit(1)
    bbox_model.move(sim)
    if f % 30 == 0:
        sim.log.clear()
        for nm in J(sim, '(function(){ var _r = []; with (obj_bulletparent) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_r, object_get_name(object_index)); } return _r; })()'):
            real_at_me.add(nm)
sim.run('global.BH = []; var _j = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { array_push(global.BH, [kfo_bot_pre_name(kfo_host_botcfg(_j).pre), _b.hits, _b.sq]); _j++; } }')
res = J(sim, 'global.BH')
hits = {r[0]: r[1] for r in res}
print('used %d items, hidden copies per item %r, bot hits %r, real objects of the bots\' sends in my game %r (%.0fs)'
      % (used, copies, hits, sorted(real_at_me), time.time() - t0), flush=True)
ok(used >= len(ITEMS), 'every item was used at the bots (%d uses)' % used)
ok(all(copies.get(s, 0) > 0 for s in ITEMS), 'every item put up its hidden copy around the bots %r' % {s: copies.get(s, 0) for s in ITEMS})
ok(leaks == 0, 'the copies are never shown or live for my own SOUL (%d)' % leaks)
ok(hits.get('DUMMY', 0) > hits.get('PERFECT', 0), 'the bots dodge: DUMMY %d hits > PERFECT %d' % (hits.get('DUMMY', 0), hits.get('PERFECT', 0)))
ok(hits.get('PERFECT', 0) <= max(3, hits.get('DUMMY', 0) // 4), 'PERFECT takes few hits (%d, DUMMY %d)' % (hits.get('PERFECT', 0), hits.get('DUMMY', 0)))
ok(sum(r[2] for r in res) > 0, "the bots use skills themselves (%d sends)" % sum(r[2] for r in res))
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
