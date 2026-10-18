"""DRBR 1.0.2: 1.0.1 and 1.0.2 in ONE room (a player who has not updated yet). Both are multiplayer build 51 (kfo_version), so
they share rooms - this checks they also PLAY together: emulated games over the simulated network (br_multi), each game running
ITS OWN version's real merged code - 1.0.2 = the build's merged code, 1.0.1 = 1.0.1's own build inputs (the toolkit of its 51.11
game package) through 1.0.1's own generator (KH_OLD, made by make_old_code.sh with OLD_TK).
  match   three players, no bots - a 1.0.2 host, a 1.0.1 game, a 1.0.2 game - the knights, then Gerson, Flowery and Pink
          (one boss a match): every game the same knight / attack, seed and start tick every cycle, the same arena; the
          bullets compared where all three play the same keys; no error in any game
  watch   six bots, a boss's SOUL mode forced, the second game OUT watching the PERFECT bot, both ways round: a 1.0.2 host
          watched by a 1.0.1 game, and a 1.0.1 host watched by a 1.0.2 game: no error in either, the watcher follows the bot and
          sees it move (on Flowery's board: dashes when it does)
Usage: python3 t_mixver102.py [match] [watch]"""
import sys, os, re, time, json
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
from br_multi import *
import br_multi
import bbox_model

NEW = harness.M
OLD = os.environ.get('KH_OLD', '/tmp/claude-0/-home-claude/86dc8034-1d0e-5f2c-a65f-e537350090b1/scratchpad/old1011/merged/')
assert os.path.exists(OLD + 'gml_GlobalScript_knight_core.gml'), 'no 1.0.1 code at ' + OLD
FAILS = []
N = [0]
ROWS = {'gerson': 7, 'flowery': 8, 'pink': 10}
FORCE = {'gerson': 2, 'flowery': 1, 'pink': 7}


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


# ---- which version a game runs: every harness module's code folder (they each hold their own M / MDIR) ----
CUR = [NEW]


def use(d):
    for mod in list(sys.modules.values()):
        for k in ('M', 'MDIR'):
            try:
                if getattr(mod, k, None) == CUR[0]:
                    setattr(mod, k, d)
            except Exception:
                pass
    CUR[0] = d


VERS = []        # the versions of the games of the room being made, in order (host first)
SIMV = {}        # id(sim) -> its code folder
_lu = br_multi.lu_battle
_pb = br_multi.preload_base
_pm = br_multi.premock


def lu_v(*a, **k):
    i = len([1 for _ in SIMV_PENDING])
    d = VERS[i]
    use(d)
    sim, e = _lu(*a, **k)
    SIMV_PENDING.append(sim)
    SIMV[id(sim)] = d
    use(NEW)
    return sim, e


def pb_v(sim):
    use(SIMV.get(id(sim), NEW))
    try:
        return _pb(sim)
    finally:
        use(NEW)


def pm_v(sim):
    use(SIMV.get(id(sim), NEW))
    try:
        return _pm(sim)
    finally:
        use(NEW)


br_multi.lu_battle = lu_v
br_multi.preload_base = pb_v
br_multi.premock = pm_v
SIMV_PENDING = []


def room(vers, *a, **k):
    VERS[:] = vers
    SIMV_PENDING.clear()
    net, sims = make_room(*a, **k)
    got = [J(s, 'kfo_version()') for s in sims]
    newcode = [J(s, 'script_exists(asset_get_index("kbr_hj_bot_face")) || variable_global_exists("__never")') for s in sims]
    return net, sims, got


def is_new(sim):
    return SIMV.get(id(sim)) == NEW


def func_src(path, name):
    core = open(path + 'gml_GlobalScript_knight_core.gml', encoding='utf8').read()
    m = re.search(r'(?m)^function %s\(' % re.escape(name), core)
    assert m, name
    i = core.index('{', m.end())
    d = 0
    j = i
    while True:
        c = core[j]
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                return core[m.start():j + 1]
        j += 1


def has_fn(sim, name):
    return sim.script_entries.get(name) is not None


# ---------------------------------------------------------------------------------------------------------------- match
def keep_alive(f, sims, prev):
    if f % 30 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            s.log.clear()


def match(label, kn, frames, setx='_s.mhp = 999;'):
    print('== match %s: 1.0.2 host, 1.0.1, 1.0.2' % label, flush=True)
    t0 = time.time()
    open_ok = kn[0] if len(kn) == 1 else 0
    net, sims, got = room([NEW, OLD, NEW], 3, 'lan', 4242 + kn[0], setx=setx, open_ok=open_ok, kn=kn)
    for s in sims:
        # (the harness's stand-in battle controller lacks Chapter 3's TP total - the real one's Create sets mercytotal = 0;
        # Gerson's blocked spears add to it through scr_tensionheal)
        s.run('with (obj_battlecontroller) { if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0; }')
    vers = ['1.0.2' if has_fn(s, 'kbr_fl_broken') else '1.0.1' for s in sims]
    ok(vers == ['1.0.2', '1.0.1', '1.0.2'] and got == [51, 51, 51], '%s: the room is 1.0.2 / 1.0.1 / 1.0.2, all multiplayer build 51 (%r %r)' % (label, vers, got))
    rec = run(net, sims, frames, 'same', on_frame=keep_alive, wall=2400)
    errs = {c: rec[c]['errors'][:1] for c in (1, 2, 3) if rec[c]['errors']}
    ok(not errs, '%s: no error in any game (%s)' % (label, json.dumps(errs)[:400]))
    cmp = compare(rec, 3)
    print('  cycles in all three %d, logic differences %r, arena differences %d, bullets same/different %d/%d, start spread p95/max %s/%s ms (%.0fs)'
          % (cmp['cycles_all'], cmp['logic_bad'][:3], len(cmp['arena_bad']), cmp['bul_same'], cmp['bul_diff'], cmp['onset_p95'], cmp['onset_max'], time.time() - t0), flush=True)
    ok(cmp['cycles_all'] >= 2, '%s: attacks were played in all three games (%d cycles)' % (label, cmp['cycles_all']))
    ok(not cmp['logic_bad'] and cmp['dupes'] == 0, '%s: every cycle the same knight / attack, seed and start tick in 1.0.1 and 1.0.2 (%r)' % (label, cmp['logic_bad'][:3]))
    ok(not cmp['arena_bad'], '%s: the same arena in every game (%r)' % (label, cmp['arena_bad'][:2]))
    ok(cmp['bul_diff'] == 0 and cmp['bul_same'] > 0, '%s: the same bullets in 1.0.1 and 1.0.2 (same %d, different %d: %r)' % (label, cmp['bul_same'], cmp['bul_diff'], [d[:2] for d in cmp['bul_diff_list'][:3]]))


# ---------------------------------------------------------------------------------------------------------------- watch
BOTS = ('(function(){ var _o = []; var _H = global.kfo.H; for (var _i = 0; _i < array_length(_H.pl); _i++) { var _b = _H.pl[_i];'
        ' if (!_b.bot) continue; var _s = _b.bt; array_push(_o, [_b.pid, is_struct(_s) ? round(_s.x * 10) / 10 : 0, is_struct(_s) ? round(_s.y * 10) / 10 : 0,'
        ' variable_struct_exists(_b, "fd") ? _b.fd : 0, _b.hits]); } return _o; })()')
WATCH = ('(function(){ var _M = global.kfo.M; var _w = kbr_spec_pid(_M); if (_w < 0 || !variable_struct_exists(_M.ps, string(_w))) return -1;'
         ' var _q = variable_struct_get(_M.ps, string(_w));'
         ' return [_w, round(kbr_ps_x(_q) * 10) / 10, round(kbr_ps_y(_q) * 10) / 10, variable_struct_exists(_q, "fd") ? _q.fd : 0,'
         ' instance_exists(obj_fl_soul) ? obj_fl_soul.dashing : -1, variable_struct_exists(_q, "gd") ? _q.gd : -9]; })()')


def watch(boss, host, watcher, frames=600):
    hv = '1.0.2' if host == NEW else '1.0.1'
    wv = '1.0.2' if watcher == NEW else '1.0.1'
    label = '%s, %s host, %s watcher' % (boss, hv, wv)
    print('== watch %s' % label, flush=True)
    row = ROWS[boss]
    net, sims, got = room([host, watcher], 2, 'lan', 6100 + row, open_ok=row, kn=(row,), bots=6, setx='_s.mhp = 999; _s.skills = 0; _s.ramp = 3; _s.hard = 1;')
    H, C2 = sims
    bbox_model.install(H)
    # the host's bot tick, synced with the box model (the host's own version of it)
    src = func_src(host, 'kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
    H.load_source('gml_GlobalScript_mixver_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')
    H.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; global.kfo.H.botcfg[_i] = _c; }')
    for s in sims:
        s.run('with (obj_battlecontroller) { if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0; }')
        s.run('global.JV_FORCE = %d;' % FORCE[boss])
        s.load_source('gml_GlobalScript_mixver_force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n')
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
        rec['bots'].append((J(H, 'global.kfo.M.R.ph'), J(H, BOTS)))
        rec['watch'].append(J(C2, WATCH))

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
    ok(not errs, '%s: no error in the host (6 bots) nor the watcher (%s)' % (label, json.dumps(errs)[:300]))
    if errs:
        return
    run_n = sum(1 for ph, b in rec['bots'] if ph == 'run')
    ok(run_n > 200, '%s: the attack ran (%d frames)' % (label, run_n))
    W = [w for w in rec['watch'] if isinstance(w, list) and w[0] == follow]
    ok(len(W) > 200, '%s: the watcher follows the PERFECT bot (%d frames)' % (label, len(W)))
    places = set((w[1], w[2]) for w in W)
    hostpl = set((fr[-1][1], fr[-1][2]) for ph, fr in rec['bots'] if ph == 'run' and fr)
    print('  places of the bot: at the host %d, at the watcher %d; the watcher\'s shield direction values %r' % (len(hostpl), len(places), sorted(set(w[5] for w in W))[:6]), flush=True)
    if len(hostpl) >= 3:
        ok(len(places) >= 3, '%s: the watcher sees the bot move (%d places)' % (label, len(places)))
    if boss == 'flowery':
        wd = [w for w in W if w[3] == 1]
        both = sum(1 for w in wd if w[4] == 1)
        ok(len(wd) > 0 and both >= len(wd) * 0.9, "%s: the watcher's orange SOUL dashes when the bot does (%d of %d frames)" % (label, both, len(wd)))
    if boss == 'gerson':
        ok(any(w[5] not in (-1, -9) for w in W), "%s: the watcher gets the bot's shield direction (%r)" % (label, sorted(set(w[5] for w in W))[:4]))


t0 = time.time()
want = sys.argv[1:] or ['match', 'watch']
# (boss names after the parts: only those - e.g. "match gerson")
only = [a for a in want if a in ('knights', 'gerson', 'flowery', 'pink')]
if 'match' in want:
    if not only or 'knights' in only:
        match('knights', (0, 1, 2, 3, 4, 5), 1500)
    for b in ('gerson', 'flowery', 'pink'):
        if not only or b in only:
            match(b, (ROWS[b],), 1200)
if 'watch' in want:
    for b in ('gerson', 'flowery', 'pink'):
        if not only or b in only:
            watch(b, NEW, OLD)
            watch(b, OLD, NEW)
print('mixver102: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
