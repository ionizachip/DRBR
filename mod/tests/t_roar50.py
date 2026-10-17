"""Build 50: the knights' Roaring (their finale) online, with bots. A practice match (the host's own game) with six bots (DUMMY ...
PERFECT), the emulator's motion and collision stand-in (bbox_model); cycle 1 is the knight's Roaring (FINAL TWO at cycle 1).

  - the online HUD steps aside while a Roaring is on screen (skill slots, log, the players, the knight card, the TARGETING row,
    the banner, the hub's lines) and is back after it;
  - the bots get through a Roaring as a player's SOUL does: the box they keep to is the screen (the Roaring's own clamp; its box
    swells past the screen, then shrinks to nothing), the stars hit them only on the stars' precise test, the Roaring pulls them;
    the bots that all died in it before (OLD=the build 50 first delivery's rules, kept for comparison) live now;
  - no errors.
Usage: python3 t_roar50.py [knight ...]   (ROAR_OLD=1 also runs the old rules for comparison)"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *
import br_harness
from br_harness import br_match, br_state
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
HUD = ['kbr_hud_skills', 'kbr_hud_players', 'kbr_hud_tg', 'kbr_hud_log', 'kbr_hud_banner', 'kbr_hud_knight', 'knight_txt_small']


def run(k, old):
    sim, e = br_match(open_ok=k, kn=(k,), seed=950 + k, bots=6)
    if e is not None:
        return {'err': 'setup: %s' % e}
    bbox_model.install(sim)
    src = t_view47.func_src('kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
    sim.load_source('gml_GlobalScript_roar50_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')
    wr = 'global.HC = {};\n'
    for f in HUD:
        s2 = t_view47.func_src(f).replace('function %s(' % f, 'function %s__orig(' % f, 1)
        wr += s2 + '\nfunction %s(_a, _b, _c) { global.HC.%s = (variable_struct_exists(global.HC, "%s") ? global.HC.%s : 0) + 1; return %s__orig(_a, _b, _c); }\n' % (f, f, f, f, f)
    sim.load_source('gml_GlobalScript_roar50_hud', wr)
    sim.run('global.HC = {};')
    s3 = t_view47.func_src('kfo_bot_hit_by').replace('function kfo_bot_hit_by(', 'function kfo_bot_hit_by__orig(', 1)
    sim.load_source('gml_GlobalScript_roar50_hb', s3 + '\nfunction kfo_bot_hit_by(_x, _y, _s) { var _r = kfo_bot_hit_by__orig(_x, _y, _s); if (_r != noone && instance_exists(_r) && kbr_hud_roaring()) { var _k = object_get_name(_r.object_index) + (variable_instance_exists(_r, "roaring2_fullscreen") ? (_r.roaring2_fullscreen ? "/full" : "/part") : ""); global.HB[$ _k] = (variable_struct_exists(global.HB, _k) ? global.HB[$ _k] : 0) + 1; } return _r; }\n')
    sim.run('global.HB = {};')
    sim.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; _c.pre = _i; global.kfo.H.botcfg[_i] = _c; }')
    if old:
        sim.mock('kfo_bot_roaring', lambda s: -4)
        sim.mock('kfo_bot_precise', lambda s, b: -1)
    sim.run('kbr_tl_set_ft(global.kfo.M.tl, 1); kbr_tl_set_ft(global.kfo.H.tl, 1);')
    r = {'err': None, 'roar': False, 'hud_before': None, 'hud_in': None, 'hud_after': None, 'hits': {}, 'dead': {}, 'box': None, 'f': 0}
    start_f = end_f = None
    hp0 = None
    f = 0
    while f < 2600:
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = br_harness.step(sim, 1)
        bbox_model.move(sim)
        f += 1
        if err:
            r['err'] = 'frame %d: %s' % (f, err[:400])
            return r
        roar = sim.eval('kbr_hud_roaring()')
        s = br_state(sim) if f % 3 == 0 else None
        if s and start_f is None and s['k'] == 1 and s['ph'] == 'run':
            start_f = f
        if not roar and start_f is None and f % 3 == 0:
            # the bots at full HP until the Roaring starts
            sim.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { _b.hp = _b.mh; _b.hits = 0; } }')
        if roar and not r['roar']:
            r['roar'] = True
            sim.run('global.HC = {}; knight_hud_draw();')
            r['hud_in'] = J(sim, 'global.HC')
            hp0 = J(sim, '(function(){ var _r = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) array_push(_r, [_b.hp, _b.hits]); } return _r; })()')
        if roar and r['box'] is None and f % 30 == 0:
            r['box'] = J(sim, 'kfo_bot_box()')
        if not roar and r['hud_before'] is None and start_f is None and s and s['ph'] == 'run':
            sim.run('global.HC = {}; knight_hud_draw();')
            r['hud_before'] = J(sim, 'global.HC')
        if roar and f % 60 == 0:
            sim.run('global.HC = {}; knight_hud_draw();')
            hc = J(sim, 'global.HC')
            if any(hc.get(x, 0) for x in HUD):
                r['hud_in'] = hc
        if r['roar'] and not roar:
            post = r.get('post', 0) + 1
            r['post'] = post
            if post >= 20:
                end_f = f
                break
        if s and start_f is not None and s['k'] >= 2:
            end_f = f
            break
    r['f'] = (start_f, end_f)
    sim.run('global.HC = {}; knight_hud_draw();')
    r['hud_after'] = J(sim, 'global.HC')
    res = J(sim, '(function(){ var _r = []; var _j = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { array_push(_r, [kfo_bot_pre_name(kfo_host_botcfg(_j).pre), _b.hits, _b.hp, _b.al, _b.mh]); _j++; } } return _r; })()')
    r['bots'] = res
    r['hitby'] = J(sim, 'global.HB')
    r['hp0'] = hp0
    return r


ks = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3, 4]
for k in ks:
    for old in ((False, True) if os.environ.get('ROAR_OLD') == '1' else (False,)):
        t0 = time.time()
        r = run(k, old)
        tag = 'knight %d%s' % (k, ' OLD' if old else '')
        print(tag, 'frames', r.get('f'), 'box', r.get('box'), 'bots', r.get('bots'), 'hud', r.get('hud_before'), r.get('hud_in'), r.get('hud_after'), 'hit by', r.get('hitby'), round(time.time() - t0), 's', flush=True)
        if old:
            continue
        ok(r['err'] is None, tag + ': no error (%s)' % r['err'])
        if r['err']:
            continue
        ok(r['roar'], tag + ': the Roaring was on screen')
        hb, hi, ha = r['hud_before'] or {}, r['hud_in'] or {}, r['hud_after'] or {}
        ok(hb.get('kbr_hud_skills', 0) > 0 and hb.get('kbr_hud_players', 0) > 0, tag + ': the HUD is drawn before the Roaring %r' % hb)
        ok(not any(hi.get(x, 0) for x in HUD), tag + ': no HUD over the Roaring %r' % hi)
        ok(ha.get('kbr_hud_players', 0) > 0, tag + ': the HUD is back after it %r' % ha)
        bx = r['box'] or [0, 0, 0, 0]
        ok(bx[2] - bx[0] >= 600 and bx[3] - bx[1] >= 440, tag + ': the bots keep to the screen in the Roaring %r' % bx)
        alive = [b for b in r['bots'] if b[3]]
        ok(len(alive) >= 5, tag + ': the bots get through the Roaring (%d of 6 alive: %r)' % (len(alive), r['bots']))
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
