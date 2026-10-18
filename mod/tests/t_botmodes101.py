"""DRBR 1.0.1: the bots PLAY the bosses' SOUL modes, and watching a bot shows it - two emulated games over the simulated network
(br_multi: the real merged code, the real host with six bots DUMMY ... PERFECT, a second game that goes OUT and watches a bot).
One boss attack forced every cycle in both games:
  gerson  (Crossfire, his green SOUL)  every bot turns its own shield toward the spears (kbr_hj_bot_face), a block is decided by
                                       where it faces; the watcher's shield turns as the followed bot's does (kbr_hj_puppet)
  flowery (Jarona!, his orange board)  every bot moves up and down out of the way (its planning, the vertical moves only) and
                                       DASHES when it passes a hazard; the watcher's orange SOUL dashes with it (kbr_fl_puppet)
  pink    (3D Tunnel, her tunnel)      every bot goes in and out along her rings (kbr_pk_bot_roam); the watcher's purple SOUL is
                                       on the followed bot's ring (kbr_pk_puppet)
Checked per boss: no error in either game, the bots move / turn / dash (not sitting still), more skill fewer hits where the
mode decides hits by play (green), and the watcher's view follows the bot.
Usage: python3 t_botmodes101.py [gerson flowery pink]"""
import sys, os, time, json
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *
import bbox_model
import t_view47

FAILS = []
N = [0]
ROWS = {'gerson': 7, 'flowery': 8, 'pink': 10}
FORCE = {'gerson': 2, 'flowery': 1, 'pink': 7}
PRE = ['DUMMY', 'EASY', 'NORMAL', 'HARD', 'EXPERT', 'PERFECT']


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


BOTS = ('(function(){ var _o = []; var _H = global.kfo.H; var _j = 0; for (var _i = 0; _i < array_length(_H.pl); _i++) { var _b = _H.pl[_i];'
        ' if (!_b.bot) continue; var _s = _b.bt; array_push(_o, [_b.pid, kfo_bot_pre_name(kfo_host_botcfg(_j).pre), is_struct(_s) ? round(_s.x * 10) / 10 : 0,'
        ' is_struct(_s) ? round(_s.y * 10) / 10 : 0, variable_struct_exists(_b, "gd") ? _b.gd : -1, variable_struct_exists(_b, "fd") ? _b.fd : 0, _b.hits]); _j++; } return _o; })()')
WATCH = ('(function(){ var _M = global.kfo.M; var _w = kbr_spec_pid(_M); if (_w < 0 || !variable_struct_exists(_M.ps, string(_w))) return -1;'
         ' var _q = variable_struct_get(_M.ps, string(_w)); var _sh = kbr_hj_up_shield();'
         ' return [_w, variable_struct_exists(_q, "gd") ? _q.gd : -1, (_sh == noone) ? -2 : _sh.idealdir, variable_struct_exists(_q, "fd") ? _q.fd : 0,'
         ' instance_exists(obj_fl_soul) ? obj_fl_soul.dashing : -1, instance_exists(obj_pk_purple) ? obj_pk_purple.mode : -1,'
         ' instance_exists(obj_pk_purple) ? obj_pk_purple.tunnel_lane_layer : -1, kbr_ps_x(_q) + 10, kbr_ps_y(_q) + 10,'
         ' instance_exists(obj_pk_purple) ? (obj_pk_purple.x + 1) : 0, instance_exists(obj_pk_purple) ? (obj_pk_purple.y + 1) : 0]; })()')


def wrap_tick(sim):
    src = t_view47.func_src('kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
    sim.load_source('gml_GlobalScript_botmodes_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')


def run_boss(boss, frames=900):
    print('== %s' % boss, flush=True)
    row = ROWS[boss]
    net, sims = make_room(2, 'lan', 6100 + row, open_ok=row, kn=(row,), bots=6, setx='_s.mhp = 999; _s.skills = 0; _s.ramp = 3; _s.hard = 1;')
    H, C2 = sims
    bbox_model.install(H)
    wrap_tick(H)
    H.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; global.kfo.H.botcfg[_i] = _c; }')
    for s in sims:
        # (the harness's stand-in battle controller lacks Chapter 3's TP total, which a blocked spear's TP adds to)
        s.run('with (obj_battlecontroller) { if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0; }')
        s.run('global.JV_FORCE = %d;' % FORCE[boss])
        s.load_source('gml_GlobalScript_botmodes_force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
        s.run('global.kfo.M.tl.cyc = [];')
    H.run('global.kfo.H.tl.cyc = [];')
    rec = {'bots': [], 'watch': []}

    def keep(f, sims_, prev):
        bbox_model.move(H)
        H.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];'
              'for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) _b.hp = _b.mh; }')
        if f % 30 == 0:
            for s in sims_:
                s.log.clear()
        rec['bots'].append((J(H, 'global.kfo.M.R.ph'), J(H, BOTS), J(H, 'instance_exists(obj_pk_purple) ? obj_pk_purple.mode : -1')))
        rec['watch'].append(J(C2, WATCH))

    # the second game goes OUT and watches the PERFECT bot (the last one)
    r0 = run(net, sims, 60, 'none', on_frame=keep, wall=1200)
    C2.run('kbr_local_death();')
    r1 = run(net, sims, 40, 'none', on_frame=keep, wall=1200)
    bots = J(H, BOTS)
    follow = bots[-1][0]
    C2.run('global.kfo.M.spect = %d; global.kfo.M.vw.picked = true; global.kfo.M.vw.cam = 0;' % follow)
    rec['bots'] = []
    rec['watch'] = []
    r2 = run(net, sims, frames, 'none', on_frame=keep, wall=2400)
    errs = {c: r[c]['errors'][:1] for r in (r0, r1, r2) for c in (1, 2) if r[c]['errors']}
    ok(not errs, '%s: no error in the host (6 bots) nor the watcher (%s)' % (boss, json.dumps(errs)[:300]))
    if errs:
        return
    run_frames = [b for ph, b, m in rec['bots'] if ph == 'run']
    tunnel_frames = [b for ph, b, m in rec['bots'] if ph == 'run' and m == 7]
    ok(len(run_frames) > 200, '%s: the attack ran (%d frames)' % (boss, len(run_frames)))
    names = [b[1] for b in bots]
    hits = {b[1]: b[6] for b in rec['bots'][-1][1]}
    print('  hits', hits, flush=True)
    W = [w for w in rec['watch'] if isinstance(w, list) and w[0] == follow]
    ok(len(W) > 200, '%s: the watcher follows the PERFECT bot (%d frames)' % (boss, len(W)))
    if boss == 'gerson':
        turns = {}
        for n in names:
            seq = [[b[4] for b in fr if b[1] == n][0] for fr in run_frames]
            seq = [v for v in seq if v >= 0]
            turns[n] = (len(set(seq)), sum(1 for a, b in zip(seq, seq[1:]) if a != b))
        print('  shield directions used / turns per bot', turns, flush=True)
        ok(all(t[0] >= 2 and t[1] >= 2 for t in turns.values()), 'gerson: every bot turns its shield (directions used, turns: %r)' % turns)
        ok(hits['DUMMY'] >= hits['NORMAL'] >= hits['PERFECT'] and hits['PERFECT'] <= 1, 'gerson: blocks follow skill - DUMMY %d >= NORMAL %d >= PERFECT %d' % (hits['DUMMY'], hits['NORMAL'], hits['PERFECT']))
        sh = [w for w in W if w[1] >= 0 and w[2] >= 0]
        same = sum(1 for w in sh if w[1] == w[2])
        ok(len(sh) > 100 and same >= len(sh) * 0.95, "gerson: the watcher's shield points where the bot's does (%d of %d frames)" % (same, len(sh)))
        ok(len(set(w[2] for w in sh)) >= 2, "gerson: ... and turns with it (%d directions)" % len(set(w[2] for w in sh)))
    if boss == 'flowery':
        ys = {n: [[b[3] for b in fr if b[1] == n][0] for fr in run_frames] for n in names}
        rng = {n: round(max(v) - min(v), 1) for n, v in ys.items() if v}
        moves = {n: sum(1 for a, b in zip(v, v[1:]) if abs(a - b) > 0.5) for n, v in ys.items()}
        dash = {n: sum(1 for fr in run_frames for b in fr if b[1] == n and b[5]) for n in names}
        print('  height range / moving frames / dash frames per bot', rng, moves, dash, flush=True)
        ok(all(moves[n] >= 20 for n in names if n != 'DUMMY'), 'flowery: the bots move up and down on the board (frames moving: %r)' % moves)
        ok(all(dash[n] > 0 for n in ('NORMAL', 'HARD', 'EXPERT', 'PERFECT')), 'flowery: the bots dash (dash frames: %r)' % dash)
        wd = [w for w in W if w[3] == 1]
        both = sum(1 for w in wd if w[4] == 1)
        ok(len(wd) > 0 and both >= len(wd) * 0.9, "flowery: the watcher's orange SOUL dashes when the bot does (%d of %d frames)" % (both, len(wd)))
    if boss == 'pink':
        tun = tunnel_frames
        ok(len(tun) > 100, 'pink: her tunnel was on (%d frames)' % len(tun))
        rad = {}
        for n in names:
            seq = []
            for fr in tun:
                b = [x for x in fr if x[1] == n][0]
                seq.append((round(b[2]), round(b[3])))
            rad[n] = len(set(seq))
        print('  distinct places per bot in the tunnel', rad, flush=True)
        ok(all(v >= 3 for v in rad.values()), 'pink: in her tunnel every bot moves from ring to ring (places: %r)' % rad)
        tl = [w for w in W if w[5] == 7]
        layers = set(w[6] for w in tl)
        ok(len(tl) > 100 and len(layers) >= 2, "pink: the watcher's purple SOUL goes to the followed bot's ring (%d tunnel frames, rings %r)" % (len(tl), sorted(layers)))


t0 = time.time()
want = sys.argv[1:] or ['gerson', 'flowery', 'pink']
for b in want:
    run_boss(b)
print('botmodes101: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
