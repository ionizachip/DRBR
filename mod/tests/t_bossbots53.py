"""DRBR: the bots against every boss (the host's bots dodge the boss's own attacks: its pieces, with each boss's own rules -
Jevil's generic bullet tracking, Gerson's green SOUL (it faces and shields), Flowery's orange board (by the odds), Spamton NEO's
yellow SOUL and his mail walls (by the odds: kbr_sn_bot_walls), Pink's lanes (snapped to her lanes: kbr_pk_bot_snap; her
tunnel and maze by the odds: kbr_pk_bot_odds).
One practice match per boss with six bots, one per preset (DUMMY ... PERFECT), the boss alone, the emulator's stand-in for
GameMaker's motion and boxes (bbox_model.py). Checked: no error in the host's bot code over the run, every bot still in, and
more skill takes fewer hits (DUMMY >= NORMAL >= PERFECT, PERFECT few). SPAMTON's walls are forced once more on their own
(RECREW Columns as every cycle's attack): each wall a bot crosses is one roll of its odds - at most one hit for it - so DUMMY is
hit by most walls and PERFECT by (almost) none.
Usage: python3 t_bossbots53.py [boss ...]   (jevil gerson flowery spamton pink walls)"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
from br_harness import *
import bbox_model
import t_view47

FAILS = []
N = [0]
PRE = ['DUMMY', 'EASY', 'NORMAL', 'HARD', 'EXPERT', 'PERFECT']
ROWS = {'jevil': 6, 'gerson': 7, 'flowery': 8, 'spamton': 9, 'pink': 10}


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def wrap_tick(sim):
    src = t_view47.func_src('kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
    sim.load_source('gml_GlobalScript_bossbots_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')


def run(boss, frames, seed, force=None):
    ok_s = ROWS[boss]
    sim, e = br_match(open_ok=ok_s, kn=(ok_s,), seed=seed, bots=6, setx='_s.mhp = 999; _s.skills = 0; _s.ramp = 3; _s.hard = 1;')
    if not ok(e is None, '%s: practice with 6 bots (%s)' % (boss, e)):
        return None
    bbox_model.install(sim)
    wrap_tick(sim)
    sim.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; global.kfo.H.botcfg[_i] = _c; }')
    if os.environ.get('BOT_DIAG'):
        # which pieces hit the bots: kfo_bot_take's callers - the walls' odds (kbr_sn_bot_walls) or the bullet kfo_bot_hit_by found
        src = ''
        for fn in ('kfo_bot_hit_by', 'kfo_bot_take', 'kbr_sn_bot_walls'):
            src += t_view47.func_src(fn).replace('function %s(' % fn, 'function %s__orig(' % fn, 1) + '\n'
        sim.load_source('gml_GlobalScript_bossbots_diag', src + '''
function kfo_bot_hit_by(_x, _y, _self) { var _r = kfo_bot_hit_by__orig(_x, _y, _self); global.DG_LAST = (_r != noone) ? object_get_name(_r.object_index) : "none"; return _r; }
function kbr_sn_bot_walls(_b, _c, _e) { global.DG_WALL = true; var _r = kbr_sn_bot_walls__orig(_b, _c, _e); global.DG_WALL = false; return _r; }
function kfo_bot_take(_b, _d) { if (!variable_global_exists("DG")) global.DG = {}; var _M = global.kfo.M; var _c = kbr_tl_get(_M.tl, _M.R.k);
  var _k = (variable_global_exists("DG_WALL") && global.DG_WALL) ? "WALL" : (variable_global_exists("DG_LAST") ? global.DG_LAST : "?");
  _k = _k + " ai" + string(is_struct(_c) ? _c.ai : -1) + (is_struct(_c) && _c.roar ? " roar" : "") + " " + string(_b.pid);
  variable_struct_set(global.DG, _k, (variable_struct_exists(global.DG, _k) ? variable_struct_get(global.DG, _k) : 0) + 1);
  return kfo_bot_take__orig(_b, _d); }
''')
    if force is not None:
        sim.run('global.JV_FORCE = %d;' % force)
        sim.load_source('gml_GlobalScript_bbforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
        sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    run_f = 0
    t0 = time.time()
    err = None
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];'
                'for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) _b.hp = _b.mh; }')
        err = step(sim, 1)
        if err:
            break
        bbox_model.move(sim)
        if f % 30 == 0:
            sim.log.clear()
        if J(sim, 'global.kfo.M.R.ph') == 'run':
            run_f += 1
    if not ok(err is None, '%s: no error in %d frames (%s)' % (boss + ('' if force is None else ' (attack %d)' % force), frames, (err or '')[:300])):
        return None
    sim.run('global.BH = []; var _j = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { array_push(global.BH, [kfo_bot_pre_name(kfo_host_botcfg(_j).pre), _b.hits, _b.al]); _j++; } }')
    res = J(sim, 'global.BH')
    walls = None
    if boss == 'spamton':
        # (every wall each bot met in the run - its record of keys is cleared every 40, so count them as they come: snw_n)
        walls = J(sim, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) array_push(_o, variable_struct_exists(_b.bt, "snw_n") ? _b.bt.snw_n : 0); } return _o; })()')
    r = {'boss': boss, 'force': force, 'run_frames': run_f, 'hits': {x[0]: x[1] for x in res}, 'alive': all(x[2] for x in res), 'walls_seen': walls,
         'wall': round(time.time() - t0)}
    if os.environ.get('BOT_DIAG'):
        print('diag hits', json.dumps(J(sim, 'variable_global_exists("DG") ? global.DG : {}'), sort_keys=True), flush=True)
        print('diag cycles', J(sim, '(function(){ var _o = []; var _l = global.kfo.M.tl.cyc; for (var _i = 0; _i < array_length(_l); _i++) array_push(_o, [_l[_i].k, _l[_i].ai, _l[_i].roar, _l[_i].dur]); return _o; })()'), flush=True)
    print('bots', json.dumps(r), flush=True)
    return r


def judge(r, name):
    if r is None:
        return
    h = r['hits']
    ok(r['alive'], '%s: every bot still in (HP kept full)' % name)
    ok(h['DUMMY'] >= h['NORMAL'] >= h['PERFECT'], '%s: more skill, fewer hits: DUMMY %d >= NORMAL %d >= PERFECT %d %r' % (name, h['DUMMY'], h['NORMAL'], h['PERFECT'], h))
    ok(h['PERFECT'] <= max(3, h['DUMMY'] // 5), '%s: PERFECT takes few hits (%d, DUMMY %d)' % (name, h['PERFECT'], h['DUMMY']))


if __name__ == '__main__':
    t0 = time.time()
    want = sys.argv[1:] or ['jevil', 'gerson', 'flowery', 'spamton', 'pink', 'walls']
    fr = int(os.environ.get('BOT_FRAMES', '1500'))
    for b in want:
        if b == 'walls':
            # SPAMTON's RECREW Columns (attack 1) every cycle
            r = run('spamton', fr, 5391, force=1)
            if r is not None:
                judge(r, 'spamton walls')
                w = r['walls_seen']
                ok(w is not None and max(w) > 0, 'spamton walls: the bots crossed his walls (walls rolled per bot %r)' % (w,))
                ok(r['hits']['DUMMY'] <= max(w) + 2, 'spamton walls: at most one hit per wall crossed (DUMMY %d hits, %d walls)' % (r['hits']['DUMMY'], max(w)))
            continue
        judge(run(b, fr, 5390 + ROWS[b]), b)
    print('bossbots53: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
